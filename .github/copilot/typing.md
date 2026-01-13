# Typing & Python Standards: Identity Platform Login UI Operator

## 1. Version Requirement
*   **Python 3.12+** syntax is mandatory.

## 2. Type Hinting
*   **Mandatory:** All function signatures (args and return) must be typed.
*   **Modern Syntax:**
    *   ❌ **Bad:** `typing.List[str]`, `typing.Optional[int]`, `typing.Union[str, int]`
    *   ✅ **Good:** `list[str]`, `int | None`, `str | int`
    *   ❌ **Bad:** `typing.Dict[str, Any]`
    *   ✅ **Good:** `dict[str, Any]`

## 3. Data Structures
*   **Strong Typing:** Do not pass raw `dict` objects between layers.
*   **Models:** Use `Pydantic` models or `frozen dataclasses` for data transfer objects (DTOs).

### Example: Integration Data
```python
@dataclass(frozen=True)
class DatabaseRelationData:
    username: str
    password: str
    endpoints: list[str]
```

## 4. Error Handling
*   **Approach:** EAFP (Easier to Ask Forgiveness than Permission).
*   **Prohibited:** Bare `except:` or `except Exception:`.
*   **Requirement:** Catch specific errors (e.g., `pebble.ConnectionError`, `KeyError`).
*   **Logging:** Never suppress an exception without logging it first.
