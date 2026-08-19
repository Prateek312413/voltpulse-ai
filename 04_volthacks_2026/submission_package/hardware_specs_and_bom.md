# VoltPulse AI: Hardware Specification, Schematics & Bill of Materials (BOM)

This document specifies the embedded electronic architecture, microcontroller pinouts, sensor interfaces, and physical Bill of Materials (BOM) for the **VoltPulse AI** 16-Cell Series Battery Management System.

---

## 1. System Hardware Block Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                   VOLTPULSE AI HARDWARE ARCHITECTURE                              |
|                                                                                                   |
|  [16-Cell Series Lithium Pack: 48V-67.2V Nominal]                                                 |
|       │                                                                                           |
|       ├──> [Analog Front End (AFE): Texas Instruments BQ76952]                                    |
|       │         • 16-Channel Differential Cell Voltage ADCs (16-bit, 1mV accuracy)                |
|       │         • 8x NTC 10k Thermistor Inputs (Cell Surface Temperatures)                        |
|       │         • Low-side Shunt Resistor (Isense: Current Measurement, 50uOhm)                   |
|       │         • Internal Passive Bleed MOSFETs (50-100mA Cell Balancing)                        |
|       │         │ (SPI / I2C Bus @ 400 kHz)                                                       |
|       │         ▼                                                                                 |
|       └──> [Main MCU: STM32F407VGT6 / ESP32-S3 Dual-Core Xtensa LX7 @ 240MHz]                    |
|                 • Executes Real-time Edge Filter & Sub-Millisecond dT/dt & dV/dt Surveillance     |
|                 • Formats SAE J1939 CAN-bus 29-bit Extended Identifier Frames                     |
|                 • Implements Modbus TCP / MQTT Bridge                                             |
|                 │                                                                                 |
|                 ├──> [CAN Transceiver: SN65HVD230 / MCP2515] ───> [ISO 11898-2 CAN-bus Line]      |
|                 ├──> [Solid-State High-Voltage Contactor Relay] ──> [High-Voltage Disconnect]     |
|                 └──> [Ethernet / Wi-Fi Edge Gateway] ───────────> [FastAPI SCADA Dashboard]       |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Bill of Materials (BOM)

| Item # | Component Category | Manufacturer / Part Number | Description / Specifications | Unit Cost (USD) | Qty |
|:---:|---|---|---|:---:|:---:|
| **1** | Analog Front End (AFE) | Texas Instruments `BQ76952` | 16-Series Cell Battery Monitor, 16-bit ADC, Integrated Passive Balancing | $5.40 | 1 |
| **2** | Main Microcontroller (MCU) | STMicroelectronics `STM32F407VGT6` (or ESP32-S3) | ARM Cortex-M4 @ 168MHz / ESP32-S3 240MHz with FPU, 1MB Flash | $6.20 | 1 |
| **3** | CAN-bus Transceiver | Texas Instruments `SN65HVD230` | 3.3V CAN Transceiver (ISO 11898-2 compliant, up to 1 Mbps) | $1.15 | 1 |
| **4** | Current Shunt Resistor | Vishay `WSLP2726L5000FEA` | 0.5 mΩ Surface Mount Current Sense Resistor, 5W, 1% Tolerance | $2.30 | 1 |
| **5** | Temperature Sensors | Vishay / Epcos `B57861S0103F040` | NTC 10k Thermistors, 1% accuracy, -40°C to +125°C | $0.45 | 8 |
| **6** | Contactor Relay Driver | Infineon `BTS50015-1TMA` | Smart High-Side High-Voltage Power Switch with Current Sense & Thermal Shutdown | $3.80 | 1 |
| **7** | Isolated DC-DC Converter | RECOM `R1SX-3.305` | 1kVDC Galvanic Isolation 5V to 3.3V DC/DC for CAN interface | $2.90 | 1 |
| **8** | Passive Balancing MOSFETs | Diodes Inc. `DMN2075U-7` | N-Channel 20V SOT-23 MOSFETs for Cell Bleed Network | $0.18 | 16 |
| **9** | Custom 4-Layer PCB | FR4 TG150 ENIG | Custom 100mm x 80mm BMS Controller Board | $4.50 | 1 |
| **Total** | — | — | **Complete Industrial Edge BMS Unit** | **~$35.00** | — |

---

## 3. Microcontroller Pinout Mapping (STM32 / ESP32)

| Pin Identifier | Functional Role | Connected Component | Protocol / Signal Type |
|:---:|---|---|---|
| `PA9` / `GPIO17` | `CAN_TX` | SN65HVD230 Transceiver `D` pin | Digital Output (CAN TX) |
| `PA10` / `GPIO18`| `CAN_RX` | SN65HVD230 Transceiver `R` pin | Digital Input (CAN RX) |
| `PB6` / `GPIO21` | `I2C_SCL` | BQ76952 `SCL` pin | I2C Clock (400 kHz) |
| `PB7` / `GPIO22` | `I2C_SDA` | BQ76952 `SDA` pin | I2C Bidirectional Data |
| `PC13` / `GPIO4` | `ALERT_INT`| BQ76952 `ALERT` pin | Hardware Interrupt (Over-voltage/Under-voltage) |
| `PB0` / `GPIO25` | `CONTACTOR_EN`| High-Side Driver Gate | Digital Output (Active High Contactor Enable) |
| `PB1` / `GPIO26` | `BUZZER_PWM` | Piezo Alarm Buzzer | PWM Audible Warning Signal |

---

## 4. SAE J1939 CAN-bus Frame Protocol Dictionary

| Arbitration ID (29-bit Hex) | PGN | Name | Payload Content | Update Rate |
|:---:|:---:|---|---|:---:|
| `0x18F00100` | `0xF001` | `BMS_PACK_SUMMARY` | Bytes 0-1: Pack V (0.1V), Bytes 2-3: Current (0.1A), Byte 4: SoC %, Byte 5: SoH %, Byte 6: Contactor, Byte 7: Seq | 10 Hz |
| `0x18F00200` | `0xF002` | `BMS_CELL_V_1_4` | 2 bytes per cell: Cell 1 to 4 Terminal Voltages (1 mV resolution) | 10 Hz |
| `0x18F00300` | `0xF003` | `BMS_CELL_V_5_8` | 2 bytes per cell: Cell 5 to 8 Terminal Voltages (1 mV resolution) | 10 Hz |
| `0x18F00400` | `0xF004` | `BMS_CELL_V_9_12` | 2 bytes per cell: Cell 9 to 12 Terminal Voltages (1 mV resolution) | 10 Hz |
| `0x18F00500` | `0xF005` | `BMS_CELL_V_13_16` | 2 bytes per cell: Cell 13 to 16 Terminal Voltages (1 mV resolution) | 10 Hz |
| `0x18F00600` | `0xF006` | `BMS_CELL_TEMPS_1_8` | 1 byte per thermistor: Temp in °C (offset +40°C) | 5 Hz |
| `0x18F00700` | `0xF007` | `BMS_SAFETY_STATUS` | Contactor State, Balancing Status, Micro-Short Fault Flag, Hardware Error Bits | 10 Hz |
