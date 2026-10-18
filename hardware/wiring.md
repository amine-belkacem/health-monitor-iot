# Hardware

The original EasyEDA / Cirkit Designer project files from the thesis were not
kept. The files in this folder were **redrawn after the thesis** from the pin
table (table 3.3 of the report). The board layout is a simplified 2-layer
version, not a copy of the original PCB shown in the report.

| File | Content |
|------|---------|
| `schematic.svg` / `schematic.png` | Redrawn schematic |
| `preview_pcb.png` | Render of the Gerber files |
| `gerber/*.zip` | Gerber RS-274X + Excellon drill (120 × 75 mm, 2 layers) |
| `easyeda/*.json` | EasyEDA-style source files, written by script (not exported by EasyEDA) |
| `pinout.csv`, `netlist.csv`, `bom.csv` | Pin map, nets, bill of materials |
| `tools/` | Python scripts that regenerate everything above |

Regenerate and check:

```bash
cd hardware/tools
python generate_hardware.py     # Gerbers, PCB json, CSV files
python render_gerber.py         # preview_pcb.png
python check_routing.py         # shorts: trace touching a foreign pad, crossings
python check_connectivity.py    # opens: every net connects all its pads
```

## ESP32 (DevKit V1, WROOM-32) pin map

| Sensor   | Sensor pin | Function                          | ESP32 pin |
|----------|------------|-----------------------------------|-----------|
| AD8232   | OUTPUT     | ECG analog signal                 | GPIO 34 (ADC1) |
| AD8232   | LO+        | Lead-off detection, + electrode   | GPIO 32   |
| AD8232   | LO-        | Lead-off detection, - electrode   | GPIO 33   |
| AD8232   | 3.3V / GND | Power                             | 3.3V / GND |
| DHT22    | DATA       | Digital data                      | GPIO 27   |
| DHT22    | VCC / GND  | Power                             | 3.3V / GND |
| MAX30102 | SDA        | I2C data                          | GPIO 21   |
| MAX30102 | SCL        | I2C clock                         | GPIO 22   |
| MAX30102 | VIN / GND  | Power                             | 3.3V / GND |
| MQ-135   | AOUT       | Analog output                     | GPIO 35 (ADC1) |
| MQ-135   | VCC / GND  | Power                             | 5V (VIN) / GND |

GPIO 34 and 35 are input-only pins on ADC1, which keeps working while Wi-Fi is
on (ADC2 does not).

## Known issues

- **First version of the redrawn PCB had 4 open nets.** LO+, LO-, SDA and SCL
  had no trace at all. `check_routing.py` only looks for shorts, so it passed.
  I added `check_connectivity.py`, routed the missing nets (LO- on the bottom
  layer because it crosses LO+) and now all 9 signal nets are connected.
- **MQ-135 output level.** The heater needs 5 V, so the board feeds the module
  from VIN. With a 5 V supply, AOUT can go above 3.3 V and GPIO 35 has no
  divider in front of it. Before building this board, add a divider
  (for example 10 kΩ / 20 kΩ) on MQ_AOUT. In the thesis prototype the module was
  powered from 3.3 V, which is safe for the ESP32 but runs the heater cold.
- **DHT22 pull-up.** The board relies on the 4.7 kΩ pull-up already present on
  most DHT22 breakout modules. A bare DHT22 sensor needs one added.
- **No DRC.** The layout was never run through a design rule check. Treat it as
  a reference for the connections, not as a board ready for fabrication.
- **Electrical safety.** Electrodes are connected to a person. The prototype
  must run from a battery or a laptop on battery, never from a mains-powered
  supply without isolation. It is not a medical device.
