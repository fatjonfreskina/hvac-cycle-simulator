import pytest
from CoolProp.CoolProp import PropsSI

from hvac_cycle.state import Phase, state_from_ph


FLUID = "R134a"
PRESSURE_PA = 500_000.0


def test_two_phase_state_returns_quality_and_saturation_temperature() -> None:
    h_liquid = PropsSI("H", "P", PRESSURE_PA, "Q", 0, FLUID)
    h_vapor = PropsSI("H", "P", PRESSURE_PA, "Q", 1, FLUID)
    expected_temperature = PropsSI("T", "P", PRESSURE_PA, "Q", 0, FLUID)

    state = state_from_ph(PRESSURE_PA, (h_liquid + h_vapor) / 2, FLUID)

    assert state.phase is Phase.TWO_PHASE
    assert state.quality == pytest.approx(0.5)
    assert state.temperature_k == pytest.approx(expected_temperature)


@pytest.mark.parametrize("quality", [0.0, 0.25, 0.75, 1.0])
def test_quality_is_recovered_from_saturated_enthalpy(quality: float) -> None:
    enthalpy = PropsSI("H", "P", PRESSURE_PA, "Q", quality, FLUID)

    state = state_from_ph(PRESSURE_PA, enthalpy, FLUID)

    assert state.phase is Phase.TWO_PHASE
    assert state.quality == pytest.approx(quality, abs=1e-8)


def test_subcooled_liquid_is_classified_without_quality() -> None:
    saturation_temperature = PropsSI("T", "P", PRESSURE_PA, "Q", 0, FLUID)
    enthalpy = PropsSI("H", "P", PRESSURE_PA, "T", saturation_temperature - 5, FLUID)

    state = state_from_ph(PRESSURE_PA, enthalpy, FLUID)

    assert state.phase is Phase.SUBCOOLED_LIQUID
    assert state.quality is None
    assert state.temperature_k == pytest.approx(saturation_temperature - 5)


def test_superheated_vapor_is_classified_without_quality() -> None:
    saturation_temperature = PropsSI("T", "P", PRESSURE_PA, "Q", 1, FLUID)
    enthalpy = PropsSI("H", "P", PRESSURE_PA, "T", saturation_temperature + 5, FLUID)

    state = state_from_ph(PRESSURE_PA, enthalpy, FLUID)

    assert state.phase is Phase.SUPERHEATED_VAPOR
    assert state.quality is None
    assert state.temperature_k == pytest.approx(saturation_temperature + 5)


def test_state_preserves_defining_properties() -> None:
    enthalpy = PropsSI("H", "P", PRESSURE_PA, "Q", 0.3, FLUID)

    state = state_from_ph(PRESSURE_PA, enthalpy, FLUID)

    assert state.pressure_pa == PRESSURE_PA
    assert state.enthalpy_j_kg == enthalpy
    assert state.entropy_j_kg_k == pytest.approx(
        PropsSI("S", "P", PRESSURE_PA, "H", enthalpy, FLUID)
    )


@pytest.mark.parametrize("pressure_pa", [0.0, -1.0])
def test_non_positive_pressure_is_rejected(pressure_pa: float) -> None:
    with pytest.raises(ValueError, match="Pressure must be greater than zero"):
        state_from_ph(pressure_pa, 200_000, FLUID)
