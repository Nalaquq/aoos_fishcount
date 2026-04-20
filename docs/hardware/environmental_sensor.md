# **README — Connecting a BME280 Environmental Sensor to Raspberry Pi 5**

This guide explains how to wire a **BME280 temperature/humidity/pressure sensor** to a **Raspberry Pi 5**, set up a Python environment using **pyenv**, and install the required libraries (`smbus2` and `bme280`).

---

## **1. Hardware Connections (BME280 → Raspberry Pi 5 GPIO)**

The BME280 communicates over **I²C**, so only four wires are required.

Use the Raspberry Pi 5 pinout reference:  
[https://pinout.xyz/pinout/ground](https://pinout.xyz/pinout/ground)

### **BME280 → Raspberry Pi 5 Wiring**

| BME280 Pin | RPi5 GPIO Pin | Notes |
|------------|---------------|-------|
| **VIN / VCC** | **Pin 1 (3.3V)** | Power the sensor at 3.3V (NOT 5V) |
| **GND** | **Pin 6 (Ground)** | Any ground pin works |
| **SCL** | **Pin 5 (GPIO 3 / SCL1)** | I²C clock |
| **SDA** | **Pin 3 (GPIO 2 / SDA1)** | I²C data |

### **Enable I²C on the Pi**
```bash
sudo raspi-config
```
Navigate to:

**Interface Options → I2C → Enable**

Reboot afterward:

```bash
sudo reboot
```

---

## **2. Create and Activate a Python Virtual Environment (pyenv)**

This project uses **pyenv** to manage Python versions and virtual environments.  
Make sure pyenv is installed and initialized in your shell.

### **Install Python (recommended: 3.9.x for Coral TPU compatibility)**
```bash
pyenv install 3.9.18
```

### **Create a virtual environment**
```bash
pyenv virtualenv 3.9.18 bme280-env
```

### **Activate the environment**
```bash
pyenv activate bme280-env
```

> **Note for collaborators:**  
> If you activate environments using `source venv/bin/activate` instead of pyenv, please update this README so the activation instructions stay consistent for everyone.

---

## **3. Install Required Python Packages**

Inside the activated pyenv environment:

```bash
pip install smbus2 bme280
```

These libraries provide:

- **smbus2** → I²C communication  
- **bme280** → High‑level sensor reading functions  

---

## **4. Test the Sensor**

Create a file named `read_bme280.py`:

```python
import smbus2
import bme280

port = 1
address = 0x76  # Some boards use 0x77
bus = smbus2.SMBus(port)

calibration_params = bme280.load_calibration_params(bus, address)
data = bme280.sample(bus, address, calibration_params)

print("Temperature:", data.temperature, "°C")
print("Humidity:", data.humidity, "%")
print("Pressure:", data.pressure, "hPa")
```

Run it:

```bash
python read_bme280.py
```

If everything is wired correctly, you’ll see live temperature, humidity, and pressure readings.

---

## **5. Troubleshooting**

### **Check if the Pi detects the sensor**
```bash
sudo i2cdetect -y 1
```

You should see `76` or `77` appear in the grid.

### **If nothing appears**
- Recheck wiring  
- Ensure I²C is enabled  
- Confirm the sensor is 3.3V compatible  
- Try the alternate address `0x77`  
