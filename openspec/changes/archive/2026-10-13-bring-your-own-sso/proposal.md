## Why

The login UI has a feature, "Bring Your Own SSO". With this feature, a tenant registers its own OIDC identity provider, and the members of the tenant sign in with that provider. The login UI then also decides when a sign-in needs MFA.

The charm has no way to turn the feature on. The workload needs 3 values from other charms to run the feature:

- The address of the Tenant Service.
- The address of the SSO Service.
- The age of a privileged session of Kratos.

Kratos must also know that the login UI runs the feature.

## What Changes

- A new boolean option, `byosso_enabled`, turns the feature on. The default is `false`.
- A new relation endpoint, `sso-service-info`, gives the charm the gRPC address of the SSO Service. Its interface is `sso_service_info`.
- While the option is on, the charm makes these checks before each plan of the workload:
  - The `tenant-service-info`, `sso-service-info` and `kratos-info` relations exist, and each has its data.
  - `kratos-info` has a `privileged_session_max_age`.
  - Kratos runs with verification and without OIDC-WebAuthn sequencing.
- While a check fails, the unit status shows that check, and the charm plans nothing. The workload stays as it is.
- When all the checks pass, the charm plans the workload with `BYOSSO_ENABLED`, `SSO_SERVICE_GRPC_ADDRESS` and `KRATOS_PRIVILEGED_SESSION_MAX_AGE`.
- The leader writes the field `byosso_enabled` in `ui-endpoint-info`. The value is the text `true` or the text `false`, as the option says. The leader does not write the field while a check fails.
- The `login_ui_endpoints` library gets the field `byosso_enabled` (LIBPATCH 6).
- The copy of the `kratos_info` library moves to LIBPATCH 7, which has `privileged_session_max_age`.
- The gateway gets one more route, the exact path `/api/v0/sso/complete`.

These 4 parts of the change apply also while the option is off:

- The route `/api/v0/sso/complete` is on the gateway.
- `ui-endpoint-info` has `byosso_enabled` as `false`.
- The charm has the relation endpoint `sso-service-info`, and the Terraform module lists it. The charm does not use the address while the option is off.
- The build of the charm needs `git`, because one dependency comes from a git repository.

The file of the `istio-public-route` specification gets a title, a `## Purpose` section and the `## Requirements` heading. The `openspec archive` command needs them before it can add a requirement to the file. The requirements that the file had do not change.

## Capabilities

### New Capabilities

- `bring-your-own-sso`: the option `byosso_enabled`, the checks of what the feature needs, the environment of the workload with the feature, and the field `byosso_enabled` of `ui-endpoint-info`.

### Modified Capabilities

- `istio-public-route`: one more route, the exact path `/api/v0/sso/complete`.

## Impact

- `charmcraft.yaml`: the option, the relation endpoint, and `git` in the build packages.
- `pyproject.toml` and `uv.lock`: the package `sso-service-info`, at a commit of the repository of the SSO Service charm.
- `src/charm.py`, `src/integrations.py`, `src/services.py`, `src/utils.py`, `src/constants.py`, and their unit tests.
- `lib/charms/identity_platform_login_ui_operator/v0/login_ui_endpoints.py` (LIBPATCH 6).
- `lib/charms/kratos/v0/kratos_info.py` (LIBPATCH 7).
- `terraform/outputs.tf`: the endpoint `sso-service-info` in the `requires` output.
- Other charms:
  - The feature needs a Kratos charm that writes `privileged_session_max_age` in `kratos-info`.
  - The charm relies on the Kratos charm to read `byosso_enabled` and to configure Kratos for the feature.
  - The feature needs a charm that provides `sso-service-info`.
- A deployment that leaves the option off gets only the 4 parts of the list above.
