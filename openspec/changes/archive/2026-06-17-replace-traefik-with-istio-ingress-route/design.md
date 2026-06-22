## Context

The Login UI operator currently uses `TraefikRouteRequirer` (from `charms.traefik_k8s.v0.traefik_route`) to configure Traefik as the ingress provider. Route rules are stored in a Jinja2 JSON template (`templates/public-route.json.j2`) and pushed to Traefik's app databag via `submit_to_traefik()`. The charm reads `external_host` and `scheme` from the relation databag to build its public base URL and publish it to the `ui-endpoint-info` relation.

The Identity Platform is moving to Istio Gateway API ingress (`istio-ingress-k8s` charm). The `charmlibs.interfaces.istio_ingress_route` library (PyPI: `charmlibs-interfaces-istio-ingress-route`) provides a typed `IstioIngressRouteRequirer` that speaks the `istio_ingress_route` interface, enabling native Gateway API routing. The charm must be updated to use this library while retaining all existing exposed paths and the public URL update flow.

## Goals / Non-Goals

**Goals:**
- Replace `TraefikRouteRequirer` with `IstioIngressRouteRequirer` under the same relation name `public-route`
- Replicate all 8 Traefik route rules as `HTTPRoute` objects in an `IstioIngressRouteConfig`
- Preserve the `/self-service` → `/api/kratos/self-service` path rewrite using `URLRewriteFilter`
- Derive the public base URL from `requirer.external_host` + `requirer.tls_enabled` (same semantics, different source)
- Update `ui-endpoint-info` databag whenever the istio URL changes (same trigger, different event)
- Provide a zero-downtime migration path document for operators

**Non-Goals:**
- Changing any of the exposed endpoint paths or the `ui-endpoint-info` schema
- Supporting both Traefik and Istio simultaneously in one charm revision
- Altering gRPC routing (the charm has no gRPC endpoints)

## Decisions

### 1. Library installation: Python package, not vendored charm lib

**Decision:** Add `charmlibs-interfaces-istio-ingress-route` to `charm-binary-python-packages` in `charmcraft.yaml` (alongside `jsonschema`).

**Rationale:** The library is distributed via PyPI as a standalone package (`charmlibs-interfaces-istio-ingress-route`). It is not a Charmhub charm lib (no `lib/charms/...` structure), so vendoring it would mean manually copying source and losing upstream updates. The `charm-binary-python-packages` mechanism builds it into the charm OCI image.

**Alternative considered:** Vendoring the source files into `lib/charmlibs/`. Rejected because it creates a maintenance burden and breaks the library's own version management.

### 2. Route configuration: 2 `HTTPRoute` objects — self-service isolated, rest consolidated

**Decision:** Use **2 `HTTPRoute` objects**: one for the path-rewrite route (`self-service`) and one consolidated route (`api-and-ui`) containing all 7 remaining paths as separate `matches` entries.

Route mapping:

| `HTTPRoute` name | Match type | Path | Filter |
|---|---|---|---|
| `self-service` | `PathPrefix` | `/self-service` | `URLRewriteFilter` → `/api/kratos/self-service` |
| `api-and-ui` | `Exact` | `/api/device` | — |
| `api-and-ui` | `Exact` | `/api/consent` | — |
| `api-and-ui` | `Exact` | `/api/v0/app-config` | — |
| `api-and-ui` | `Exact` | `/api/v0/tenants/resolve` | — |
| `api-and-ui` | `Exact` | `/api/v0/tenants` | — |
| `api-and-ui` | `Exact` | `/api/v0/auth/tenant` | — |
| `api-and-ui` | `PathPrefix` | `/ui` | — |

**Rationale:** The `self-service` route must be isolated because its `URLRewriteFilter` is route-level and would corrupt all other matches if merged. The remaining 7 paths share identical semantics (pass-through to backend at the same path, no transformation) and can safely share one `HTTPRoute` with multiple `matches`. The `charmlibs.interfaces.istio_ingress_route` library exposes only two filter types (`URLRewriteFilter` and `RequestRedirectFilter`); neither is a credible future need for any of these 7 pass-through paths. Real Istio concerns (auth, rate-limiting, CORS) are configured via separate Kubernetes resources (`AuthorizationPolicy`, `EnvoyFilter`) — not `HTTPRoute.filters` — so consolidation does not reduce future extensibility.

**Alternative considered:** One `HTTPRoute` per path (8 total). Rejected because the "complicates future per-route filter additions" rationale does not hold against the library's actual filter surface — the only actionable filters are URL rewrites and redirects, neither of which these pass-through routes need.

### 3. Event handling: `ingress.on.ready` replaces raw relation events

**Decision:** Observe `self.public_route.on.ready` instead of the raw `relation_joined` / `relation_changed` / `relation_broken` events.

**Rationale:** `IstioIngressRouteRequirer` already emits `ready` when:
- The relation-changed event fires and the relation exists (requirer side: to signal the charm should re-submit config).
- The relation-broken event fires (so the charm can clear the URL).

This avoids the current `self.public_route._relation = event.relation` workaround that was needed to synchronise the traefik lib's internal state.

**Alternative considered:** Keeping the raw relation events. Rejected as it bypasses the library's intended API.

### 4. URL derivation: `tls_enabled` property replaces `scheme` databag key

**Decision:** Build the public URL as:
```python
scheme = "https" if requirer.tls_enabled else "http"
url = URL(f"{scheme}://{requirer.external_host}")
```

**Rationale:** `IstioIngressRouteRequirer` exposes typed `external_host: str` and `tls_enabled: bool` properties that read from the provider's app databag. This replaces the manual databag key parsing in the old `PublicRouteData._external_host()` and `PublicRouteData._scheme()` class methods.

### 5. `PublicRouteData` refactor: drop Jinja2 template, keep frozen dataclass contract

**Decision:** Keep `PublicRouteData` as a `@dataclass(frozen=True)` in `integrations.py` but replace the `TraefikRouteRequirer` argument type with `IstioIngressRouteRequirer`. The `config` field changes type from `dict` (raw Traefik JSON) to `IstioIngressRouteConfig`. The `load()` classmethod builds the config programmatically.

**Rationale:** Removes the Jinja2 dependency from the integration layer, uses typed Pydantic models from the library, and preserves the dataclass boundary that `charm.py` already depends on.

### 6. Listener port: follows TLS status

**Decision:** Derive the Gateway listener port dynamically: `port = 443 if requirer.tls_enabled else 80`.

**Rationale:** The `istio-ingress-k8s` provider applies TLS upgrade globally — `Listener(port=80, HTTP)` with TLS enabled creates a Gateway HTTPS listener on port 80 (non-standard). Clients connecting to `https://host` default to port 443, so traffic would never reach a HTTPS/80 listener. Setting port 443 when TLS is enabled ensures correct routing. When TLS is disabled, port 80 is the standard HTTP port.

**HTTP→HTTPS redirect:** Full parity with Traefik (HTTP/80 redirect + HTTPS/443) is **not achievable** through `istio-ingress-route` alone because the TLS upgrade is all-or-nothing and there is no API to keep one listener as plain HTTP while another is HTTPS in a single config submission. The `_create_http_redirect_route()` function in the provider is hardwired to the IPA code path only.

### 7. Integration tests: deploy `istio-k8s` + `istio-ingress-k8s` on channel `2/stable`

**Decision:** The integration test deploys both `istio-k8s` (control plane) and `istio-ingress-k8s` (gateway) from channel `2/stable` with `trust=True`, integrates them together, then integrates the login-ui with `istio-ingress-k8s:istio-ingress-route`. The `public_address` fixture reads `external_host` from the `public-route` relation app databag rather than the unit IP of a Traefik app.

**Rationale:** Mirrors the documented manual deployment procedure. Reading `external_host` from the relation databag is the canonical source of truth — it is the same value the charm itself uses for `_domain_url`, so the test validates the end-to-end flow accurately.

## Risks / Trade-offs

- **[Breaking relation interface]** Changing `public-route` from `traefik_route` to `istio_ingress_route` makes the charm incompatible with Traefik. Existing deployments must remove the relation before upgrading. → **Mitigation:** Document the migration procedure in `docs/migration-traefik-to-istio.md`; include it in release notes.

- **[Path prefix rewrite semantics]** Traefik's `replacePathRegex` `^/self-service/(.*)` matches only paths with a trailing slash after the prefix. Istio's `ReplacePrefixMatch` on `/self-service` matches the prefix regardless of trailing slash. → **Mitigation:** This is functionally equivalent for all known Kratos self-service paths (e.g., `/self-service/login/api`). No functional regression expected. Document the subtle difference.

- **[New PyPI dependency]** `charmlibs-interfaces-istio-ingress-route` must be available at charm build time. → **Mitigation:** It is on PyPI; pin a minimum version (`>=0.1`) in charmcraft.yaml.

## Migration Plan

See `docs/migration-traefik-to-istio.md` (created as part of this change).

Summary:
1. **Before upgrade:** Run `juju remove-relation <login-ui-app> <traefik-app>` to detach the existing Traefik ingress.
2. **Upgrade the charm** to the new revision.
3. **After upgrade:** Run `juju relate <login-ui-app> <istio-ingress-app>` with relation name `public-route`.

Rollback: Re-deploy the previous charm revision, then re-add the Traefik relation.

## Open Questions

- *(none — requirements fully understood from codebase analysis)*
