import pytest

from hvac_cycle import CycleInputs, simulate_cycle
from hvac_cycle.state import Phase


def test_default_cycle_is_physically_consistent() -> None:
    result = simulate_cycle(CycleInputs())

    assert result.cooling_capacity_w > 0
    assert result.compressor_power_w > 0
    assert result.cooling_cop > 1
    assert result.condenser_capacity_w == pytest.approx(
        result.cooling_capacity_w + result.compressor_power_w
    )
    assert result.evaporator_outlet.phase is Phase.SUPERHEATED_VAPOR
    assert result.condenser_outlet.phase is Phase.SUBCOOLED_LIQUID
    assert result.expansion_valve_outlet.phase is Phase.TWO_PHASE


def test_expansion_valve_is_isenthalpic() -> None:
    result = simulate_cycle(CycleInputs())
    assert result.expansion_valve_outlet.enthalpy_j_kg == pytest.approx(
        result.condenser_outlet.enthalpy_j_kg
    )


def test_component_pressures_form_two_isobars() -> None:
    result = simulate_cycle(CycleInputs())

    assert result.evaporator_outlet.pressure_pa == pytest.approx(
        result.expansion_valve_outlet.pressure_pa
    )
    assert result.compressor_outlet.pressure_pa == pytest.approx(
        result.condenser_outlet.pressure_pa
    )
    assert result.compressor_outlet.pressure_pa > result.evaporator_outlet.pressure_pa


def test_compressor_increases_enthalpy_and_temperature() -> None:
    result = simulate_cycle(CycleInputs())

    assert (
        result.compressor_outlet.enthalpy_j_kg
        > result.evaporator_outlet.enthalpy_j_kg
    )
    assert result.compressor_outlet.temperature_k > result.evaporator_outlet.temperature_k


def test_mass_flow_scales_capacities_but_not_cop_or_states() -> None:
    base = simulate_cycle(CycleInputs(mass_flow_kg_s=0.05))
    doubled = simulate_cycle(CycleInputs(mass_flow_kg_s=0.10))

    assert doubled.cooling_capacity_w == pytest.approx(2 * base.cooling_capacity_w)
    assert doubled.compressor_power_w == pytest.approx(2 * base.compressor_power_w)
    assert doubled.condenser_capacity_w == pytest.approx(2 * base.condenser_capacity_w)
    assert doubled.cooling_cop == pytest.approx(base.cooling_cop)
    assert doubled.evaporator_outlet == base.evaporator_outlet
    assert doubled.compressor_outlet == base.compressor_outlet


def test_lower_compressor_efficiency_requires_more_power() -> None:
    efficient = simulate_cycle(CycleInputs(compressor_isentropic_efficiency=0.9))
    inefficient = simulate_cycle(CycleInputs(compressor_isentropic_efficiency=0.6))

    assert inefficient.compressor_power_w > efficient.compressor_power_w
    assert inefficient.compressor_outlet.temperature_k > efficient.compressor_outlet.temperature_k
    assert inefficient.cooling_capacity_w == pytest.approx(efficient.cooling_capacity_w)
    assert inefficient.cooling_cop < efficient.cooling_cop


def test_more_subcooling_increases_refrigeration_effect() -> None:
    no_subcooling = simulate_cycle(CycleInputs(subcooling_k=0))
    subcooled = simulate_cycle(CycleInputs(subcooling_k=10))

    assert subcooled.condenser_outlet.enthalpy_j_kg < no_subcooling.condenser_outlet.enthalpy_j_kg
    assert subcooled.cooling_capacity_w > no_subcooling.cooling_capacity_w
    assert subcooled.compressor_power_w == pytest.approx(no_subcooling.compressor_power_w)
    assert subcooled.cooling_cop > no_subcooling.cooling_cop


def test_zero_superheat_and_subcooling_use_saturation_boundaries() -> None:
    result = simulate_cycle(CycleInputs(superheat_k=0, subcooling_k=0))

    assert result.evaporator_outlet.phase is Phase.TWO_PHASE
    assert result.evaporator_outlet.quality == pytest.approx(1.0)
    assert result.condenser_outlet.phase is Phase.TWO_PHASE
    assert result.condenser_outlet.quality == pytest.approx(0.0)
    assert result.cooling_capacity_w > 0


def test_default_case_stays_within_a_sensible_regression_range() -> None:
    result = simulate_cycle(CycleInputs())

    assert result.cooling_capacity_w == pytest.approx(7_850, rel=0.02)
    assert result.compressor_power_w == pytest.approx(1_520, rel=0.02)
    assert result.cooling_cop == pytest.approx(5.17, rel=0.02)


@pytest.mark.parametrize(
    "inputs",
    [
        CycleInputs(evaporating_temperature_c=45, condensing_temperature_c=40),
        CycleInputs(compressor_isentropic_efficiency=0),
        CycleInputs(compressor_isentropic_efficiency=1.01),
        CycleInputs(mass_flow_kg_s=0),
        CycleInputs(mass_flow_kg_s=-0.01),
        CycleInputs(superheat_k=-1),
        CycleInputs(subcooling_k=-1),
    ],
)
def test_invalid_inputs_are_rejected(inputs: CycleInputs) -> None:
    with pytest.raises(ValueError):
        simulate_cycle(inputs)
