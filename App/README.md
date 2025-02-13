# BeaconApp
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
```powershell
python -m beaconapp.main
```