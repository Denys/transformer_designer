"""
Pydantic models for waveform definitions.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WaveformType(str, Enum):
    """Input waveform type"""
    SINUSOIDAL = "sinusoidal"  # Kf = 4.44
    SQUARE = "square"          # Kf = 4.0
    TRIANGULAR = "triangular"  # Kf = 4.0
    PULSE = "pulse"            # Use volt-seconds method
    CAPACITOR_DISCHARGE = "capacitor_discharge"
    CUSTOM = "custom"


class PulseWaveform(BaseModel):
    """Define pulse characteristics for transformer design"""
    waveform_type: WaveformType = Field(..., description="Type of waveform")
    peak_voltage: float = Field(..., gt=0, description="Peak voltage [V]")
    pulse_width: float = Field(..., gt=0, description="Pulse width [s]")
    rise_time: float = Field(..., ge=0, description="Rise time 10-90% [s]")
    fall_time: float = Field(..., ge=0, description="Fall time [s]")
    repetition_rate: float = Field(..., gt=0, description="Repetition rate [Hz]")

    # For capacitor discharge
    source_capacitance: Optional[float] = Field(None, gt=0, description="Source capacitance [F]")
    circuit_resistance: Optional[float] = Field(None, gt=0, description="Circuit resistance [Ω]")
    circuit_inductance: Optional[float] = Field(None, ge=0, description="Circuit inductance [H]")
