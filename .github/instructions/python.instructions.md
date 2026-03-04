---
applyTo: "**/*.py"
---

# Naming conventions
- Use `snake_case` for variables, functions, and methods.
- Use `ALL_CAPS` for module-level constants (_e.g., `LOCK_DIR`, `API_ENDPOINT`_).
- Use `PascalCase` for classes and enums (_e.g., `SomeClass`, `SomeEnum`_).
- Use single-underscore prefix (`_`) for private methods and instance attributes (_e.g., `_some_function`, `self._some_attribute`_).
- Use double-underscore prefix (`__`) for class-level private constants with name mangling (_e.g., `__SOME_VALUE`, `__SOME_VALUE_MAX_SIZE`_).

# Error handling
- Use custom exception classes nested inside the relevant class (_e.g., `SomeClass.SomeSpecificError`_) for domain-specific errors.
- Use `ValueError` for input validation failures.
- Use `try`/`except` with specific exception types. Log errors instead of re-raising (_in async/callback contexts_).
- Use `contextlib.suppress()` for non-critical exceptions that should be silently ignored (_e.g., `contextlib.suppress(OSError)`_).

# Code formatting
- Follow PEP 8 style guide for Python code formatting.
- Use blank lines to separate logical blocks of code for better readability.
- Use 4 spaces per indentation level. Do not use tabs.

# Comments
- Use Google-style docstrings (_triple-quoted strings_) to document functions and classes. Include `Args:`, `Returns:`, `Yields:`, and `Raises:` sections where applicable.
- Class-level docstrings are required for all classes, including widgets and test modules. Method-level docstrings are required for all public methods, and private methods that perform non-trivial operations.
- For widget `__init__` methods that accept external dependencies (_e.g., `parent`, `device`, `config`_), add a docstring with an `Args:` section describing each parameter.
- Document class-level private constants using regular `#` comments placed above the constant. Do not use standalone triple-quoted string literals inside a class body for this purpose - they are not attached to the following assignment, do not appear in generated documentation, and create an unused string constant at class creation time.
- Use inline comments sparingly to explain non-obvious code sections. Avoid stating the obvious.
- Keep comments up to date with code changes to prevent confusion.
- Avoid using comments to disable code.

# Import ordering
- Follow PEP 8 import grouping: standard library first, then third-party, then local (`modulename.*`). Separate each group with a blank line.
- Within each group, place bare `import` statements before `from ... import` statements, each sub-group sorted alphabetically.

# Type hints
- Use type hints for function parameters and return types where applicable.
- Use `typing` module types (_`Optional`, `Dict`, `List`, `Set`, `Callable`, `Any`_) for complex annotations.
- Use modern union syntax (_`X | Y`_) where applicable.

# Best practices
- Use context managers (_`with` statements_) for resource management (_e.g., file handling, serial connections, threading locks_).
- Use list comprehensions and generator expressions for concise and efficient code where appropriate.
- Avoid using mutable global variables. Use module-level `ALL_CAPS` constants for configuration values.
- Always specify `encoding="utf-8"` when opening text files.
- Use f-strings for string formatting instead of `%` or `.format()`.
- Use `@dataclass` for data containers with manual `to_json()`/`from_json()` serialization methods. Dataclass fields must be typed.
- Use `Enum` for value enumerations.
- Use `ABC` + `@abstractmethod` for abstract interfaces.
- Use `@staticmethod` for utility methods that do not access instance or class state (_e.g., `Widgets` factory, `DataValidation` validators_).
- Use `@classmethod` for factory/deserialization methods (_e.g., `from_json`_).
- Use `widget.after(0, lambda: ...)` for thread-safe Tkinter/customtkinter UI updates from non-main threads.
