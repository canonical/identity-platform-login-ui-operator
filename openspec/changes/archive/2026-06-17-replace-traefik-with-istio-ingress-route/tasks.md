## 1. Dependency Setup

- [x] 1.1 Add `charmlibs-interfaces-istio-ingress-route` to `charm-binary-python-packages` in `charmcraft.yaml`
- [x] 1.2 Update `charmcraft.yaml` `public-route` relation interface from `traefik_route` to `istio_ingress_route`
- [x] 1.3 Remove `lib/charms/traefik_k8s/` charm library directory (no longer needed)

## 2. Integration Layer (`src/integrations.py`)

- [x] 2.1 Remove `TraefikRouteRequirer` import and all Traefik-related imports (`jinja2.Template`, `json`)
- [x] 2.2 Add imports for `IstioIngressRouteRequirer`, `IstioIngressRouteConfig`, `Listener`, `HTTPRoute`, `BackendRef`, `HTTPRouteMatch`, `HTTPPathMatch`, `HTTPPathMatchType`, `ProtocolType`, `URLRewriteFilter`, `URLRewriteSpec`, `PathModifier`, `PathModifierType` from `charmlibs.interfaces.istio_ingress_route`
- [x] 2.3 Replace `PublicRouteData.load()` classmethod: accept `IstioIngressRouteRequirer` instead of `TraefikRouteRequirer`; derive `url` from `requirer.external_host` + `requirer.tls_enabled`; build `IstioIngressRouteConfig` programmatically (no Jinja2 template)
- [x] 2.4 Implement the 8 `HTTPRoute` objects in `PublicRouteData.load()` matching all paths from the old `public-route.json.j2` template: `self-service` (PathPrefix + URLRewrite), `api-device` (Exact), `api-consent` (Exact), `api-app-config` (Exact), `api-tenants-resolve` (Exact), `api-tenants` (Exact), `api-auth-tenant` (Exact), `ui` (PathPrefix)
- [x] 2.5 Change `PublicRouteData.config` field type from `dict` to `IstioIngressRouteConfig`
- [x] 2.6 Remove `PublicRouteData._external_host()` and `PublicRouteData._scheme()` class methods

## 3. Orchestration Layer (`src/charm.py`)

- [x] 3.1 Replace `TraefikRouteRequirer` import with `IstioIngressRouteRequirer` from `charmlibs.interfaces.istio_ingress_route`
- [x] 3.2 Replace `self.public_route = TraefikRouteRequirer(...)` with `self.public_route = IstioIngressRouteRequirer(self, relation_name=PUBLIC_ROUTE_INTEGRATION_NAME)`
- [x] 3.3 Update event observers: replace `relation_joined` / `relation_changed` / `relation_broken` raw events for `public-route` with `self.public_route.on.ready`
- [x] 3.4 Remove `_on_public_route_changed()` and `_on_public_route_broken()` methods; replace with a single `_on_public_route_ready()` handler that calls `_holistic_handler` and `_update_login_ui_endpoint_relation_data`
- [x] 3.5 In `_holistic_handler()`: replace `self.public_route.submit_to_traefik(config)` with `self.public_route.submit_config(config)`; update the readiness check from `self.public_route.is_ready()` to the new requirer API
- [x] 3.6 Remove the `self.public_route._relation = event.relation` workaround lines (no longer needed with the new lib)
- [x] 3.7 Update `_domain_url` property to use `PublicRouteData.load(self.public_route)` with the new `IstioIngressRouteRequirer` argument

## 4. Remove Traefik Template

- [x] 4.1 Delete `templates/public-route.json.j2`
- [x] 4.2 Verify no other file references `public-route.json.j2` or Jinja2 template loading for this route

## 5. Unit Tests

- [x] 5.1 Update `public_route_relation` fixture in `tests/unit/conftest.py`: change interface from `traefik_route` to `istio_ingress_route` and remote app name from `traefik-k8s` to `istio-ingress-k8s`; add `remote_app_data` with `external_host` and `tls_enabled` entries
- [x] 5.2 Rename `TestPublicRouteRelationEvents.test_traefik_route_integration` → `test_istio_route_integration` and update its docstring
- [x] 5.3 Add test for `_domain_url` returns HTTPS URL when `tls_enabled=True` in provider databag
- [x] 5.4 Add test for `_domain_url` returns HTTP URL when `tls_enabled=False` in provider databag
- [x] 5.5 Add test for `_domain_url` returns `None` when `external_host` is empty (relation without provider data)
- [x] 5.6 Add test verifying `submit_config()` is called with an `IstioIngressRouteConfig` containing all 8 routes on `relation_changed`
- [x] 5.7 Run `tox -e unit` and confirm all tests pass

## 6. Migration Document

- [x] 6.1 Create `docs/` directory if it does not exist
- [x] 6.2 Create `docs/migration-traefik-to-istio.md` with: overview of the breaking change, step-by-step Juju commands (remove Traefik relation → upgrade charm → add Istio relation), rollback instructions, and a note on the `/self-service` path rewrite semantic difference

## 7. Validation

- [x] 7.1 Run `tox -e lint` and fix any issues introduced by the change
- [x] 7.2 Run `tox -e unit` with full coverage and confirm no regressions
- [x] 7.3 Confirm `templates/public-route.json.j2` is deleted and no dead imports remain in `integrations.py` and `charm.py`

## 8. Listener Port Fix

- [x] 8.1 Add `INGRESS_HTTPS_PORT = 443` to `src/constants.py`
- [x] 8.2 In `PublicRouteData.load()`, derive listener port as `443 if requirer.tls_enabled else 80` so that TLS-enabled deployments create a Gateway listener on the standard HTTPS port rather than port 80
- [x] 8.3 Add unit test `test_submit_config_uses_port_443_when_tls_enabled`: assert all routes use `listener.port == 443` when `tls_enabled=True`
- [x] 8.4 Add unit test `test_submit_config_uses_port_80_when_tls_disabled`: assert all routes use `listener.port == 80` when `tls_enabled=False`
- [x] 8.5 Run `tox -e lint` and `tox -e unit` — confirm 27 tests pass

## 9. Integration Tests

- [x] 9.1 Update `tests/integration/constants.py`: remove `TRAEFIK_CHARM`, `TRAEFIK_PUBLIC_APP`, `PUBLIC_INGRESS_DOMAIN`; add `ISTIO_CHARM = "istio-k8s"`, `ISTIO_INGRESS_CHARM = "istio-ingress-k8s"`, `ISTIO_CHANNEL = "2/stable"`
- [x] 9.2 Update `tests/integration/conftest.py`: replace `TRAEFIK_PUBLIC_APP` import with `ISTIO_CHARM`/`ISTIO_INGRESS_CHARM`; rewrite `integrate_dependencies()` to first integrate `ISTIO_INGRESS_CHARM` with `ISTIO_CHARM`, then integrate the login-ui `public-route` endpoint with `istio-ingress-k8s:istio-ingress-route`; rewrite `public_address` fixture to read `external_host` from the `public-route` relation app databag
- [x] 9.3 Update `tests/integration/test_charm.py`: replace Traefik deploy with sequential deploys of `istio-k8s` and `istio-ingress-k8s` on channel `2/stable` with `trust=True`; update wait predicates to include `ISTIO_CHARM` and `ISTIO_INGRESS_CHARM`; update `test_has_ingress` comment; update `test_remove_integration` parametrize to use `ISTIO_INGRESS_CHARM`
- [x] 9.4 Run `tox -e lint` — confirm clean

## 10. Route Consolidation

- [x] 10.1 In `PublicRouteData.load()`, replace the 7 individual no-filter `HTTPRoute` objects (`api-device`, `api-consent`, `api-app-config`, `api-tenants-resolve`, `api-tenants`, `api-auth-tenant`, `ui`) with a single `HTTPRoute` named `"api-and-ui"` carrying all 7 paths as `matches`; keep `self-service` isolated (it has a `URLRewriteFilter`)
- [x] 10.2 Update `test_submit_config_called_with_all_routes`: assert route names are `{"self-service", "api-and-ui"}`; assert `api-and-ui` has all 7 matched paths
- [x] 10.3 Run `tox -e lint` and `tox -e unit` — confirm all tests pass
