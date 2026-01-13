# Architecture & Patterns: Identity Platform Login UI Operator

## 1. The 3-Layer Architecture
This project follows a strict separation of concerns. Violating these boundaries is a critical failure.

### Layer 1: Orchestration (`src/charm.py`)
*   **Role:** The "Traffic Controller".
*   **Responsibilities:** 
    *   Observe Juju events.
    *   Retrieve data from Sources (Configs, Integrations).
    *   Decide on the state.
    *   Push data to Sinks (Workload, Relations).
*   **Strict Prohibitions:**
    *   **NO Business Logic:** Do not calculate things here.
    *   **NO Raw Pebble Commands:** `container.push()`, `pebble.replan()` belong in services.
    *   **NO Kubernetes API Calls:** Use `lightkube` only via a Service wrapper.
*   **Pattern:** `Event -> State Check -> Service Call -> Status Update`.

### Layer 2: Abstraction (`src/services.py`, `src/integrations.py`)
*   **`src/services.py`**:
    *   Encapsulates the Workload (Pebble) and Platform (K8s).
    *   Methods must be **atomic** (e.g., `restart_service`, `write_config`).
    *   Must raise specific custom exceptions (e.g., `WorkloadNotReadyError`), never generic `Exception`.
*   **`src/integrations.py`**:
    *   Strictly typed wrappers for relation data.
    *   Use `@dataclass(frozen=True)` for all relation data schemas.
    *   Validation logic for relation data belongs here.

### Layer 3: Infrastructure
*   Libraries like `ops` (Juju SDK) and `lightkube`.
*   Interacted with **only** via Layer 2 (Abstraction) or standard `ops` hooks in Layer 1.

## 2. "No-Go" Examples
*   ❌ **Bad:** Calling `self.unit.get_container("workload").push(...)` inside `charm.py`.
    *   ✅ **Good:** `self.workload_service.write_config(...)`
*   ❌ **Bad:** Parsing a raw dict from `relation.data` inside `charm.py`.
    *   ✅ **Good:** `data = HydraEndpointsData.load(relation.data)`
