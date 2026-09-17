import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .cycle import CycleInputs, CycleResult, simulate_cycle
from .state import Phase, ThermodynamicState


STATE_LOCATIONS = (
    "Evaporator outlet",
    "Compressor outlet",
    "Condenser outlet",
    "Expansion valve outlet",
)


def package_version() -> str:
    """Return the installed package version, with a source-tree fallback."""
    try:
        return version("hvac-cycle-simulator")
    except PackageNotFoundError:
        return "0.1.0"


def create_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="hvac-cycle",
        description=(
            "Simulate an idealized steady-state vapor-compression HVAC cycle. "
            "Evaporating and condensing temperatures are saturation temperatures."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {package_version()}")
    parser.add_argument("--fluid", default="R134a", help="CoolProp refrigerant name")
    parser.add_argument(
        "--evap-temp", type=float, default=5.0, metavar="DEG_C",
        help="evaporating saturation temperature",
    )
    parser.add_argument(
        "--cond-temp", type=float, default=40.0, metavar="DEG_C",
        help="condensing saturation temperature",
    )
    parser.add_argument(
        "--superheat", type=float, default=5.0, metavar="K",
        help="compressor-inlet superheat",
    )
    parser.add_argument(
        "--subcooling", type=float, default=5.0, metavar="K",
        help="condenser-outlet subcooling",
    )
    parser.add_argument(
        "--efficiency", type=float, default=0.75, metavar="FRACTION",
        help="compressor isentropic efficiency in the range (0, 1]",
    )
    parser.add_argument(
        "--mass-flow", type=float, default=0.05, metavar="KG_S",
        help="refrigerant mass flow",
    )
    parser.add_argument(
        "--output", choices=("full", "summary", "json"), default="full",
        help="output detail and format",
    )
    return parser


def inputs_from_args(args: argparse.Namespace) -> CycleInputs:
    """Translate parsed CLI arguments into domain inputs."""
    return CycleInputs(
        fluid=args.fluid,
        evaporating_temperature_c=args.evap_temp,
        condensing_temperature_c=args.cond_temp,
        superheat_k=args.superheat,
        subcooling_k=args.subcooling,
        compressor_isentropic_efficiency=args.efficiency,
        mass_flow_kg_s=args.mass_flow,
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


def result_as_dict(inputs: CycleInputs, result: CycleResult) -> dict[str, Any]:
    """Build a stable, JSON-serializable representation of a simulation."""
    states = []
    for number, (location, state) in enumerate(
        zip(STATE_LOCATIONS, result.states, strict=True), start=1
    ):
        states.append(
            {
                "number": number,
                "location": location,
                "pressure_pa": state.pressure_pa,
                "temperature_k": state.temperature_k,
                "enthalpy_j_kg": state.enthalpy_j_kg,
                "entropy_j_kg_k": state.entropy_j_kg_k,
                "phase": state.phase.value,
                "quality": state.quality,
            }
        )

    return {
        "inputs": asdict(inputs),
        "states": states,
        "performance": {
            "cooling_capacity_w": result.cooling_capacity_w,
            "compressor_power_w": result.compressor_power_w,
            "condenser_capacity_w": result.condenser_capacity_w,
            "cooling_cop": result.cooling_cop,
            "heating_cop": result.heating_cop,
            "pressure_ratio": result.pressure_ratio,
            "energy_balance_error_w": result.energy_balance_error_w,
        },
    }


def print_full_report(inputs: CycleInputs, result: CycleResult) -> None:
    """Print the complete educational report."""
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


def run(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        inputs = inputs_from_args(args)
        result = simulate_cycle(inputs)
    except ValueError as exc:
        parser.error(f"simulation failed: {exc}")

    if args.output == "json":
        print(json.dumps(result_as_dict(inputs, result), indent=2))
    elif args.output == "summary":
        print(format_performance_summary(result))
    else:
        print_full_report(inputs, result)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
