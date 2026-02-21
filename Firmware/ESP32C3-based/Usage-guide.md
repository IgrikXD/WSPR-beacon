# Usage guide
Interaction with the device is performed using the [BEACON.App] user application. The application is used to configure the parameters of the active transmission mode, view confirmed spots on the WSPRnet network, run hardware self-checks, and change the device’s global settings.

The [BEACON.App] application structure:
- [Transmission tab](#transmission-tab)
    - [Transmission mode block](#transmission-mode-block)
    - [Transmission details block](#transmission-details-block)
- [Spots database tab](#spots-database-tab)
    - [Active mode spots block](#active-mode-spots-block)
- [Self-check tab](#self-check-tab)
    - [Hardware test block](#hardware-test-block)
    - [Device info block](#device-info-block)
- [Settings tab](#settings-tab)
    - [Device calibration block](#device-calibration-block)
        - [Automatic calibration (via GPS)](#automatic-calibration-via-gps)
        - [Manual calibration (by frequency measurement)](#manual-calibration-by-frequency-measurement)
    - [Device connection settings block](#device-connection-settings-block)
    - [App settings block](#app-settings-block)

## Transmission tab
Used to configure and control the active transmission mode and display the device operating status.

### Transmission mode block
Allows you to select the active transmission mode (_currently only WSPR is available_) and configure its parameters:
- TX call (_your amateur radio callsign_)
- QTH locator (_calculated automatically by GPS, but available for modification_)
- Output power, dBm
- Transmission interval, minutes
- Transmission band, meters

> [!NOTE]
> You can change the active mode parameters without resetting it. If the application detects parameter changes, the **Activated!** button state changes to **Set as active mode**, allowing you to apply the updated parameters. If the device is transmitting when you set a new mode, the changes will be applied after the transmission completes.

The **Set as active mode** button activates the configured transmission mode. After successful activation, the button changes state to **Activated!**.

> [!NOTE]
> When an active transmission mode is set, any actions in the **Self-check** and **Settings** tabs are blocked until the active transmission mode is reset!

### Transmission details block
The **Active mode details** field displays brief information about the currently set transmission mode in the following format:
```
<MODE>: <TX call> <QTH locator> <Output power, dBm>
```
The **Reset mode** button resets the active transmission mode.

> [!NOTE]
> After pressing **Reset mode**, the active transmission mode will be reset only after the current transmission completes. Resetting the active transmission mode is required for any actions in the **Self-check** and **Settings** tabs!

The **TX status** field displays the current event related to the active transmission mode:
- "_- Waiting for valid GPS data... -_" - Waiting for valid GPS data to synchronize the QTH locator and transmission time
- "_- Waiting for next transmission window... -_" - Waiting for the next available timeslot to start message transmission
- "_- Error processing TX mode! -_" - Error processing the active transmission mode
- "_- Transmission finished! -_" - Message transmission completed successfully
- "_- No active TX mode set! -_" - No active transmission mode is set

To the right of the **TX status** field, the current device status indicators are shown:
- **CAL** - SI5351 is calibrated
- **GPS** - GPS data is valid
- **TX** - Message transmission is active

> [!NOTE]
> There is no need to configure the active transmission mode parameters every time the device is powered on. The last configured mode is stored in NVS and is automatically loaded when the device reboots.

## Spots database tab
Used to view the list of confirmed spots on the WSPRnet network for the currently set active transmission mode.

> [!NOTE]
> Available only when an active transmission mode is set!

### Active mode spots block
The **Extract the latest** field allows you to choose how many of the most recently reported spots to display in the table (_10, 30, 50_).

The **Sort by** field allows you to select the spot sorting method (_Time, SNR, Drift, Distance_).

The **Extract** button downloads spots for the currently set active transmission mode using the [WSPR.live API](https://wspr.live/). During execution, the button state changes to **Extraction...**. After completion, the downloaded spots are displayed in the table.

Results:
- **Extracted!** - The spot list was successfully downloaded and displayed in the table
- **Failed!** - The spot list download failed

After 2 seconds, the button returns to the **Extract** state, allowing you to retry downloading spots.

## Self-check tab
Used to diagnose the device hardware and update the firmware.

> [!NOTE]
> Available only when no active transmission mode is set!

### Hardware test block
The **Self-check** field displays the logs during hardware self-check execution.

> [!IMPORTANT]
> The hardware self-check must be run with the GPS antenna connected. The test fails if the current GPS data is invalid!

The **Run checks** button starts the hardware test and, during execution, changes its state to **Running...**.

During the test, the following checks are performed:
- SI5351 initialization check
- GPS module initialization check
- Verification of correct GPS data synchronization (_coordinates, date, time_)

Results:
- **Passed!** - The test completed successfully
- **Failed!** - The test failed. The last error message is saved in the **Self-check** field

After 2 seconds, the button returns to the **Run checks** state, allowing you to run the test again.

### Device info block
The **Hardware info** field shows the device hardware revision. This value does not depend on firmware, is stored in the device’s eFuse, and cannot be changed.

The **Firmware info** field shows the current firmware version.

The **Update** button checks for device firmware updates. During the check, the button state changes to **Checking...**. If an update is available, the button state changes to **Updating...** and automatic firmware download and update is started.

Results:
- **Latest!** - The latest available firmware version is already installed
- **Updated!** - Firmware update completed successfully
- **Failed!** - An error occurred during the update check or during the firmware update process

After 2 seconds, the button returns to the **Update** state, allowing you to check for firmware updates again.

## Settings tab
Used to change the global settings of the device and UI parameters of the [BEACON.App].

> [!NOTE]
> Available only when no active transmission mode is set!

### Device calibration block
The **Calibration value** field is used to display or adjust the current calibration value of the internal SI5351 IC (_in ppb_).

#### Automatic calibration (via GPS)
> [!NOTE]
> Automatic calibration is not available when the GPS signal (_1PPS_) is missing. While automatic calibration is in progress, access to controls in the **Transmission**, **Spots database**, **Self-check**, and **Settings** tabs is blocked!
>
> The calibration process takes about **90 seconds** and uses the ESP32-C3 RMT peripheral to count pulses generated by the SI5351 IC, using the GPS 1PPS signal as a timing reference.

The **Auto by GPS** button starts automatic SI5351 calibration using the 1PPS signal from the built-in GPS module and, during execution, changes its state to **Calibration...**.

Results:
- **Calibrated!** - Calibration completed successfully. A new calibration value (_in ppb_) is set in the **Calibration value** field
- **Failed!** - Calibration failed

After 2 seconds, the button returns to the **Auto by GPS** state, allowing you to retry calibration.

#### Manual calibration (by frequency measurement)
> [!NOTE]
> While manual calibration is in progress, access to controls in the **Transmission**, **Spots database**, **Self-check**, and **Settings** tabs is blocked!

The **Calibration frequency, MHz** field is used to manually calibrate the SI5351 by setting the generated frequency at the TX OUT output (_in MHz_).

The **Generate** button starts generating a carrier signal at the specified frequency on the TX OUT output and changes its state to **Terminate** (_pressing it again stops generation_).

Manual calibration procedure:
- Start carrier generation using the **Generate** button
- Measure the frequency at the TX OUT output using a frequency analyzer
- Reach the required reference frequency by changing the **Calibration value** field and using the **+** and **-** buttons to fine-tune the calibration value in 1 ppb steps
- Press the **Terminate** button to stop carrier generation

### Device connection settings block
The **SSID** field is used to specify the name of the Wi-Fi network that the device will connect to for use with [BEACON.App].

The **Password** field is used to specify the password of the Wi-Fi network the device will connect to.

The **Auto-connect to Wi-Fi on startup** option enables/disables automatic connection to the specified Wi-Fi network when the device boots.

The **Connect** button initiates a connection to the specified Wi-Fi network and changes its state to **Connecting...** while the operation is in progress.
> [!IMPORTANT]
> The PC running [BEACON.App] and the device must be on the same local network! Otherwise, the application will not be able to discover the device.

Results:
- **Disconnect** - Connection established (_press again to disconnect the Wi-Fi connection_)
- **Failed!** - Connection failed

In case of **Failed!**, after 2 seconds the button returns to the **Connect** state, allowing you to retry the connection.

### App settings block
The **UI theme** option sets the [BEACON.App] user interface theme (_Dark, Light_). The value is automatically saved to the app configuration file and loaded on the next launch.

The **UI scaling** option sets the [BEACON.App] user interface scaling (_80%, 90%, 100%, 110%, 120%_). The value is automatically saved to the app configuration file and loaded on the next launch.

[BEACON.App]: ../../App/README.md
