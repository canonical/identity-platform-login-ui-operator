## Why

The Identity Platform is migrating its ingress infrastructure from Traefik to Istio (Gateway API). The current charm uses `TraefikRouteRequirer` with a raw JSON template (`public-route.json.j2`) to configure Traefik-specific routing. This tightly couples the charm to Traefik, making it incompatible with Istio-based deployments. Replacing the integration with `IstioIngressRouteRequirer` from [`charmlibs.interfaces.istio_ingress_route`](https://github.com/canonical/charmlibs/tree/main/interfaces/istio-ingress-route) enables native Gateway API routing through `istio-ingress-k8s` while preserving all exposed endpoints and the public URL update logic.

## What Changes

- **Replace** `TraefikRouteRequirer` (from `charms.traefik_k8s.v0.traefik_route`) with `IstioIngressRouteRequirer` (from `charmlibs.interfaces.istio_ingress_route`) — keeps the same relation name `public-route`
- **BREAKING**: Change `charmcraft.yaml` `public-route` interface from `traefik_route` → `istio_ingress_route`
- **Remove** `templates/public-route.json.j2` (Traefik-specific JSON template)
- **Update** `PublicRouteData` in `integrations.py` to derive URL from `IstioIngressRouteRequirer.external_host` and `tls_enabled`, and build an `IstioIngressRouteConfig` matching all current exposed routes
- **Update** `charm.py` to call `requirer.submit_config(config)` instead of `public_route.submit_to_traefik(config)` and to observe `ingress.on.ready` instead of raw relation events
- **Update** unit tests — replace `traefik_route` fixtures with `istio_ingress_route` fixtures, keep all existing behavioural assertions
- **Add** `lib/charmlibs/interfaces/istio_ingress_route/` charm library (fetched from charmlibs)
- **Add** `docs/migration-traefik-to-istio.md` with the operator migration procedure

## Capabilities

### New Capabilities

- `istio-public-route`: Expose the Login UI endpoints through `istio-ingress-k8s` via the `istio_ingress_route` interface; submit an `IstioIngressRouteConfig` that mirrors all Traefik route rules (path prefixes, exact paths, and the `/self-service` → `/api/kratos/self-service` URL rewrite); derive the public base URL from the istio provider's `external_host` + `tls_enabled` and propagate it to `ui-endpoint-info` databag — the same behaviour as with Traefik today.

### Modified Capabilities

*(none — no existing spec files exist in `openspec/specs/`)*

## Impact

- **`src/charm.py`**: swap `TraefikRouteRequirer` for `IstioIngressRouteRequirer`; update event observers and handler logic
- **`src/integrations.py`**: replace `PublicRouteData` implementation; remove Jinja2 template loading; remove `TraefikRouteRequirer` import
- **`src/constants.py`**: no change (relation name `PUBLIC_ROUTE_INTEGRATION_NAME = "public-route"` stays the same)
- **`charmcraft.yaml`**: change `public-route` interface from `traefik_route` to `istio_ingress_route`
- **`templates/public-route.json.j2`**: deleted
- **`lib/charmlibs/interfaces/istio_ingress_route/`**: new charm library added
- **`tests/unit/conftest.py`**: update `public_route_relation` fixture
- **`tests/unit/test_charm.py`**: update public-route tests
- **`docs/migration-traefik-to-istio.md`**: new operator migration guide
- **Dependencies**: remove `traefik_k8s` charm lib dependency; add `charmlibs-interfaces-istio-ingress-route` PyPI package
