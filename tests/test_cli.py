from hvac_cycle import CycleInputs, simulate_cycle
from hvac_cycle.cli import (
    build_explanations,
    describe_phase,
    format_performance_summary,
    format_state_table,
)


def test_state_table_contains_four_numbered_locations_and_units() -> None:
    table = format_state_table(simulate_cycle(CycleInputs()))

    assert "P [bar]" in table
    assert "T [degC]" in table
    assert "h [kJ/kg]" in table
    assert "1      Evaporator outlet" in table
    assert "2      Compressor outlet" in table
    assert "3      Condenser outlet" in table
    assert "4      Expansion valve outlet" in table


def test_performance_summary_contains_metrics_and_balance() -> None:
    summary = format_performance_summary(simulate_cycle(CycleInputs()))

    assert "Specific cooling effect:" in summary
    assert "Condenser capacity:" in summary
    assert "Cooling COP:" in summary
    assert "Heating COP:" in summary
    assert "Energy balance error:" in summary


def test_explanations_cover_every_component_and_key_assumption() -> None:
    result = simulate_cycle(CycleInputs())
    explanations = build_explanations(result)

    assert len(explanations) == 4
    assert "isentropic" in explanations[0]
    assert "constant high pressure" in explanations[1]
    assert "enthalpy remains constant" in explanations[2]
    assert "constant low pressure" in explanations[3]


def test_phase_description_distinguishes_saturation_boundaries() -> None:
    result = simulate_cycle(CycleInputs(superheat_k=0, subcooling_k=0))

    assert describe_phase(result.evaporator_outlet) == "saturated vapor"
    assert describe_phase(result.condenser_outlet) == "saturated liquid"


def test_phase_description_includes_two_phase_quality() -> None:
    state = simulate_cycle(CycleInputs()).expansion_valve_outlet

    description = describe_phase(state)

    assert description.startswith("two-phase (Q=")
