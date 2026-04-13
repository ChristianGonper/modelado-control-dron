# LiteWing ESP32 Drone - Wiki Page
[Source](https://circuitdigest.com/wiki/litewing/)


**LiteWing** is a **compact, WiFi-controlled drone based on the ESP32-S3 microcontroller.** Designed for hobbyists, makers, and engineers, LiteWing offers a simple yet powerful platform for drone experimentation and development. It is an **open-hardware** project, making it **easy to modify and expand.**

Whether you’re new to drones or an experienced developer looking to create custom flight applications, LiteWing provides an **accessible and affordable** way to explore drone technology. Unlike traditional drones that require proprietary controllers, LiteWing connects to your smartphone, allowing for an intuitive flying experience without additional hardware.

The firmware on LiteWing supports Crazyflie cfclient and cflib, meaning you can program and control your drone using Python and add more features like height hold, position hold, gesture control, and more.

LiteWing Version 3.0

The latest version includes more **GPIO pins, sensor mounts, LED indicators** to make it easier to tinker with and program. The PCB frame design keeps it lightweight while reducing costs, making it one of the most affordable DIY drones available.

**Open Hardware**

Fully open-source design with schematics, Gerber & Firmware available for download & modification

**Mobile App**

Dedicated mobile app for Android and iPhone. No need for an external controller or Joystick

**Crazyflie**

Comes with modified Crazyflie firmware with support for CFclient and add-on sensor integration

**PC Control**

Compatible with custom Python SDK (CFlib), allowing you to control the drone with Python scripts

**Betaflight**

Supports Betaflight, an open-source flight control software for FPV enthusiasts

**Arduino**

The on-board ESP32-S3 microcontroller can also be programmed using Arduino IDE

---

## Specifications

| Category | Parameter | Specification / Details |
| :--- | :--- | :--- |
| Core System | Microcontroller | ESP32-S3, Dual-core Xtensa LX7, 240 MHz, 512 KB SRAM |
| Core System | IMU Sensor | MPU6050 – 3-Axis Gyroscope + 3-Axis Accelerometer |
| Core System | Communication | Wi-Fi 2.4 GHz (CRTP over UDP protocol) |
| Core System | Programming Interface | USB Type-C with CH340 USB-to-UART bridge |
| Motor & Propulsion | Motor Type | 720 Coreless DC Motors |
| Motor & Propulsion | Propeller Size | 55 mm or 65 mm |
| Motor & Propulsion | Motor Control | MOSFET-based PWM speed control |
| Power System | Battery | 3.7 V 1S Li-Po battery, 20C or higher |
| Power System | Charging Circuit | TP4056 Li-ion charging IC (1 A max) |
| Power System | Voltage Regulator | SPX3819, 500 mA low-noise LDO |
| Physical Specifications | Frame Material | Custom FR4 PCB frame |
| Physical Specifications | Dimensions | 100 mm × 100 mm |
| Physical Specifications | Weight | ~45 g (without battery) |
| Physical Specifications | Payload Capacity | ~25 g (with 55 mm propellers) |
| Optional Sensors | VL53L1X ToF Sensor | Height-hold capability |
| Optional Sensors | MS5611 Barometric Sensor | Altitude-hold capability |
| Optional Sensors | PMW3901 Optical Flow Sensor | Position-hold capability |
| Control Options | Mobile Control | Android & iOS app (Wi-Fi based) |
| Control Options | PC Control | CFClient support and custom Python SDK |


---

## Quick Start Tutorials

### Basic Tutorials

### Intermediate Tutorials

### Advanced Tutorials

### Tutorials using LiteWing Drone Positioning Module

## Hardware Overview

**ESP32-S3 Microcontroller**

The LiteWing drone is powered by the **ESP32-S3**, a highly efficient microcontroller that offers low power consumption and an increased number of GPIO pins for enhanced expandability. It is powered by a **dual-core Xtensa LX7 core,** capable of running at 240 MHz, accompanied by 512 KB of internal SRAM and integrated 2.4 GHz, 802.11 b/g/n Wi-Fi and Bluetooth 5 (LE) connectivity.

Its improved computational efficiency ensures better flight stabilisation and allows seamless future firmware upgrades. The built-in USB interface simplifies programming, debugging, and firmware updates.

**MPU6050 IMU Sensor**

For precise flight stability, the LiteWing features an **MPU6050 IMU**, which provides accurate motion tracking and stabilisation.

**Programming Interface**

The LiteWing can be easily programmed through the **onboard USB Type-C** connector without the need for any external programmers or debuggers, thanks to the onboard USB-UART bridge controller and auto-reset circuitry.

Designed for minimalist efficiency, the LiteWing drone incorporates an **all-in-one PCB** frame, eliminating the need for additional structural components. The frame includes hook & loop battery strap slots for easy mounting and removal of the battery.

**Motor Drivers**

The LiteWing employs **PWM-based motor control,** ensuring smooth acceleration and manoeuvrability with precision. The motor driver circuit is built around an N-channel MOSFET along with a flyback diode and a pull-down resistor.


## Firmware and Programming

The LiteWing drone firmware is built using ESP-IDF, the official development framework by Espressif for ESP32-series microcontrollers. ESP-IDF provides a set of libraries, drivers, and tools essential for embedded development. Ensure your device is ready for firmware flashing. To flash the latest firmware to your LiteWing drone, you can use the web tool provided here. Click on start flashing and select the correct firmware version for your hardware and confirm that your LiteWing Drone is properly connected via USB and follow the on screen instructions.


### Download Firmware

The default LiteWing firmware that comes pre-installed in the drone can be found on our GitHub repo. To know more about check out the tutorial: [flash firmware on your litewing drone](https://circuitdigest.com/articles/flashing-litewing-firmware).

**Firmware Overview**

| **Framework Feature** | **Description** |
| --- | --- |
| WiFi & Bluetooth | Built-in support for wireless communication |
| FreeRTOS | Seamless multitasking capabilities |
| Debugging Tools | Performance monitoring and power management |

The LiteWing firmware is based on **[ESP-Drone](https://github.com/espressif/esp-drone)**, an open-source flight control firmware specifically designed for ESP32-powered drones. ESP-Drone integrates flight control algorithms from the Crazyflie open-source project.

**Firmware Components**

| **Component** | **Function** |
| --- | --- |
| Flight Control Core | Sensor data processing, stabilization, motor control, PID adjustments |
| Hardware Drivers | Communication with peripherals (I2C, SPI, UART) |
| Communication Modules | Telemetry, remote control, data logging via WiFi |
| Software Libraries | Signal filtering, sensor fusion, real-time data processing |

### Programming Options

| **Platform** | **Method** | **Documentation** |
| --- | --- | --- |
| **Python SDK** | Crazyflie cflib library | [Python Programming Guide](https://circuitdigest.com/microcontroller-projects/how-to-program-litewing-drone-using-python-with-crazyflie-cflib-python-sdk) |
| **CFClient** | Desktop application for control and monitoring | [cfClient Installation Guide](https://circuitdigest.com/articles/how-to-use-cfclient-with-litewing) |
| **Arduino** | ESP32-S3 Arduino programming | Coming soon |

**CrazyFlie and Python Tutorials**

LiteWing comes preloaded with firmware based on **ESP-Drone** and **Crazyflie,** making it compatible with cfclient and the cflib Python library. You can control it using an Xbox or PS4/PS5 controller and monitor flight data in real time.  

| **Tutorial** | **Description** | **Link** |
| --- | --- | --- |
| Gesture Control | Control LiteWing using hand gestures | [View Tutorial](https://circuitdigest.com/microcontroller-projects/diy-gesture-controlled-drone-using-esp32-and-python-with-litewing) |
| Python SDK Basics | Getting started with cflib | [Python Programming Guide](https://circuitdigest.com/microcontroller-projects/how-to-program-litewing-drone-using-python-with-crazyflie-cflib-python-sdk) |