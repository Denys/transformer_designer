"""
PSFB Transformer Calculations

Implements:
- Leakage inductance calculation for shell-type transformers
- Design targeting specific leakage inductance (for ZVS)
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Constants
MU_0 = 4 * math.pi * 1e-7

@dataclass
class LeakageInductanceResult:
    Llk_primary_H: float
    Llk_secondary_H: float
    Llk_total_referred_primary_H: float
    notes: List[str]


def calculate_leakage_inductance_shell(
    N_primary: int,
    N_secondary: int,
    MLT_m: float,
    winding_width_m: float,
    primary_height_m: float,
    secondary_height_m: float,
    insulation_thickness_m: float,
    interleaving_level: int = 1, # 1 = P-S, 2 = P-S-P, etc.
) -> LeakageInductanceResult:
    """
    Calculate leakage inductance for shell-type transformer (concentric windings).

    Based on Dowell's equations/standard leakage formula:
    Llk = (mu0 * N^2 * MLT * K) / (3 * w)
    Where K is geometry factor involving heights and spacing.

    For simple P-S:
    Llk = (mu0 * N^2 * MLT / w) * (hp/3 + hs/3 + d)

    With interleaving, leakage reduces by 1/M^2 where M is number of interfaces?
    Or more accurately, M sections reduces Llk by 1/M^2.

    Args:
        N_primary: Primary turns
        N_secondary: Secondary turns
        MLT_m: Mean Length Turn [m]
        winding_width_m: Winding width (window height in EI, or breadth) [m]
        primary_height_m: Radial build of primary [m]
        secondary_height_m: Radial build of secondary [m]
        insulation_thickness_m: Spacing between P and S [m]
        interleaving_level: Number of P-S interfaces (1=Simple, 2=Sandwich P-S-P, etc)

    Returns:
        LeakageInductanceResult
    """

    # Geometry factor
    # Effective height term: (hp + hs)/3 + d
    # For interleaved, it's roughly divided by M^2

    # Let's assume interleaving_level = number of interfaces.
    # P-S: 1 interface. Factor = 1.
    # P-S-P: 2 interfaces. Primary split in 2. Each section has Np/2.
    # Leakage of one P/2-S section is calculated, then summed?
    # Standard approximation: Llk ~ 1/P^2 where P is number of primitive sections.

    # We'll use a simplified factor M = interleaving_level
    # Llk_total = Llk_base / M^2

    # Base calculation (referred to primary)
    # Note: winding_width_m is the length of the coil along the axis (b in many formulas)
    # For EI core, this is usually the window height.

    if winding_width_m <= 0:
        return LeakageInductanceResult(0,0,0, ["Invalid winding width"])

    geom_term = (primary_height_m / 3) + (secondary_height_m / 3) + insulation_thickness_m

    Llk_base = (MU_0 * (N_primary ** 2) * MLT_m * geom_term) / winding_width_m

    # Apply interleaving reduction
    # If interleaved P-S-P (primary split), Llk reduces significantly.
    # P-S-P is often considered M=2 (2 interfaces) -> 1/4 leakage?
    # Yes, roughly.

    Llk_total = Llk_base / (interleaving_level ** 2)

    return LeakageInductanceResult(
        Llk_primary_H = Llk_total / 2, # Rough split
        Llk_secondary_H = Llk_total / 2 * (N_secondary/N_primary)**2,
        Llk_total_referred_primary_H = Llk_total,
        notes=[f"Interleaving level: {interleaving_level} (reduction factor {1/interleaving_level**2:.2f})"]
    )


def design_for_target_leakage(
    target_Llk_H: float,
    N_primary: int,
    MLT_m: float,
    winding_width_m: float,
    primary_height_m: float,
    secondary_height_m: float,
    min_insulation_m: float = 0.0001,
    max_insulation_m: float = 0.01,
) -> float:
    """
    Calculate required insulation spacing (shim gap) to achieve target leakage.

    Llk = (mu0 * N^2 * MLT / w) * (hp/3 + hs/3 + d)
    Solve for d (insulation_thickness).

    d = (Llk * w) / (mu0 * N^2 * MLT) - (hp/3 + hs/3)

    Args:
        target_Llk_H: Desired leakage inductance [H]
        N_primary: Primary turns
        MLT_m: Mean Length Turn [m]
        winding_width_m: Winding width [m]
        primary_height_m: Radial build P [m]
        secondary_height_m: Radial build S [m]

    Returns:
        Required insulation thickness [m].
        Returns -1.0 if target is impossible (too low).
        Returns max_insulation_m if target is too high.
    """
    term1 = (target_Llk_H * winding_width_m) / (MU_0 * (N_primary ** 2) * MLT_m)
    term2 = (primary_height_m / 3) + (secondary_height_m / 3)

    required_d = term1 - term2

    if required_d < min_insulation_m:
        # Cannot achieve target, leakage from windings alone is higher
        return -1.0

    if required_d > max_insulation_m:
        return max_insulation_m

    return required_d
