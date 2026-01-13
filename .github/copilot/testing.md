# Testing Standards: Identity Platform Login UI Operator

## 1. Unit Tests (`tests/unit`)
*   **Framework:** `ops.testing` (Scenario) is the **MANDATORY** standard.
*   **Prohibited:** Do not use `ops.testing.Harness`. It is legacy.
*   **Structure:** Follow the AAA pattern (Arrange, Act, Assert) with blank lines for separation. **NO comments** like `# Arrange`, `# Act`, `# Assert` in function bodies.
*   **Organization:** Class-based grouping by event type (e.g., `TestPebbleReadyEvent`).
*   **Fixtures:** Use atomic → composed fixture hierarchy for reusability.
*   **Mocking:**
    *   Mock external service calls (e.g., `WorkloadService.restart`).
    *   **NEVER** mock the Charm object itself or `ops` framework internals unless absolutely necessary.

### Test Organization Pattern

Tests MUST be organized into classes by event type or feature area:

```python
class TestPebbleReadyEvent:
    """Tests for pebble_ready event handling."""

    @pytest.mark.parametrize("leader", [True, False])
    def test_pebble_ready_leadership_scenarios(
        self,
        context: ops.testing.Context,
        base_state: ops.testing.State,
        peer_relation: ops.testing.PeerRelation,
        leader: bool,
    ) -> None:
        """Test pebble_ready with different leadership states."""
        state_in = replace(base_state, leader=leader, relations=[peer_relation])

        container = state_in.get_container(WORKLOAD_CONTAINER_NAME)
        state_out = context.run(context.on.pebble_ready(container), state_in)

        assert state_out.unit_status == ActiveStatus()
```

### Fixture Hierarchy

Fixtures follow three-tier hierarchy:

1. **Atomic Fixtures** (Tier 1): Single-purpose, no dependencies
   - `container_can_connect`, `container_cannot_connect`
   - `leader_state`, `non_leader_state`

2. **Composed Fixtures** (Tier 2): Built from atomic fixtures
   - `base_state` (composed from `leader_state` + `container_can_connect`)

3. **Existing Fixtures** (Tier 3): Keep using
   - `context`, `peer_relation`, `kratos_relation`, etc.

### Example: Composed Fixture
```python
@pytest.fixture
def base_state(
    leader_state: bool,
    container_can_connect: ops.testing.Container,
) -> ops.testing.State:
    """Base charm state: leader with connectable container."""
    return ops.testing.State(
        leader=leader_state,
        containers=[container_can_connect],
    )
```

### Parametrization Pattern

Use `@pytest.mark.parametrize` for scenarios with similar logic:

```python
@pytest.mark.parametrize(
    "can_connect,expected_status",
    [
        (True, ActiveStatus()),
        (False, WaitingStatus("Waiting to connect to Login_UI container")),
    ],
)
def test_pebble_ready_connection_scenarios(
    self,
    context: ops.testing.Context,
    base_state: ops.testing.State,
    peer_relation: ops.testing.PeerRelation,
    can_connect: bool,
    expected_status,
) -> None:
    """Test pebble_ready with different container connection states."""
    container = base_state.get_container(WORKLOAD_CONTAINER_NAME)
    new_container = replace(container, can_connect=can_connect)
    state_in = replace(
        base_state,
        containers=[new_container],
        relations=[peer_relation],
    )

    state_out = context.run(context.on.pebble_ready(new_container), state_in)

    assert state_out.unit_status == expected_status
```

## 2. Integration Tests (`tests/integration`)
*   **Framework:** `pytest`.
*   **Tooling:** Prefer `jubilant` helpers if available in the environment.
*   **Coverage:** New features MUST include integration tests validating the charm in a real K8s environment.

## 3. General Rules
*   **Source of Truth:** `tox` runs the tests.
    *   `tox -e unit`
    *   `tox -e integration`
*   **No Mixed Patterns:** Do not mix Harness and Scenario in the same file.
