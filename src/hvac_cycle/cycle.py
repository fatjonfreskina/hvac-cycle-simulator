from dataclasses import dataclass

from CoolProp.CoolProp import PropsSI

from .state import ThermodynamicState, state_from_ph


@dataclass(frozen=True)
class CycleInputs:
    fluid: str = "R134a"
    evaporating_temperature_c: float = 5.0
    condensing_temperature_c: float = 40.0
    superheat_k: float = 5.0
    subcooling_k: float = 5.0
    compressor_isentropic_efficiency: float = 0.75
    mass_flow_kg_s: float = 0.05


@dataclass(frozen=True)
class CycleResult:
    evaporator_outlet: ThermodynamicState
    compressor_outlet: ThermodynamicState
    condenser_outlet: ThermodynamicState
    expansion_valve_outlet: ThermodynamicState
    cooling_capacity_w: float
    compressor_power_w: float
    condenser_capacity_w: float
    cooling_cop: float


def simulate_cycle(inputs: CycleInputs) -> CycleResult:
    """Simulate an idealized steady-state vapor-compression cycle."""
    if inputs.evaporating_temperature_c >= inputs.condensing_temperature_c:
        raise ValueError("Evaporating temperature must be below condensing temperature")
    if not 0 < inputs.compressor_isentropic_efficiency <= 1:
        raise ValueError("Compressor isentropic efficiency must be in (0, 1]")
    if inputs.mass_flow_kg_s <= 0:
        raise ValueError("Mass flow must be greater than zero")
    if inputs.superheat_k < 0 or inputs.subcooling_k < 0:
        raise ValueError("Superheat and subcooling cannot be negative")

    evaporating_k = inputs.evaporating_temperature_c + 273.15
    condensing_k = inputs.condensing_temperature_c + 273.15
    p_low = PropsSI("P", "T", evaporating_k, "Q", 1, inputs.fluid)
    p_high = PropsSI("P", "T", condensing_k, "Q", 0, inputs.fluid)

    t1 = evaporating_k + inputs.superheat_k
    if inputs.superheat_k == 0:
        h1 = PropsSI("H", "P", p_low, "Q", 1, inputs.fluid)
        s1 = PropsSI("S", "P", p_low, "Q", 1, inputs.fluid)
    else:
        h1 = PropsSI("H", "P", p_low, "T", t1, inputs.fluid)
        s1 = PropsSI("S", "P", p_low, "T", t1, inputs.fluid)
    state1 = state_from_ph(p_low, h1, inputs.fluid)

    h2s = PropsSI("H", "P", p_high, "S", s1, inputs.fluid)
    h2 = h1 + (h2s - h1) / inputs.compressor_isentropic_efficiency
    state2 = state_from_ph(p_high, h2, inputs.fluid)

    t3 = condensing_k - inputs.subcooling_k
    if inputs.subcooling_k == 0:
        h3 = PropsSI("H", "P", p_high, "Q", 0, inputs.fluid)
    else:
        h3 = PropsSI("H", "P", p_high, "T", t3, inputs.fluid)
    state3 = state_from_ph(p_high, h3, inputs.fluid)

    h4 = h3
    state4 = state_from_ph(p_low, h4, inputs.fluid)

    specific_cooling = h1 - h4
    specific_work = h2 - h1
    if specific_cooling <= 0 or specific_work <= 0:
        raise ValueError("The selected inputs do not produce a valid cooling cycle")

    cooling_capacity = inputs.mass_flow_kg_s * specific_cooling
    compressor_power = inputs.mass_flow_kg_s * specific_work
    condenser_capacity = inputs.mass_flow_kg_s * (h2 - h3)

    return CycleResult(
        evaporator_outlet=state1,
        compressor_outlet=state2,
        condenser_outlet=state3,
        expansion_valve_outlet=state4,
        cooling_capacity_w=cooling_capacity,
        compressor_power_w=compressor_power,
        condenser_capacity_w=condenser_capacity,
        cooling_cop=cooling_capacity / compressor_power,
    )
