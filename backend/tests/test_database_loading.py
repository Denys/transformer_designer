"""
Integration tests for Database Loading and Ecosystem Expansion
"""

import pytest
from backend.routers.transformer import load_cores
from backend.calculations.winding import WIRES_DB

def test_load_all_core_files():
    """Test that all new core files are loaded correctly."""
    cores = load_cores()

    # Check if all categories exist
    assert "ferrite_cores" in cores
    assert "silicon_steel_cores" in cores
    assert "powder_cores" in cores
    assert "nanocrystalline_cores" in cores

    # Check counts (basic sanity check)
    # Original cores.json had 27 ferrites + 10 silicon steel (approx)
    # New files added more.
    assert len(cores["ferrite_cores"]) > 25
    assert len(cores["silicon_steel_cores"]) > 0
    assert len(cores["powder_cores"]) > 0
    assert len(cores["nanocrystalline_cores"]) > 0

    # Check for specific new cores
    # Magnetics Inc (Powder)
    magnetics_cores = [c for c in cores["powder_cores"] if c["manufacturer"] == "Magnetics Inc"]
    assert len(magnetics_cores) > 0
    assert any(c["part_number"] == "77083A7" for c in magnetics_cores)

    # Ferroxcube (Ferrite)
    ferroxcube_cores = [c for c in cores["ferrite_cores"] if c["manufacturer"] == "Ferroxcube"]
    assert len(ferroxcube_cores) > 0
    assert any(c["part_number"] == "E100/60/28" for c in ferroxcube_cores)

    # Micrometals (Powder)
    micrometals_cores = [c for c in cores["powder_cores"] if c["manufacturer"] == "Micrometals"]
    assert len(micrometals_cores) > 0
    assert any(c["part_number"] == "T106-26" for c in micrometals_cores)

    # Nanocrystalline
    nano_cores = cores["nanocrystalline_cores"]
    assert any(c["material"] == "Vitroperm 500F" for c in nano_cores)

def test_wires_db_loading():
    """Test that wires database is loaded."""
    assert WIRES_DB is not None
    assert "litz_wires" in WIRES_DB
    assert len(WIRES_DB["litz_wires"]) > 0

    # Check specific wire
    wire = next((w for w in WIRES_DB["litz_wires"] if w["equivalent_awg"] == 20 and w["strand_awg"] == 38), None)
    assert wire is not None
    assert wire["strand_count"] == 60
