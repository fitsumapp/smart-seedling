# ESP8266 Integration & Hardware Wiring Guide (NodeMCU / D1 Mini)

## Hardware Specifications & Components

* **Microcontroller**: ESP8266 (NodeMCU v2/v3 / Amica / CP2102 or Wemos D1 Mini)
* **Soil Temperature Sensor**: DS18B20 1-Wire Digital Soil/Water Temperature Sensor (Waterproof probe)
* **Soil Moisture Sensor**: Capacitive Soil Moisture Sensor v1.2 / v2.0 (Analog output)
* **Ambient Air Sensor**: DHT22 (AM2302) Temperature & Relative Humidity Sensor
* **Actuator Relays (Dual Channel or 2x Single Relay)**:
  * **Relay #1**: 5V Relay for Submersible DC Mini Water Pump
  * **Relay #2**: 5V Relay for Greenhouse Ventilation / Cooling Fan
* **Resistor**: 4.7kΩ Resistor (Pull-Up for DS18B20 data line to 3.3V)

---

## Pin Mapping Table

| Component & Pin | ESP8266 Pin (NodeMCU) | ESP8266 GPIO | Description / Notes |
| :--- | :--- | :--- | :--- |
| **Capacitive Moisture AOUT** | **A0** | **ADC0** | ESP8266 Single Analog Input (10-bit, 0–1023) |
| **DS18B20 DATA (Yellow/White)** | **D2** | **GPIO 4** | 1-Wire Data line (**Requires 4.7kΩ pull-up to 3.3V**) |
| **Relay #1 IN (Water Pump)** | **D1** | **GPIO 5** | Digital Output (Controls Irrigation Pump) |
| **DHT22 DATA (Air Temp/Hum)** | **D5** | **GPIO 14** | High-speed digital input for ambient climate |
| **Relay #2 IN (Ventilation Fan)** | **D6** | **GPIO 12** | Digital Output (Controls Cooling / Exhaust Fan) |
| **Sensor Power (VCC)** | **3V3 / 3.3V** | 3.3V Rail | For DS18B20 VCC, Moisture Sensor VCC, DHT22 VCC |
| **Relay Power (VCC)** | **VIN / 5V** | 5V Rail | From USB/5V supply to power relay coils |
| **Ground (GND)** | **GND** | GND | **Common Ground** shared across all components |

---

## Circuit / Wiring Diagram (ASCII)

```
                       +-----------------------------------+
                       |      ESP8266 NodeMCU (V2/V3)      |
                       |                                   |
                       | [A0]                        [3V3] |---+----> 3.3V (Moisture, DS18B20 & DHT22 VCC)
                       | [GND]                       [GND] |---|----> Common GND
                       | [VU/VIN]                    [D1]  |---|----> Relay #1 IN (Pump) [GPIO 5]
                       |                             [D2]  |---|----> DS18B20 DATA [GPIO 4]
                       |                             [D5]  |---|----> DHT22 DATA [GPIO 14]
                       |                             [D6]  |---|----> Relay #2 IN (Fan) [GPIO 12]
                       +-----------------------------------+   |
                                                               |
1. Capacitive Soil Moisture Sensor v1.2 / v2.0                 |
   +------------+                                              |
   |        VCC |----------------------------------------------+ (3.3V)
   |        GND |----------------------------------------------+ (GND)
   |       AOUT |--------------------> [A0] on ESP8266
   +------------+

2. DS18B20 Soil Temperature Sensor (Waterproof Probe)
   +------------+
   |  RED (VCC) |----------------------------------------------+ (3.3V)
   | BLK  (GND) |----------------------------------------------+ (GND)
   | YEL (DATA) |---------+----------> [D2] (GPIO 4) on ESP8266
   +------------+         |
                         [4.7kΩ Resistor]
                          |
                          +------------------------------------+ (3.3V)

3. DHT22 Ambient Air Temperature & Relative Humidity Sensor
   +------------+
   |  PIN 1 VCC |----------------------------------------------+ (3.3V or 5V)
   |  PIN 2 DATA|--------------------> [D5] (GPIO 14) on ESP8266
   |  PIN 4 GND |----------------------------------------------+ (GND)
   +------------+

4. 5V Dual Relay Module (Controls Pump & Fan)
   +------------+
   |        VCC |--------------------> [VIN / VU / 5V] on NodeMCU
   |        GND |--------------------> [GND]
   |        IN1 |--------------------> [D1] (GPIO 5) -> Submersible Pump
   |        IN2 |--------------------> [D6] (GPIO 12)-> Ventilation / Cooling Fan
   +------------+
```

---

## Autonomous Local Edge Logic

* **Irrigation Pump Control**:
  * If $\text{Soil Moisture} \le 30.0\%$ $\rightarrow$ Pump **ON**.
  * If $\text{Soil Moisture} \ge 50.0\%$ or runtime $> 30\text{s}$ $\rightarrow$ Pump **OFF**.
* **Ventilation Fan Control**:
  * If $\text{Air Temperature} \ge 30.0^\circ\text{C}$ OR $\text{Air Humidity} \ge 85.0\%$ $\rightarrow$ Fan **ON** (Exhaust heat & excess moisture).
  * If $\text{Air Temperature} \le 25.0^\circ\text{C}$ AND $\text{Air Humidity} < 80.0\%$ $\rightarrow$ Fan **OFF** (Optimum microclimate restored).
