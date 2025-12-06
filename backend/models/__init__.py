"""Pydantic models for transformer and inductor design"""

from .transformer import (
    TransformerType,
    WaveformType,
    DesignMethod,
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
    "DesignMethod",
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

