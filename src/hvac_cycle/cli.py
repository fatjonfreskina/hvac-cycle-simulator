from collections.abc import Sequence

from .cycle import CycleInputs, CycleResult, simulate_cycle
from .state import Phase, ThermodynamicState


STATE_LOCATIONS = (
    "Evaporator outlet",
    "Compressor outlet",
    "Condenser outlet",
    "Expansion valve outlet",
)


def describe_phase(state: ThermodynamicState) -> str:
    """Return an educational phase label, including quality when relevant."""
    if state.phase is not Phase.TWO_PHASE:
        return state.phase.value
    if state.quality is None:
        return state.phase.value
    if state.quality <= 1e-8:
        return "saturated liquid"
    if state.quality >= 1 - 1e-8:
        return "saturated vapor"
    return f"two-phase (Q={state.quality:.3f})"


def format_state_table(result: CycleResult) -> str:
    """Format canonical cycle states using practical HVAC units."""
    header = (
        f"{'State':<7}{'Location':<27}{'P [bar]':>10}"
        f"{'T [degC]':>12}{'h [kJ/kg]':>13}  Phase"
    )
    separator = "-" * len(header)
    rows = [header, separator]

    for number, (location, state) in enumerate(
        zip(STATE_LOCATIONS, result.states, strict=True), start=1
    ):
        rows.append(
            f"{number:<7}{location:<27}{state.pressure_pa / 100_000:>10.2f}"
            f"{state.temperature_k - 273.15:>12.2f}"
            f"{state.enthalpy_j_kg / 1000:>13.2f}  {describe_phase(state)}"
        )

    return "\n".join(rows)


def format_performance_summary(result: CycleResult) -> str:
    """Format cycle performance and first-law balance."""
    return "\n".join(
        (
            f"Evaporating pressure:       {result.evaporating_pressure_pa / 100_000:.2f} bar(a)",
            f"Condensing pressure:        {result.condensing_pressure_pa / 100_000:.2f} bar(a)",
            f"Pressure ratio:             {result.pressure_ratio:.2f}",
            f"Superheat:                  {result.superheat_k:.2f} K",
            f"Subcooling:                 {result.subcooling_k:.2f} K",
            "",
            f"Specific cooling effect:    {result.specific_cooling_j_kg / 1000:.2f} kJ/kg",
            f"Specific compressor work:   {result.specific_compressor_work_j_kg / 1000:.2f} kJ/kg",
            f"Specific condenser heat:    {result.specific_condenser_heat_j_kg / 1000:.2f} kJ/kg",
            "",
            f"Cooling capacity:           {result.cooling_capacity_w / 1000:.2f} kW",
            f"Compressor power:           {result.compressor_power_w / 1000:.2f} kW",
            f"Condenser capacity:         {result.condenser_capacity_w / 1000:.2f} kW",
            f"Cooling COP:                {result.cooling_cop:.2f}",
            f"Heating COP:                {result.heating_cop:.2f}",
            f"Energy balance error:       {result.energy_balance_error_w:.3e} W",
        )
    )


def build_explanations(result: CycleResult) -> Sequence[str]:
    """Create deterministic explanations of the modeled transformations."""
    valve_quality = result.expansion_valve_outlet.quality
    valve_detail = (
        f" The outlet is {valve_quality * 100:.1f}% vapor by mass."
        if valve_quality is not None
        else ""
    )
    return (
        "1 -> 2, compressor: pressure and enthalpy rise. The ideal reference is "
        "isentropic; the specified efficiency accounts for real irreversibility.",
        "2 -> 3, condenser: the refrigerant rejects heat at constant high pressure, "
        f"condenses, then leaves with {result.subcooling_k:.1f} K of subcooling.",
        "3 -> 4, expansion valve: pressure falls while enthalpy remains constant."
        + valve_detail,
        "4 -> 1, evaporator: the refrigerant absorbs heat at constant low pressure, "
        f"evaporates, then leaves with {result.superheat_k:.1f} K of superheat.",
    )


def main() -> None:
    inputs = CycleInputs()
    result = simulate_cycle(inputs)

    print(f"Educational HVAC cycle - {inputs.fluid}")
    print(
        f"Saturation temperatures: {inputs.evaporating_temperature_c:.1f} degC evaporation, "
        f"{inputs.condensing_temperature_c:.1f} degC condensation"
    )
    print(f"Refrigerant mass flow: {inputs.mass_flow_kg_s:.3f} kg/s")
    print()
    print(format_state_table(result))
    print()
    print("PERFORMANCE")
    print(format_performance_summary(result))
    print()
    print("WHAT HAPPENS IN EACH COMPONENT")
    for explanation in build_explanations(result):
        print(f"- {explanation}")
    print()
    print("MODEL ASSUMPTIONS")
    print("- Steady-state operation and constant refrigerant mass flow.")
    print("- No pressure drops or heat losses in pipes and heat exchangers.")
    print("- Constant compressor isentropic efficiency; no motor losses.")
    print("- The expansion valve is adiabatic and isenthalpic.")


if __name__ == "__main__":
    main()
