import pytest

from hvac_cycle import CycleInputs, simulate_cycle
from hvac_cycle.refrigerants import (
    get_refrigerant,
    normalize_refrigerant,
    supported_refrigerant_names,
)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("r134a", "R134a"),
        ("R-134A", "R134a"),
        ("R1234ze", "R1234ze(E)"),
        ("r-1234ZE(e)", "R1234ze(E)"),
        ("R1234YF", "R1234yf"),
        ("r-32", "R32"),
        ("propane", "R290"),
        ("CO2", "R744"),
        ("carbon dioxide", "R744"),
    ],
)
def test_refrigerant_aliases_resolve_to_canonical_names(
    alias: str,
    canonical: str,
) -> None:
    assert normalize_refrigerant(alias) == canonical


def test_unknown_refrigerant_reports_supported_choices() -> None:
    with pytest.raises(ValueError, match="Unsupported refrigerant") as error:
        normalize_refrigerant("R404A")

    for name in supported_refrigerant_names():
        assert name in str(error.value)


def test_r515b_explains_backend_limitation() -> None:
    with pytest.raises(ValueError, match="REFPROP-backed implementation"):
        normalize_refrigerant("R515B")


@pytest.mark.parametrize("fluid", supported_refrigerant_names())
def test_supported_refrigerants_run_the_default_cycle(fluid: str) -> None:
    refrigerant = get_refrigerant(fluid)
    result = simulate_cycle(
        CycleInputs(
            fluid=fluid,
            evaporating_temperature_c=refrigerant.default_evaporating_temperature_c,
            condensing_temperature_c=refrigerant.default_condensing_temperature_c,
            superheat_k=refrigerant.default_superheat_k,
            subcooling_k=refrigerant.default_subcooling_k,
        )
    )
    assert result.cooling_capacity_w > 0
    assert result.cooling_cop > 1
