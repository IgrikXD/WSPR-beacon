# BeaconApp
A Windows GUI application for working with a [WSPR beacon](https://github.com/IgrikXD/WSPR-beacon?tab=readme-ov-file#wspr-beacon) based on an ESP32 MCU. 
It uses communication with the device via a serial port to configure transmission parameters, hardware self-check, and set up the device (_calibration, Wi-Fi connection_).
![BeaconApp](../Resources/BeaconApp-Transmission-frame.png)

## Building
Download and install the [latest version of Python for Windows](https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe).

### Clone repository
```powershell
git clone https://github.com/IgrikXD/WSPR-beacon.git
cd WSPR-beacon/App
```

There are two possible ways to use the application: [creating a monolithic executable file](#building-the-executable-file) (_recommended_) and [running the application from the source code](#launching-the-application-without-building-the-executable-file) without prior build.

### Building the executable file
```powershell
pip install --upgrade pip
pip install pyinstaller==6.11.1
pyinstaller --noconsole --onefile `
    --icon=beaconapp/ui/resources/beacon-app-logo.ico `
    --add-data "beaconapp/ui/resources/*;ui/resources" `
    --name BeaconApp beaconapp/main.py
```

### Launching the application without building the executable file
```powershell
python -m beaconapp.main
```