"""
Waveform models for transformer design
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
    waveform_type: WaveformType
    peak_voltage: float = Field(..., description="Peak voltage [V]")
    pulse_width: float = Field(..., description="Pulse width [seconds]")
    rise_time: float = Field(..., description="Rise time [seconds] (10-90%)")
    fall_time: float = Field(..., description="Fall time [seconds]")
    repetition_rate: float = Field(..., description="Repetition rate [Hz]")

    # For capacitor discharge
    source_capacitance: Optional[float] = Field(None, description="Source capacitance [F]")
    circuit_resistance: Optional[float] = Field(None, description="Circuit resistance [Ω]")
    circuit_inductance: Optional[float] = Field(None, description="Circuit inductance [H]")
