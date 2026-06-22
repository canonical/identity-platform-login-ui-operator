## ADDED Requirements

### Requirement: Charm registers istio-ingress-route relation
The charm SHALL declare a `public-route` relation with interface `istio_ingress_route` in `charmcraft.yaml` (replacing the former `traefik_route` interface). The relation SHALL remain optional and limited to one provider.

#### Scenario: Relation declared with correct interface
- **WHEN** the charm metadata is inspected
- **THEN** `public-route` relation SHALL have interface `istio_ingress_route`

---

### Requirement: Charm submits IstioIngressRouteConfig on relation joined/changed
When the `public-route` relation is established and the charm is the leader, the charm SHALL submit an `IstioIngressRouteConfig` via `IstioIngressRouteRequirer.submit_config()` containing one `Listener` on `APPLICATION_PORT` with `ProtocolType.HTTP` and all required HTTP routes (see Route Requirements below).

#### Scenario: Config submitted on requirer ready
- **WHEN** the `public-route` relation is joined or changed and the charm is the leader
- **THEN** `IstioIngressRouteRequirer.submit_config()` SHALL be called with a valid `IstioIngressRouteConfig`

#### Scenario: Non-leader does not submit config
- **WHEN** the `public-route` relation changes and the charm unit is NOT the leader
- **THEN** `IstioIngressRouteRequirer.submit_config()` SHALL NOT be called

---

### Requirement: Route – self-service path with URL rewrite
The charm SHALL expose a route matching path prefix `/self-service` with a `URLRewriteFilter` that replaces the `/self-service` prefix with `/api/kratos/self-service` before forwarding to the backend.

#### Scenario: Self-service route with rewrite present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.PathPrefix` value `/self-service` and a `URLRewriteFilter` using `PathModifierType.ReplacePrefixMatch` value `/api/kratos/self-service`

---

### Requirement: Route – /api/device exact path
The charm SHALL expose an exact-match route for path `/api/device` with no filters.

#### Scenario: /api/device route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/device`

---

### Requirement: Route – /api/consent exact path
The charm SHALL expose an exact-match route for path `/api/consent` with no filters.

#### Scenario: /api/consent route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/consent`

---

### Requirement: Route – /api/v0/app-config exact path
The charm SHALL expose an exact-match route for path `/api/v0/app-config` with no filters.

#### Scenario: /api/v0/app-config route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/v0/app-config`

---

### Requirement: Route – /api/v0/tenants/resolve exact path
The charm SHALL expose an exact-match route for path `/api/v0/tenants/resolve` with no filters.

#### Scenario: /api/v0/tenants/resolve route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/v0/tenants/resolve`

---

### Requirement: Route – /api/v0/tenants exact path
The charm SHALL expose an exact-match route for path `/api/v0/tenants` with no filters.

#### Scenario: /api/v0/tenants route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/v0/tenants`

---

### Requirement: Route – /api/v0/auth/tenant exact path
The charm SHALL expose an exact-match route for path `/api/v0/auth/tenant` with no filters.

#### Scenario: /api/v0/auth/tenant route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.Exact` value `/api/v0/auth/tenant`

---

### Requirement: Route – /ui path prefix
The charm SHALL expose a route matching path prefix `/ui` with no filters.

#### Scenario: /ui route present in config
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** it SHALL contain an `HTTPRoute` with `HTTPPathMatchType.PathPrefix` value `/ui`

---

### Requirement: All routes target the charm's backend service
Every `HTTPRoute` in the config SHALL have a `BackendRef` pointing to the charm's app name on `APPLICATION_PORT`.

#### Scenario: Backend ref matches app name and port
- **WHEN** `IstioIngressRouteConfig` is built
- **THEN** every `HTTPRoute.backends` SHALL contain exactly one `BackendRef` with `service=<app_name>` and `port=APPLICATION_PORT`

---

### Requirement: Public URL derived from istio provider data
When `IstioIngressRouteRequirer.external_host` is non-empty, the charm SHALL derive the public base URL as `https://<external_host>` if `tls_enabled` is `True`, or `http://<external_host>` otherwise.

#### Scenario: HTTPS URL when TLS enabled
- **WHEN** `external_host` is `"example.com"` and `tls_enabled` is `True`
- **THEN** `_domain_url` SHALL return `"https://example.com"`

#### Scenario: HTTP URL when TLS disabled
- **WHEN** `external_host` is `"example.com"` and `tls_enabled` is `False`
- **THEN** `_domain_url` SHALL return `"http://example.com"`

#### Scenario: No URL when external_host is empty
- **WHEN** `external_host` is `""` (relation not yet ready)
- **THEN** `_domain_url` SHALL return `None`

---

### Requirement: ui-endpoint-info databag updated on istio URL change
When the `public-route` relation data changes (external_host or tls_enabled updated by istio provider), the charm SHALL update the `ui-endpoint-info` databag with all endpoint URLs built from the new public base URL.

#### Scenario: Endpoint URLs reflect new istio host
- **WHEN** the istio provider updates `external_host` to `"new.host.example.com"`
- **THEN** `ui-endpoint-info` SHALL be updated with all endpoint URLs prefixed by the new base URL (e.g., `login_url` = `"http://new.host.example.com/ui/login"`)

#### Scenario: Endpoint URLs empty when relation broken
- **WHEN** the `public-route` relation is broken
- **THEN** `ui-endpoint-info` SHALL be updated with empty-prefix endpoint URLs (e.g., `login_url` = `"/ui/login"`)

---

### Requirement: Listener port matches TLS status
When `tls_enabled` is `True`, the charm SHALL declare the Gateway listener on port 443. When `tls_enabled` is `False`, the charm SHALL declare the listener on port 80. This ensures HTTPS traffic reaches the standard port and HTTP traffic reaches the standard port.

#### Scenario: Listener port 443 when TLS enabled
- **WHEN** `tls_enabled` is `True`
- **THEN** all `HTTPRoute` objects in the submitted config SHALL reference `listener.port == 443`

#### Scenario: Listener port 80 when TLS disabled
- **WHEN** `tls_enabled` is `False`
- **THEN** all `HTTPRoute` objects in the submitted config SHALL reference `listener.port == 80`

---

### Requirement: Integration tests use istio-k8s and istio-ingress-k8s
The integration test suite SHALL deploy `istio-k8s` and `istio-ingress-k8s` (channel `2/stable`, `trust=True`) as ingress dependencies, replacing the former Traefik deployment. The `public-route` relation SHALL be integrated with `istio-ingress-k8s:istio-ingress-route`.

#### Scenario: Integration test deployment
- **WHEN** `test_build_and_deploy` runs
- **THEN** `istio-k8s` and `istio-ingress-k8s` SHALL be deployed and active
- **AND** the login-ui `public-route` endpoint SHALL be integrated with `istio-ingress-k8s:istio-ingress-route`

#### Scenario: Public address read from relation databag
- **WHEN** the `public_address` fixture is used
- **THEN** it SHALL return `external_host` from the `public-route` relation app databag

---

### Requirement: Operator migration document provided
A `docs/migration-traefik-to-istio.md` document SHALL be included that describes the step-by-step procedure for operators migrating from the Traefik integration to the Istio integration, including the required sequence of Juju commands and rollback instructions.

#### Scenario: Migration document exists in repository
- **WHEN** the repository is inspected after the change
- **THEN** `docs/migration-traefik-to-istio.md` SHALL exist and contain commands for removing the Traefik relation, upgrading the charm, and adding the Istio relation
