"""
High-fidelity CAN-bus (SAE J1939) & Modbus TCP Hardware Emulator for 16-Cell Series Battery Pack.
"""

import time
import math
import random
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

from .protocols import (
    BatteryChemistry,
    ContactorState,
    BalancingState,
    CellTelemetry,
    CANFrame,
    ModbusRegisterBlock,
    PackTelemetryFrame,
)


class CANBusEmulator:
    """
    Emulates an automotive/grid grade Battery Management System (BMS) MCU
    streaming J1939 CAN-bus packets and Modbus TCP registers for a 16-cell series string.
    """

    def __init__(self, pack_id: str = "BESS-GRID-PACK-01", chemistry: BatteryChemistry = BatteryChemistry.NMC_811):
        self.pack_id = pack_id
        self.chemistry = chemistry
        self.nominal_capacity_ah = 100.0
        self.contactor_state = ContactorState.CLOSED
        self.balancing_state = BalancingState.IDLE
        self.balancing_cells: set[int] = set()

        # Cell baseline states
        self.cell_socs: List[float] = [88.5 + random.uniform(-1.0, 1.0) for _ in range(16)]
        self.cell_temps: List[float] = [28.0 + random.uniform(-0.5, 0.5) for _ in range(16)]
        self.cell_resistances: List[float] = [1.2 + random.uniform(-0.05, 0.05) for _ in range(16)]  # mOhm
        self.pack_soh: float = 94.2  # Overall Pack SOH %

        # Simulation parameters
        self.current_a: float = 25.0  # +25A discharge
        self.ambient_temp_c: float = 25.0
        self.sequence_counter: int = 1000
        self.time_elapsed: float = 0.0

        # Fault Injection Flags
        self.fault_thermal_runaway_cell: Optional[int] = None
        self.fault_thermal_growth_rate: float = 0.0
        self.fault_imbalance_cell: Optional[int] = None
        self.fault_sensor_noise_active: bool = False

    def set_current(self, current_a: float):
        """Set pack load current (positive = discharge, negative = charge)."""
        self.current_a = current_a

    def inject_thermal_runaway(self, cell_id: int = 7, growth_rate_c_per_sec: float = 4.5):
        """Inject dangerous thermal runaway on a target cell."""
        if 1 <= cell_id <= 16:
            self.fault_thermal_runaway_cell = cell_id
            self.fault_thermal_growth_rate = growth_rate_c_per_sec

    def clear_thermal_fault(self):
        """Clear thermal fault injection."""
        self.fault_thermal_runaway_cell = None
        self.fault_thermal_growth_rate = 0.0
        # restore temps gradually
        for i in range(16):
            self.cell_temps[i] = 28.0 + random.uniform(-0.5, 0.5)

    def inject_cell_imbalance(self, cell_id: int = 4, soc_drop_pct: float = 22.0):
        """Inject severe state-of-charge imbalance."""
        if 1 <= cell_id <= 16:
            self.fault_imbalance_cell = cell_id
            self.cell_socs[cell_id - 1] = max(5.0, self.cell_socs[cell_id - 1] - soc_drop_pct)

    def set_sensor_noise(self, enabled: bool):
        """Toggle sensor noise/jitter."""
        self.fault_sensor_noise_active = enabled

    def set_contactor(self, state: ContactorState):
        """Control main high-voltage contactor state."""
        self.contactor_state = state

    def set_balancing(self, state: BalancingState, cells: List[int]):
        """Trigger active or passive cell balancing."""
        self.balancing_state = state
        self.balancing_cells = set(cells)

    def _soc_to_ocv(self, soc_pct: float) -> float:
        """Non-linear Open Circuit Voltage (OCV) model for NMC/LFP."""
        soc = max(0.0, min(100.0, soc_pct)) / 100.0
        if self.chemistry in (BatteryChemistry.NMC_811, BatteryChemistry.NCA):
            # Typical NMC OCV curve (3.0V to 4.2V)
            ocv = 3.20 + 0.95 * soc - 0.15 * math.exp(-35.0 * soc) + 0.18 * math.log(soc + 0.005) + 0.05 * math.pow(soc, 4)
            return max(2.8, min(4.25, ocv))
        elif self.chemistry == BatteryChemistry.LFP:
            # Typical flat LFP curve (3.0V to 3.45V)
            ocv = 3.05 + 0.35 * soc + 0.08 / (1.0 + math.exp(-50.0 * (soc - 0.1))) - 0.08 / (1.0 + math.exp(-50.0 * (soc - 0.9)))
            return max(2.5, min(3.65, ocv))
        else:
            # Solid State (3.0V to 4.4V)
            return 3.2 + 1.15 * soc

    def step(self, dt: float = 0.5) -> PackTelemetryFrame:
        """
        Advance the physics state by dt seconds and generate CAN/Modbus frames.
        """
        self.time_elapsed += dt
        self.sequence_counter += 1

        effective_current = self.current_a if self.contactor_state == ContactorState.CLOSED else 0.0

        # Update cell SoC (Coulomb Counting with efficiency)
        coulomb_eff = 0.995 if effective_current < 0 else 1.0
        ah_delta = (effective_current * (dt / 3600.0)) / (self.nominal_capacity_ah * (self.pack_soh / 100.0)) * 100.0 * coulomb_eff

        cells_data: List[CellTelemetry] = []
        cell_voltages: List[float] = []

        for i in range(16):
            cell_id = i + 1
            # Update SoC
            self.cell_socs[i] = max(0.0, min(100.0, self.cell_socs[i] - ah_delta))

            # Balancing bleed
            if cell_id in self.balancing_cells and self.balancing_state != BalancingState.IDLE:
                self.cell_socs[i] = max(0.0, self.cell_socs[i] - 0.05 * dt)

            # Thermal runaway fault injection
            if self.fault_thermal_runaway_cell == cell_id:
                self.cell_temps[i] += self.fault_thermal_growth_rate * dt
                # Micro-short lowers voltage
                ocv_offset = -0.18 * (self.cell_temps[i] / 40.0)
            else:
                # Normal Joule heating: P = I^2 * R
                p_heat = math.pow(effective_current, 2) * (self.cell_resistances[i] * 1e-3)
                # Newton's law of cooling towards ambient
                cooling = 0.08 * (self.cell_temps[i] - self.ambient_temp_c)
                self.cell_temps[i] += (p_heat * 0.04 - cooling) * dt
                ocv_offset = 0.0

            # Compute terminal voltage: V_term = OCV - I * R_int
            ocv = self._soc_to_ocv(self.cell_socs[i]) + ocv_offset
            v_term = ocv - (effective_current * (self.cell_resistances[i] * 1e-3))

            # Noise / Jitter
            if self.fault_sensor_noise_active:
                v_term += random.gauss(0, 0.015)
                temp_noisy = self.cell_temps[i] + random.gauss(0, 0.4)
            else:
                v_term += random.gauss(0, 0.001)
                temp_noisy = self.cell_temps[i]

            v_term = max(1.8, min(4.5, round(v_term, 4)))
            temp_noisy = round(temp_noisy, 2)
            cell_voltages.append(v_term)

            cells_data.append(CellTelemetry(
                cell_id=cell_id,
                voltage_v=v_term,
                temperature_c=temp_noisy,
                soc_pct=round(self.cell_socs[i], 2),
                internal_resistance_mohm=round(self.cell_resistances[i], 3),
                is_balancing=(cell_id in self.balancing_cells)
            ))

        pack_v = round(sum(cell_voltages), 2)
        pack_power_kw = round((pack_v * effective_current) / 1000.0, 3)
        pack_soc = round(sum(self.cell_socs) / 16.0, 2)
        max_v = max(cell_voltages)
        min_v = min(cell_voltages)
        delta_mv = round((max_v - min_v) * 1000.0, 1)
        max_t = max(self.cell_temps)
        min_t = min(self.cell_temps)

        # Generate J1939 CAN Frames
        now_ms = int(time.time() * 1000)
        can_frames = self._generate_j1939_frames(
            now_ms=now_ms,
            pack_v=pack_v,
            pack_i=effective_current,
            pack_soc=pack_soc,
            cell_voltages=cell_voltages,
            cell_temps=self.cell_temps
        )

        iso_now = datetime.now(timezone.utc).isoformat()

        return PackTelemetryFrame(
            timestamp=time.time(),
            iso_timestamp=iso_now,
            pack_id=self.pack_id,
            chemistry=self.chemistry,
            nominal_capacity_ah=self.nominal_capacity_ah,
            pack_voltage_v=pack_v,
            pack_current_a=round(effective_current, 2),
            pack_power_kw=pack_power_kw,
            pack_soc_pct=pack_soc,
            pack_soh_pct=self.pack_soh,
            max_cell_voltage_v=max_v,
            min_cell_voltage_v=min_v,
            cell_voltage_delta_mv=delta_mv,
            max_cell_temp_c=round(max_t, 2),
            min_cell_temp_c=round(min_t, 2),
            ambient_temp_c=round(self.ambient_temp_c, 2),
            contactor_status=self.contactor_state,
            balancing_status=self.balancing_state,
            cells=cells_data,
            can_frames=can_frames,
            is_late_telemetry=False,
            sequence_id=self.sequence_counter
        )

    def _generate_j1939_frames(
        self,
        now_ms: int,
        pack_v: float,
        pack_i: float,
        pack_soc: float,
        cell_voltages: List[float],
        cell_temps: List[float]
    ) -> List[CANFrame]:
        """Encode physical metrics into standard 8-byte CAN J1939 frames."""
        frames = []

        # 1. PGN 0x18F00100 - Pack Summary
        # Bytes 0-1: Pack V in 0.1V, Bytes 2-3: Pack I in 0.1A (offset 32000), Byte 4: SOC %, Byte 5: SOH %, Byte 6: Contactor, Byte 7: Seq
        v_scaled = min(65535, max(0, int(pack_v * 10)))
        i_scaled = min(65535, max(0, int((pack_i + 3200.0) * 10)))
        soc_b = int(pack_soc) & 0xFF
        soh_b = int(self.pack_soh) & 0xFF
        contactor_b = 1 if self.contactor_state == ContactorState.CLOSED else (2 if self.contactor_state == ContactorState.FAULT_TRIPPED else 0)
        seq_b = self.sequence_counter & 0xFF

        payload1 = [
            (v_scaled >> 8) & 0xFF, v_scaled & 0xFF,
            (i_scaled >> 8) & 0xFF, i_scaled & 0xFF,
            soc_b, soh_b, contactor_b, seq_b
        ]
        frames.append(CANFrame(
            timestamp_ms=now_ms,
            arbitration_id=0x18F00100,
            pgn=0xF001,
            dlc=8,
            data_hex="".join(f"{b:02X}" for b in payload1),
            payload_bytes=payload1,
            description="BMS_PGN_PACK_SUMMARY (V, I, SoC, SoH, Contactor)"
        ))

        # 2. PGNs for Cell Voltages: 4 cells per frame (2 bytes per cell, 1mV resolution)
        for chunk_idx in range(4):
            start_cell = chunk_idx * 4
            pgn_id = 0x18F00200 + (chunk_idx * 0x100)
            chunk_v = cell_voltages[start_cell:start_cell + 4]
            payload_v = []
            for v in chunk_v:
                mv = min(65535, max(0, int(v * 1000)))
                payload_v.extend([(mv >> 8) & 0xFF, mv & 0xFF])

            frames.append(CANFrame(
                timestamp_ms=now_ms,
                arbitration_id=pgn_id,
                pgn=0xF002 + chunk_idx,
                dlc=8,
                data_hex="".join(f"{b:02X}" for b in payload_v),
                payload_bytes=payload_v,
                description=f"BMS_PGN_CELL_VOLTAGES_{start_cell+1}_{start_cell+4}"
            ))

        # 3. PGN 0x18F00600 - Cell Thermistors 1-8 (1 byte per cell, offset +40C)
        payload_t1 = [min(255, max(0, int(t + 40))) for t in cell_temps[0:8]]
        frames.append(CANFrame(
            timestamp_ms=now_ms,
            arbitration_id=0x18F00600,
            pgn=0xF006,
            dlc=8,
            data_hex="".join(f"{b:02X}" for b in payload_t1),
            payload_bytes=payload_t1,
            description="BMS_PGN_CELL_TEMPS_1_8"
        ))

        return frames

    def generate_modbus_registers(self, frame: PackTelemetryFrame) -> ModbusRegisterBlock:
        """Create 16-bit Modbus TCP register map (40001 - 40025)."""
        regs = [
            int(frame.pack_voltage_v * 10),                     # 40001: Pack Voltage (0.1V)
            int((frame.pack_current_a + 3200.0) * 10),          # 40002: Pack Current (0.1A, offset 32000)
            int(frame.pack_soc_pct * 10),                       # 40003: SOC (0.1%)
            int(frame.pack_soh_pct * 10),                       # 40004: SOH (0.1%)
            int(frame.max_cell_temp_c * 10),                    # 40005: Max Temp (0.1C)
            int(frame.min_cell_temp_c * 10),                    # 40006: Min Temp (0.1C)
            int(frame.cell_voltage_delta_mv),                   # 40007: Delta mV
            1 if frame.contactor_status == ContactorState.CLOSED else 0, # 40008: Contactor
            1 if frame.balancing_status != BalancingState.IDLE else 0,   # 40009: Balancing
            frame.sequence_id & 0xFFFF                          # 40010: Seq ID
        ]
        # Append cell voltages (16 cells)
        for cell in frame.cells:
            regs.append(int(cell.voltage_v * 1000))

        return ModbusRegisterBlock(
            transaction_id=frame.sequence_id,
            registers=regs
        )

    def create_delayed_telemetry(self, lag_cycles: int = 15) -> PackTelemetryFrame:
        """Simulate an out-of-order / late telemetry frame from lag_cycles ago."""
        old_frame = self.step(dt=0.1)
        old_time = time.time() - (lag_cycles * 86400.0 * 2.0)  # Simulate days ago
        old_frame.timestamp = old_time
        old_frame.iso_timestamp = datetime.fromtimestamp(old_time, tz=timezone.utc).isoformat()
        old_frame.is_late_telemetry = True
        old_frame.sequence_id = max(1, self.sequence_counter - lag_cycles * 50)
        # Slightly degraded historical capacity
        old_frame.pack_soh_pct = min(100.0, self.pack_soh + (lag_cycles * 0.15))
        return old_frame
