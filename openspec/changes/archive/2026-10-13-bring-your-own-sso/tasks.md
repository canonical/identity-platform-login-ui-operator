## 1. Option and relation

- [x] 1.1 Add the boolean option `byosso_enabled`, default `false`, to `charmcraft.yaml`
- [x] 1.2 Add the endpoint `sso-service-info` (interface `sso_service_info`, optional, limit 1) to `charmcraft.yaml`
- [x] 1.3 Add `sso-service-info` to the `requires` output of the Terraform module
- [x] 1.4 Add the package `sso-service-info` to `pyproject.toml`, at a commit of its repository, and update `uv.lock`
- [x] 1.5 Add `git` to the build packages of the charm
- [x] 1.6 Read `grpc_url` from `sso-service-info`, and handle the relation when it changes or breaks

## 2. Checks of the feature

- [x] 2.1 Read `privileged_session_max_age` from `kratos-info`, and update the `kratos_info` library to LIBPATCH 7
- [x] 2.2 Make the 9 checks in order before each plan, and set the status of the first check that fails
- [x] 2.3 Stop before the plan while a check fails

## 3. Workload

- [x] 3.1 Add `BYOSSO_ENABLED`, `SSO_SERVICE_GRPC_ADDRESS` and `KRATOS_PRIVILEGED_SESSION_MAX_AGE` to the environment when the feature is on

## 4. The field for Kratos

- [x] 4.1 Add the optional field `byosso_enabled` to the `login_ui_endpoints` library, LIBPATCH 6
- [x] 4.2 Write `byosso_enabled` after each plan that succeeds
- [x] 4.3 Write `byosso_enabled` with the endpoint URLs, but not while a check fails

## 5. Route

- [x] 5.1 Add the exact path `/api/v0/sso/complete` to the route `api-and-ui`

## 6. Unit tests

- [x] 6.1 Test the environment and the field `byosso_enabled` with the option on and with the option off
- [x] 6.2 Test the status for each absent relation, for each relation without data, and for each Kratos check
- [x] 6.3 Test that a check that fails adds no layer and leaves the field `byosso_enabled` unchanged
- [x] 6.4 Test the field `byosso_enabled` for a new `ui-endpoint-info` relation
- [x] 6.5 Test that the route configuration has the path `/api/v0/sso/complete`
