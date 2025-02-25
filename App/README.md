# BEACON.App
A Windows GUI application for configuring and managing a [WSPR beacon](https://github.com/IgrikXD/WSPR-beacon?tab=readme-ov-file#wspr-beacon) based on an ESP32 SoC ([_PCB version 3.1_](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-pcb-3.1)). The application communicates with the device via USB or Wi-Fi to configure transmission parameters, perform hardware self-checks, and manage device setup (_including calibration and Wi-Fi configuration_).

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

### Build the executable file
```powershell
pip install pyinstaller==6.11.1
pyinstaller --noconsole --onefile `
    --icon=beaconapp/ui/resources/beacon-app-logo.ico `
    --add-data "beaconapp/ui/resources/*;ui/resources" `
    --exclude-module beaconapp.tests `
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

Unit tests are available to verify the application's core functionality, and they verify:
- Correct formation of commands sent to the device
- Proper decoding of messages received from the device
- Correct processing of data retrieved from the [**WSPR.live API**](https://wspr.live/)
- Automatic selection of the appropriate communication transport (_USB or Wi-Fi_)
- Proper registration of message handlers for incoming device messages
- Validation of user-configured parameters
- Correct operation of data wrappers used for data exchange during device communication

To run the unit tests, install `pytest` and execute:
```powershell
pip install pytest==8.3.4
pytest
```

### Hardware self-check
After flashing the firmware onto the device, it is recommended to run the hardware self-check to ensure that all components are functioning correctly (_LEDs, SI5351, GPS, Wi-Fi_) and the device is ready for operation.

To perform the hardware self-check:

1. Navigate to the "_Self-check_" section in the application.
2. Click the "_Run checks_" button.

If the test completes with the status "**PASS!**", the device is fully operational and ready to use.