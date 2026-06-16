# Migration: Traefik → Istio Ingress

This document describes how operators should migrate from the `traefik-route`
integration to the `istio-ingress-route` integration when upgrading the
Identity Platform Login UI charm.

## Breaking Change

Starting from the charm revision that includes this change, the `public-route`
relation interface has changed from `traefik_route` to `istio_ingress_route`.
The relation **name** (`public-route`) is unchanged, but it must now be related
to an `istio-ingress-k8s` application instead of `traefik-k8s`.

Juju will block cross-interface relations, so the existing Traefik relation
**must be removed before upgrading** the charm.

## Migration Steps

### 1. Remove the Traefik relation (before upgrading)

```bash
juju remove-relation <login-ui-app>:public-route <traefik-app>:traefik-route
```

Verify the relation is removed:

```bash
juju status --relations
```

The Login UI charm will move to `active` without a public ingress (endpoints
will still be served internally within the cluster).

### 2. Upgrade the charm

```bash
juju refresh <login-ui-app> --channel <new-channel>
```

Wait for the unit to settle:

```bash
juju status <login-ui-app>
```

### 3. Relate to the Istio ingress application

Assuming `istio-ingress-k8s` is already deployed in the model:

```bash
juju relate <login-ui-app>:public-route <istio-ingress-app>:istio-ingress-route
```

Once the relation is established and `istio-ingress-k8s` has published the
`external_host`, the charm will submit the routing configuration and the
`ui-endpoint-info` databag will be updated with the public URLs.

Verify everything is healthy:

```bash
juju status <login-ui-app>
```

## Rollback

If you need to roll back to the previous charm revision (with Traefik):

1. Remove the Istio relation:

   ```bash
   juju remove-relation <login-ui-app>:public-route <istio-ingress-app>:istio-ingress-route
   ```

2. Refresh to the previous revision:

   ```bash
   juju refresh <login-ui-app> --revision <previous-revision>
   ```

3. Re-add the Traefik relation:

   ```bash
   juju relate <login-ui-app>:public-route <traefik-app>:traefik-route
   ```

## Route Behaviour Notes

All previously exposed paths are available through the Istio ingress:

| Path | Type | Notes |
|---|---|---|
| `/self-service/*` | PathPrefix | Rewritten to `/api/kratos/self-service/*` before forwarding |
| `/api/device` | Exact | — |
| `/api/consent` | Exact | — |
| `/api/v0/app-config` | Exact | — |
| `/api/v0/tenants/resolve` | Exact | — |
| `/api/v0/tenants` | Exact | — |
| `/api/v0/auth/tenant` | Exact | — |
| `/ui/*` | PathPrefix | — |

**Subtle difference in `/self-service` rewrite:** The previous Traefik
configuration used a regex `^/self-service/(.*)` which required a trailing
slash after the prefix. The Istio configuration uses
`ReplacePrefixMatch: /api/kratos/self-service` which matches the prefix
regardless of trailing slash. This is functionally equivalent for all known
Kratos self-service paths (e.g., `/self-service/login/api`).

**TLS/HTTPS:** The charm no longer forces HTTPS via URL rewriting. The scheme
of the public URL is determined by the `tls_enabled` flag published by the
`istio-ingress-k8s` provider. When TLS is enabled at the gateway level, the
charm will use `https://` for all endpoint URLs in the `ui-endpoint-info`
databag.
