"""
Unit tests for CAN-bus J1939 & Modbus TCP protocols and frame packing.
"""

import pytest
from voltpulse.hardware.can_bus_emulator import CANBusEmulator
from voltpulse.hardware.protocols import BatteryChemistry, ContactorState, BalancingState


def test_can_bus_emulator_initialization():
    emulator = CANBusEmulator(pack_id="TEST-PACK-16S", chemistry=BatteryChemistry.NMC_811)
    assert emulator.pack_id == "TEST-PACK-16S"
    assert emulator.contactor_state == ContactorState.CLOSED
    assert len(emulator.cell_socs) == 16


def test_can_frame_generation_j1939():
    emulator = CANBusEmulator()
    frame = emulator.step(dt=0.5)

    assert frame.pack_voltage_v > 45.0
    assert len(frame.cells) == 16
    assert len(frame.can_frames) >= 6  # Summary, 4 cell voltage chunks, 1 temp frame

    # Check PGN Summary
    summary_frame = frame.can_frames[0]
    assert summary_frame.arbitration_id == 0x18F00100
    assert summary_frame.dlc == 8
    assert len(summary_frame.payload_bytes) == 8


def test_modbus_register_packing():
    emulator = CANBusEmulator()
    frame = emulator.step(dt=0.5)
    modbus = emulator.generate_modbus_registers(frame)

    assert modbus.transaction_id > 0
    assert len(modbus.registers) >= 25
    # Register 40001 is Pack Voltage * 10
    assert modbus.registers[0] == int(frame.pack_voltage_v * 10)


def test_contactor_and_balancing_state_transitions():
    emulator = CANBusEmulator()
    emulator.set_contactor(ContactorState.FAULT_TRIPPED)
    assert emulator.contactor_state == ContactorState.FAULT_TRIPPED

    emulator.set_balancing(BalancingState.ACTIVE_BLEEDING, [3, 7])
    frame = emulator.step(dt=0.5)
    assert frame.cells[2].is_balancing is True
    assert frame.cells[6].is_balancing is True
    assert frame.cells[0].is_balancing is False
