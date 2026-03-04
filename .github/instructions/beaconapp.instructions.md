---
applyTo: "App/**"
---

> Python coding conventions (_naming, error handling, formatting, type hints_) are defined in [python.instructions.md](./python.instructions.md).

## BEACON.App source code
The **BEACON.App Python source code** is located in the `App/` directory and is responsible for:
- Supporting communication between the hardware device (_WSPR-beacon_) and the desktop user application (_BEACON.App_) via USB (_Serial_) or Wi-Fi (_WebSocket_) connections using control commands in JSON format.
- Generating valid JSON control commands sent to the device (_WSPR-beacon_) to set the active transmission mode, run self-checks, and configure device parameters (_calibration, Wi-Fi connection_).
- Providing a device firmware update mechanism both via USB and through OTA updates.
- Ensuring the reliability of the user application by implementing integration and unit tests to verify the functionality of implemented features.

The application source code is organized into the following subpackages within `App/beaconapp/`:
- `transports/` - transport layer implementations.
- `ui/` - user interface widgets and graphical resources.
- `tests/` - test suite, split into `unit/` and `integration/` subdirectories.

**BEACON.App** is designed to work only with devices based on the **ESP32-C3 SoC**. Devices based on the **ATmega328P MCU** are not supported!

### Build environment
- **Build system (_GitHub Actions_):** PyInstaller.
- **Build configuration file (_Linux, GitHub Actions_):** `.github/workflows/app-build-linux.yml`.
- **Build configuration file (_Windows, GitHub Actions_):** `.github/workflows/app-build-windows.yml`.
- **Test configuration file (_GitHub Actions_):** `.github/workflows/app-tests.yml`.
- **Python standard:** 3.12.

# Async and threading
The application uses a two-thread architecture:
- **Main thread** runs the Tkinter/customtkinter event loop (_UI_). All UI manipulations must happen on this thread.
- **Asyncio thread** is a dedicated daemon thread running `asyncio.run_forever()` that handles USB (_Serial_) and Wi-Fi (_WebSocket_) transport I/O.

Communication between threads:
- **Main -> asyncio**: Use `asyncio.run_coroutine_threadsafe()` to schedule coroutines, or `loop.call_soon_threadsafe()` for synchronous calls into the event loop.
- **Asyncio -> UI**: Transport layers decode incoming JSON messages and invoke registered callback handlers via `Device._call_handlers()`. Callbacks that update UI must use `widget.after(0, lambda: ...)` to marshal the call onto the main thread.

The UI registers its callbacks for device message types via `Device.set_device_response_handlers()`, forming a message-driven architecture where the `Device` class acts as the bridge between transports and UI.

Threading primitives:
- Use `asyncio.Queue` for outgoing message passing between the main thread and the asyncio transmit loop.
- Use `threading.Lock` for protecting shared state (_e.g., connection state_).
- Use `threading.Event` for cross-thread synchronization (_e.g., waiting for the event loop to start_).
- Use `threading.Thread(target=..., daemon=True)` for background work dispatch (_e.g., USB firmware update_).
- Any new functionality that may block the UI thread or the asyncio thread must be executed in a separate thread to prevent freezing the interface or stalling transport I/O.

# Logging
- Use the logging facade in `logger.py` (_`log_ok`, `log_error`, `log_warning`, `log_rx_message`, `log_tx_message`_) instead of calling the `logging` module or `print()` directly.
- Debug mode is controlled by the `--debug` CLI argument.

# Testing conventions
- Any new functionality must be covered by unit tests. Features that involve hardware interaction must also be covered by integration tests.
- Use **pytest** as the primary test framework.
- Mark every unit test with `@pytest.mark.unit` and every integration test with `@pytest.mark.integration`.
- Use `@pytest.mark.parametrize` for data-driven tests. Place `@pytest.mark.parametrize` **before** the marker decorator (_e.g., `@pytest.mark.unit`_) in the decorator stack.
- Use `tmp_path` (pytest built-in) for temporary file operations in tests. Use `os.path.dirname(__file__)` for loading test fixture files.
- Gate integration tests with `@pytest.mark.skipif(not find_device(), reason="...")` when they require a connected hardware device.
- Add Google-style docstrings to test functions to describe what is being verified.
- Use `pytest.raises()` with an optional `match=` parameter for exception testing.
- Use **pytest-cov** for measuring test coverage. Run coverage with `python -m pytest --cov=beaconapp --cov-config=pytest.ini`. Coverage configuration is defined in `App/pytest.ini` and excludes test files, `__init__.py`, and `main.py` (_application entry point_) to focus on business logic coverage.

# Auxiliary tools
- **pip**: Package manager for installing project dependencies. Runtime dependencies are listed in `App/requirements.txt`, development dependencies in `App/requirements-dev.txt`.
- **flake8**: The project uses flake8 with plugins for linting, code style enforcement, cyclomatic complexity checking, and static analysis (_bugbear, builtins, comprehensions, eradicate, simplify_). Refer to the `App/.flake8` file for the configuration.
