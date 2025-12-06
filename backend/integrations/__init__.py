"""
Backend integrations with external databases
"""

from .openmagnetics import OpenMagneticsDB, get_openmagnetics_db

__all__ = [
    "OpenMagneticsDB",
    "get_openmagnetics_db",
]
