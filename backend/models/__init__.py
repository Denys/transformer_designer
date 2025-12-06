"""Pydantic models for transformer and inductor design"""

from .transformer import (
    TransformerType,
    WaveformType,
    TransformerRequirements,
    CoreSelection,
    WindingDesign,
    LossAnalysis,
    ThermalAnalysis,
    VerificationStatus,
    TransformerDesignResult,
    DesignSuggestion,
    CoreAlternative,
    NoMatchResult,
)
from .inductor import (
    InductorRequirements,
    InductorDesignResult,
)

__all__ = [
    "TransformerType",
    "WaveformType",
    "TransformerRequirements",
    "CoreSelection",
    "WindingDesign",
    "LossAnalysis",
    "ThermalAnalysis",
    "VerificationStatus",
    "TransformerDesignResult",
    "DesignSuggestion",
    "CoreAlternative",
    "NoMatchResult",
    "InductorRequirements",
    "InductorDesignResult",
]
