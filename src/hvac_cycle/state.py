from dataclasses import dataclass
from enum import Enum

from CoolProp.CoolProp import PropsSI


class Phase(str, Enum):
    SUBCOOLED_LIQUID = "subcooled liquid"
    TWO_PHASE = "two-phase"
    SUPERHEATED_VAPOR = "superheated vapor"


@dataclass(frozen=True)
class ThermodynamicState:
    pressure_pa: float
    temperature_k: float
    enthalpy_j_kg: float
    entropy_j_kg_k: float
    phase: Phase
    quality: float | None = None


def state_from_ph(pressure_pa: float, enthalpy_j_kg: float, fluid: str) -> ThermodynamicState:
    """Return a refrigerant state from pressure and specific enthalpy."""
    if pressure_pa <= 0:
        raise ValueError("Pressure must be greater than zero")

    h_liquid = PropsSI("H", "P", pressure_pa, "Q", 0, fluid)
    h_vapor = PropsSI("H", "P", pressure_pa, "Q", 1, fluid)
    temperature_k = PropsSI("T", "P", pressure_pa, "H", enthalpy_j_kg, fluid)
    entropy = PropsSI("S", "P", pressure_pa, "H", enthalpy_j_kg, fluid)

    tolerance_j_kg = 1.0
    if enthalpy_j_kg < h_liquid - tolerance_j_kg:
        phase = Phase.SUBCOOLED_LIQUID
        quality = None
    elif enthalpy_j_kg > h_vapor + tolerance_j_kg:
        phase = Phase.SUPERHEATED_VAPOR
        quality = None
    else:
        phase = Phase.TWO_PHASE
        quality = max(0.0, min(1.0, (enthalpy_j_kg - h_liquid) / (h_vapor - h_liquid)))

    return ThermodynamicState(
        pressure_pa=pressure_pa,
        temperature_k=temperature_k,
        enthalpy_j_kg=enthalpy_j_kg,
        entropy_j_kg_k=entropy,
        phase=phase,
        quality=quality,
    )
