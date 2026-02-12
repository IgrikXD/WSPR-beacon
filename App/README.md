# BEACON.App
A cross-platform GUI application for configuring and managing a [WSPR-beacon](https://github.com/IgrikXD/WSPR-beacon?tab=readme-ov-file#wspr-beacon) based on an ESP32 SoC. The application communicates with the device via USB or Wi-Fi to configure transmission parameters, perform hardware self-checks, and manage device setup (_including calibration and Wi-Fi configuration_).

![BeaconApp](../Resources/BeaconApp-Transmission-frame.png)

## Building
Download and install the [latest version of Python for Windows](https://www.python.org/downloads/).

### Clone the repository & install dependencies
```powershell
git clone https://github.com/IgrikXD/WSPR-beacon.git
cd WSPR-beacon/App
pip install --upgrade pip
pip install -r requirements.txt
```

There are two possible ways to use the application: [creating a monolithic executable file](#build-the-executable-file) (_recommended_) and [running the application from the source code](#run-the-application-without-building-the-executable) without prior build.

### Build the executable file (Windows)
```powershell
pip install -r requirements-dev.txt
pyinstaller --noconsole --onefile `
    --icon=beaconapp/ui/resources/beacon-app-logo.ico `
    --add-data "beaconapp/ui/resources/*;ui/resources" `
    --exclude-module beaconapp.tests `
    --name BeaconApp beaconapp/main.py
```

### Build the executable file (Linux)
```bash
pip install -r requirements-dev.txt
pyinstaller --noconsole --onefile \
    --add-data "beaconapp/ui/resources/*:ui/resources" \
    --exclude-module beaconapp.tests \
    --hidden-import PIL._tkinter_finder \
    --name BeaconApp beaconapp/main.py
```

After the build is complete, you can run the executable file located in the `dist` directory.

### Run the application without building the executable
To run the application directly without building an executable, use:
```powershell
python -m beaconapp.main
```

#### Debug mode
To enable debug mode and display messages about data exchange with the device in the console, use:
```powershell
python -m beaconapp.main --debug
```

## Testing

### Unit tests
> [!WARNING]  
> These tests help detect potential issues early but do not replace full validation on real hardware!

Unit tests are available to verify the application's core functionality, including:
- Correct formation of commands sent to the device
- Proper decoding of messages received from the device
- Correct processing of data retrieved from the [**WSPR.live API**](https://wspr.live/)
- Automatic selection of the appropriate communication transport (_USB or Wi-Fi_)
- Proper registration of message handlers for incoming device messages
- Validation of user-configured parameters
- Correct operation of data wrappers used for data exchange during device communication
- Correct saving and loading of the application's configuration file

To run the unit tests, install development dependencies and execute:
```powershell
pip install -r requirements-dev.txt
python -m pytest -m unit
```

### Integration tests
> [!WARNING]  
> These tests require a physical WSPR-beacon device connected via USB! Wi-Fi connection and GPS antenna must be disconnected during testing.

Integration tests are available to verify the core functionality of the device, including:
- Thread-safe concurrent `Device.connect()` calls without race conditions
- Successful device reconnection after a disconnect
- Complete device info retrieval (_active TX mode, Wi-Fi data, GPS status, calibration value, firmware/hardware info_)
- Correct setting of active TX mode, SI5351 calibration value and automatic SSID connection at device startup
- Calibration frequency generation control
- Wi-Fi connection handling with invalid credentials
- Handling incorrect request types and non-request messages by the device firmware

To run the integration tests, install development dependencies and execute:
```powershell
pip install -r requirements-dev.txt
python -m pytest -m integration
```

### Code coverage
> [!WARNING]  
> By default, coverage runs both [unit](#unit-tests) and [integration](#integration-tests) tests. Integration tests require a physical WSPR-beacon device connected via USB! Wi-Fi connection and GPS antenna must be disconnected during [integration](#integration-tests) tests execution.

To measure test coverage, install development dependencies and execute:
```powershell
pip install -r requirements-dev.txt
python -m pytest --cov=beaconapp --cov-config=pytest.ini
```

The coverage report excludes test files, `__init__.py`, and the `main.py` file (_application entry point_) to focus on actual business logic coverage.

### Hardware self-check
After flashing the firmware to the device, it is recommended to run a hardware self-check to ensure that all components are functioning correctly and that the device is ready for operation.

To perform the hardware self-check:

1. Navigate to the **Self-check** section in the application.
2. Click the **Run checks** button.

If the test completes with the status **Passed!**, the device is fully operational and ready to use.