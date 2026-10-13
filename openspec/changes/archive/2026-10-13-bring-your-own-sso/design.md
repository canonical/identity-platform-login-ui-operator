## Context

The login UI runs "Bring Your Own SSO" when its setting `BYOSSO_ENABLED` is on. With the feature, the login UI calls the Tenant Service and the SSO Service over gRPC. It also decides itself when a sign-in needs MFA. The login UI refuses to start when the feature is on and something that the feature needs is absent.

The charm already has 2 of the relations that the feature needs. The `tenant-service-info` relation gives the address of the Tenant Service, and the `kratos-info` relation gives the settings of Kratos. The charm also gives its endpoint URLs to other charms in `ui-endpoint-info`. The Kratos charm is one of the charms that read that relation.

In this document, to plan the workload is to give Pebble the layer of the service and to start or replan the service.

## Goals / Non-Goals

**Goals:**

- One option turns the feature on. The charm gets all other values from its relations.
- The unit status tells the operator what the feature needs.
- The charm leaves a workload that runs the feature as it is when a relation goes away.

**Non-Goals:**

- The configuration of Kratos for the feature. The Kratos charm does that work.
- Credentials for the calls to the Tenant Service and the SSO Service. The login UI makes these calls with no token.
- A check that the workload image has the feature.

## Decisions

### 1. The charm plans nothing while a check fails

**Decision:** While the option is on and a check of the feature fails, the charm sets its status and stops before the plan. It does not plan the workload with the feature, and it does not plan the workload without the feature.

**Reason:** The login UI refuses to start when `BYOSSO_ENABLED` is on and something that it needs is absent. A login UI with the feature off does not enforce the sign-in policies of the tenants. Thus the 2 possible plans are both wrong, and the charm leaves the workload as it is.

**Alternatives that we turned down:**

- A plan without the feature until all the checks pass. With such a plan, a relation that goes away stops the enforcement of the sign-in policies of the tenants.
- A plan with the feature. The service does not start with such a plan.

### 2. The checks include 2 settings of Kratos

**Decision:** The charm blocks the feature when Kratos runs with OIDC-WebAuthn sequencing, and when Kratos runs without verification. The charm reads both settings from `kratos-info`.

**Reason:** The charm relies on the Kratos charm to block on the same 2 settings. Without these checks, the login UI runs the feature while Kratos is not configured for the feature.

### 3. The charm tells Kratos in ui-endpoint-info, and takes the value from its option

**Decision:** The leader writes `byosso_enabled` in `ui-endpoint-info`. The value is the text `true` or the text `false`, as the option says. The leader writes the field after each plan that succeeds, and together with the endpoint URLs. It does not write the field while a check of the feature fails.

**Reason:** There are 2 reasons:

- Kratos must change its configuration only for a login UI that the charm plans with the feature.
- While a check fails, the workload stays as it is. Thus the value that Kratos has must also stay as it is. If the charm writes `false` at that time, Kratos and a workload that runs the feature disagree.

**Alternative that we turned down:** A value that the charm reads from the Pebble plan and from the state of the service. That value needs calls to Pebble in each hook. The option and the checks give the charm its answer without those calls.

### 4. The age of a privileged session comes from kratos-info

**Decision:** The charm passes the `privileged_session_max_age` of `kratos-info` to the workload as `KRATOS_PRIVILEGED_SESSION_MAX_AGE`. The charm has no option for this value. When `kratos-info` does not have the field, the charm blocks the feature and tells the operator to refresh the Kratos charm.

**Reason:** The login UI must apply the same age as Kratos. Kratos knows the age that it runs with, so the charm takes the value from there.

**Alternative that we turned down:** An option of this charm. Such an option is a second copy of the value, and the operator must keep the 2 copies equal.

The status for an absent field is blocked and not waiting. The field does not arrive until the operator refreshes the Kratos charm, and the message says so.

### 5. The sso_service_info library is a Python package from git

**Decision:** The charm installs the library as the Python package `sso-service-info`. The package comes from a commit of the repository of the SSO Service charm, from its directory `interfaces/sso_service_info`. The pin is in `pyproject.toml` and in `uv.lock`, and `git` is in the build packages of the charm.

**Reason:** Charmhub takes no new libraries. Thus `charmcraft fetch-lib` cannot get this library.

## Risks / Trade-offs

- **A new container while a check fails.** The charm adds no layer to a workload container that starts while a check fails. The charm does not start the service there until all the checks pass. The unit status shows the check that fails.
- **The value in ui-endpoint-info can be ahead of the workload.** The leader writes the field with the endpoint URLs when a `ui-endpoint-info` relation is created. That write can come before the first plan, and after a plan that failed. The charm does not read the workload, so the text `true` does not prove that the service runs.
- **The 2 charms act in different hooks.** After the operator changes the option, this charm plans the workload first. The Kratos charm changes Kratos later, in a hook of its own. Between the 2 hooks, Kratos and the login UI can disagree about the feature.
- **An older revision of the charm.** A revision from before this change does not write `byosso_enabled`. After a refresh to such a revision, the last value stays in the relation data. Turn the option off before such a refresh.
- **The build needs the repository of the SSO Service charm.** The build of the charm gets the library with `git`. The commit in `pyproject.toml` and in `uv.lock` must exist in that repository.
- **The charm checks relation data only.** The charm does not check that the Tenant Service and the SSO Service answer at their addresses.
