# bring-your-own-sso Specification

## Purpose

"Bring Your Own SSO" is a feature of the login UI. With this feature, a tenant registers its own OIDC identity provider, and the members of the tenant sign in with that provider. This capability says how an operator turns the feature on in the charm. It also says what the charm needs from other charms for the feature, what the workload gets, and what the charm tells Kratos.

This specification uses these terms:

- To plan the workload is to give Pebble the layer of the service, with its environment, and to start or replan the service.
- The checks of the feature are the 9 checks of the requirement "What the feature needs".

Key decisions:

- **The feature is off by default.** While the option is off, the workload gets the same environment as without this capability. The leader then writes the text `false` in `ui-endpoint-info`.
- **The charm plans nothing while a check fails.** There are 2 reasons. The login UI refuses to start when `BYOSSO_ENABLED` is on and something that the feature needs is absent. A login UI with the feature off does not enforce the sign-in policies of the tenants. Thus the charm does not plan the workload with the feature, and it does not plan the workload without the feature. It shows the check in its status and leaves the workload as it is.
- **The checks include 2 settings of Kratos.** Check 8 fails when Kratos runs with OIDC-WebAuthn sequencing, and check 9 fails when Kratos runs without verification. The charm relies on the Kratos charm to block on the same 2 settings. Without checks 8 and 9, the login UI runs the feature while Kratos is not configured for it.
- **The charm tells Kratos about the feature in `ui-endpoint-info`.** The value comes from the option, and the charm writes it only while no check fails. While a check fails, the workload stays as it is. Thus the value that Kratos has also stays as it is.
- **The age of a privileged session comes from Kratos.** The login UI must apply the same age as Kratos. Thus the charm takes the value from `kratos-info` and has no option for it.

Non-goals:

- The configuration of Kratos for the feature. The charm relies on the Kratos charm for that.
- Credentials for the calls of the login UI to the Tenant Service and the SSO Service. The login UI makes these calls with no token, and the charm gives the workload no credentials for them.
- A check that the workload image has the feature, or that the service runs. The charm does not read the workload for this capability.
- A check that the Tenant Service and the SSO Service answer at their addresses.
- The host of the SSO Service. The charm relies on the deployment to serve the pages of the SSO Service on the host of the login UI.
- The route `/api/v0/sso/complete` on the gateway. The `istio-public-route` capability has that route, and the route does not depend on the option.

Compatibility:

- The capability has no breaking change. It adds an option, a relation endpoint and a field of `ui-endpoint-info`, and it changes or removes none.
- These 4 parts apply also while the option is off:
  - The leader writes `byosso_enabled` as `false` in `ui-endpoint-info`.
  - The charm has the relation endpoint `sso-service-info`.
  - The gateway has the route `/api/v0/sso/complete`.
  - The build of the charm needs `git`, because one dependency comes from a git repository.
- The feature needs a Kratos charm that writes `privileged_session_max_age` in `kratos-info`. Check 7 fails with a Kratos charm that does not write the field.

## Requirements
### Requirement: The option byosso_enabled
The charm SHALL have a boolean option `byosso_enabled` that turns on "Bring Your Own SSO" in the workload. The default is `false`. While the option is off, the charm SHALL plan the workload without the feature, and it SHALL make none of the checks of the feature.

#### Scenario: The option is off
- **WHEN** `byosso_enabled` is off
- **AND** the `tenant-service-info`, `sso-service-info` and `kratos-info` relations have their data
- **THEN** the charm plans the workload without `BYOSSO_ENABLED`, `SSO_SERVICE_GRPC_ADDRESS` and `KRATOS_PRIVILEGED_SESSION_MAX_AGE`
- **AND** the unit status is active

#### Scenario: The option is off and a relation of the feature is absent
- **WHEN** `byosso_enabled` is off and there is no `sso-service-info` relation
- **THEN** the charm makes no check of the feature
- **AND** the charm plans the workload

### Requirement: The sso-service-info relation
The charm SHALL require the relation endpoint `sso-service-info` with the interface `sso_service_info`. The endpoint is optional and takes at most 1 relation. The charm SHALL read the gRPC address of the SSO Service from the field `grpc_url` in the application data of the SSO Service. The charm uses the address only while `byosso_enabled` is on.

When the relation changes or breaks, the charm SHALL start its usual sequence again. In that sequence the charm makes the checks of the feature while the option is on, and then it plans the workload.

The `requires` output of the Terraform module of the charm SHALL list the endpoint.

#### Scenario: The address arrives after the relation
- **WHEN** `byosso_enabled` is on and the `sso-service-info` relation has no `grpc_url`
- **AND** checks 1 and 2 pass
- **THEN** the unit status is waiting with `Waiting for sso-service-info data`

#### Scenario: The SSO Service writes its address
- **WHEN** the unit status is waiting with `Waiting for sso-service-info data` and the SSO Service writes `grpc_url`
- **AND** no other check fails
- **THEN** the charm plans the workload with that address

#### Scenario: The operator removes the relation
- **WHEN** `byosso_enabled` is on and the operator removes the `sso-service-info` relation
- **AND** checks 1 and 2 pass
- **THEN** the unit status is blocked with `Missing integration sso-service-info`
- **AND** the charm does not plan the workload

### Requirement: What the feature needs
While `byosso_enabled` is on, the charm SHALL make the checks of this table each time before it plans the workload. The charm SHALL make the checks in the order of the table. The first check that fails sets the unit status, and the charm makes no later check.

| check | the check fails when | unit status |
| --- | --- | --- |
| 1 | there is no `tenant-service-info` relation | blocked, `Missing integration tenant-service-info` |
| 2 | the `tenant-service-info` relation does not have its data | waiting, `Waiting for tenant-service-info data` |
| 3 | there is no `sso-service-info` relation | blocked, `Missing integration sso-service-info` |
| 4 | the `sso-service-info` relation does not have its data | waiting, `Waiting for sso-service-info data` |
| 5 | there is no `kratos-info` relation | blocked, `Missing integration kratos-info` |
| 6 | the `kratos-info` relation does not have its data | waiting, `Waiting for kratos-info data` |
| 7 | `kratos-info` has no `privileged_session_max_age` | blocked, `byosso_enabled needs a newer Kratos charm: refresh it` |
| 8 | `oidc_webauthn_sequencing_enabled` in `kratos-info` is true | blocked, `byosso_enabled conflicts with Kratos OIDC-WebAuthn sequencing` |
| 9 | `verification_enabled` in `kratos-info` is not true | blocked, `byosso_enabled requires Kratos's enable_verification` |

The status messages use the word "integration" for a relation.

A relation has its data when the application data of the remote application has these contents:

- For `tenant-service-info`: a `service_url` and a `grpc_url`. The `service_url` must be an `http` or `https` URL with a host.
- For `sso-service-info`: a `grpc_url` that is not empty.
- For `kratos-info`: one field or more.

For checks 8 and 9, the charm reads a field of `kratos-info` as true only when its text is `true`, in any letter case. Thus a `verification_enabled` that is absent fails check 9. An `oidc_webauthn_sequencing_enabled` that is absent passes check 8.

The charm makes these checks after 2 checks that do not depend on the option. Those 2 checks are that the charm can connect to the workload container, and that the peer relation exists.

The charm makes the checks in a hook that runs its usual sequence. The removal of the `kratos-info` relation starts no such hook. The unit status then shows check 5 in the next such hook, for example `update-status`.

#### Scenario: More than one check fails
- **WHEN** `byosso_enabled` is on and there is no `tenant-service-info` relation
- **AND** `kratos-info` has `oidc_webauthn_sequencing_enabled` as `True`
- **THEN** the unit status is blocked with `Missing integration tenant-service-info`

#### Scenario: Kratos runs with OIDC-WebAuthn sequencing
- **WHEN** `byosso_enabled` is on and checks 1 to 7 pass
- **AND** `kratos-info` has `oidc_webauthn_sequencing_enabled` as `True`
- **THEN** the unit status is blocked with `byosso_enabled conflicts with Kratos OIDC-WebAuthn sequencing`

#### Scenario: Kratos runs without verification
- **WHEN** `byosso_enabled` is on and checks 1 to 8 pass
- **AND** `kratos-info` has `verification_enabled` as `False`
- **THEN** the unit status is blocked with `byosso_enabled requires Kratos's enable_verification`

#### Scenario: All the checks pass
- **WHEN** `byosso_enabled` is on and all 9 checks pass
- **THEN** the charm plans the workload with the feature
- **AND** the unit status is active when the plan succeeds

### Requirement: The charm plans nothing while a check fails
While a check of the feature fails, the charm SHALL NOT plan the workload. The charm adds no layer, and it does not start, restart or stop the service. A service that runs keeps the environment of its last plan. The charm SHALL plan the workload the next time that it makes the checks and all of them pass.

The leader continues to submit its routes on `public-route` while a check fails, because that step comes before the checks.

While a check fails, the charm also does not push the CA certificates in its usual sequence, because that step comes after the checks. The charm continues to push them in a certificate event of `receive-ca-cert`.

#### Scenario: A relation of the feature goes away
- **WHEN** the workload runs with the feature and the operator removes the `tenant-service-info` relation
- **THEN** the unit status is blocked with `Missing integration tenant-service-info`
- **AND** the charm does not change the layer or the service

#### Scenario: A new container while a check fails
- **WHEN** Pebble becomes ready in a new workload container while a check of the feature fails
- **THEN** the charm adds no layer to the container and does not start the service
- **AND** the unit status comes from the check that fails

### Requirement: The environment of the workload with the feature
When `byosso_enabled` is on and all the checks of the feature pass, the charm SHALL add these variables to the environment of the workload:

| variable | value |
| --- | --- |
| `BYOSSO_ENABLED` | true |
| `SSO_SERVICE_GRPC_ADDRESS` | the `grpc_url` of `sso-service-info` |
| `KRATOS_PRIVILEGED_SESSION_MAX_AGE` | the `privileged_session_max_age` of `kratos-info` |

The charm SHALL NOT set these 3 variables while the option is off. The option changes no other variable.

The charm sets `TENANT_SERVICE_GRPC_ADDRESS` and `MULTI_TENANCY_ENABLED` for a `tenant-service-info` relation that has its data, with the option on or off. Thus a workload with the feature always has these 2 variables, because check 2 passes.

#### Scenario: The charm plans the workload with the feature
- **WHEN** `byosso_enabled` is on and all the checks pass
- **AND** `sso-service-info` has `grpc_url` as `sso-service.example:50051`
- **AND** `kratos-info` has `privileged_session_max_age` as `1h`
- **THEN** the environment has `BYOSSO_ENABLED` as true and `SSO_SERVICE_GRPC_ADDRESS` as `sso-service.example:50051`
- **AND** the environment has `KRATOS_PRIVILEGED_SESSION_MAX_AGE` as `1h`
- **AND** the environment has `MULTI_TENANCY_ENABLED` as true

### Requirement: The age of a privileged session comes from Kratos
With the feature on, the charm SHALL take the age of a privileged session from the field `privileged_session_max_age` of `kratos-info`. The charm SHALL pass the text of the field to the workload without a change, as `KRATOS_PRIVILEGED_SESSION_MAX_AGE`. The charm has no option for this value. A Kratos charm that does not publish the field fails check 7, and the status tells the operator to refresh that charm.

#### Scenario: Kratos does not publish the age
- **WHEN** `byosso_enabled` is on and checks 1 to 6 pass
- **AND** `kratos-info` has no `privileged_session_max_age`
- **THEN** the unit status is blocked with `byosso_enabled needs a newer Kratos charm: refresh it`
- **AND** the charm does not plan the workload

#### Scenario: Kratos changes the age
- **WHEN** the workload runs with the feature and Kratos writes a new `privileged_session_max_age`
- **AND** all the checks continue to pass
- **THEN** the charm plans the workload with the new value

### Requirement: The field byosso_enabled of ui-endpoint-info
The leader SHALL write the field `byosso_enabled` in its application data of every `ui-endpoint-info` relation. The value is the text `true` when the option `byosso_enabled` is on, and the text `false` when the option is off. The field is an optional text of `LoginUIProviderData` in the `login_ui_endpoints` library.

The leader SHALL write the field at these 2 times:

- After each plan of the workload that succeeds.
- With the endpoint URLs, when a `ui-endpoint-info` relation is created and when the `public-route` relation changes or breaks.

While a check of the feature fails, the charm SHALL NOT write the field. A value that a relation has stays as it is, and a new relation gets no value. The charm continues to write the endpoint URLs.

The charm takes the value from its option, and it does not read the workload. Thus the text `true` says that the charm plans the workload with the feature. It does not say that the service runs. The write with the endpoint URLs does not depend on a plan. It can come before the first plan of the workload, and after a plan that failed.

A unit that is not the leader writes nothing to the relation. The charm relies on the Kratos charm to read the field and to configure Kratos for the feature.

#### Scenario: The leader writes true after a plan with the feature
- **WHEN** `byosso_enabled` is on, all the checks pass and the plan succeeds
- **THEN** the leader writes `byosso_enabled` as `true` in every `ui-endpoint-info` relation

#### Scenario: The leader writes false after a plan without the feature
- **WHEN** `byosso_enabled` is off and the plan succeeds
- **THEN** the leader writes `byosso_enabled` as `false` in every `ui-endpoint-info` relation

#### Scenario: A check fails after the leader wrote true
- **WHEN** a `ui-endpoint-info` relation has `byosso_enabled` as `true`
- **AND** the operator removes the `sso-service-info` relation
- **THEN** the charm does not write the field
- **AND** the relation continues to have `byosso_enabled` as `true`

#### Scenario: A new ui-endpoint-info relation while a check fails
- **WHEN** an application relates to `ui-endpoint-info` while a check of the feature fails
- **THEN** the leader writes the endpoint URLs in the new relation
- **AND** the new relation has no `byosso_enabled` until the checks pass and the leader writes the field

#### Scenario: A new ui-endpoint-info relation while the checks pass
- **WHEN** an application relates to `ui-endpoint-info` while `byosso_enabled` is on and all the checks pass
- **THEN** the leader writes the endpoint URLs and `byosso_enabled` as `true` in the new relation

#### Scenario: The operator turns the option off
- **WHEN** the workload runs with the feature and the operator sets `byosso_enabled` to `false`
- **THEN** the charm plans the workload without the 3 variables of the feature
- **AND** the leader then writes `byosso_enabled` as `false`

#### Scenario: The plan fails
- **WHEN** Pebble fails to start the service in a hook that does not write the endpoint URLs
- **THEN** the unit status is blocked with `Failed to replan, please consult the logs`
- **AND** the charm does not write `byosso_enabled` in that hook

#### Scenario: A unit that is not the leader
- **WHEN** a unit that is not the leader plans its workload with the feature
- **THEN** the unit writes nothing to `ui-endpoint-info`
