import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable

from .cycle import CycleInputs, CycleResult, simulate_cycle
from .refrigerants import SUPPORTED_REFRIGERANTS, normalize_refrigerant
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


def add_simulation_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the inputs shared by direct simulations."""
    parser.add_argument(
        "--fluid",
        default="R134a",
        help=(
            "supported refrigerant name or alias: "
            + ", ".join(refrigerant.name for refrigerant in SUPPORTED_REFRIGERANTS)
        ),
    )
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


def create_parser() -> argparse.ArgumentParser:
    """Build the command-line parser and its learning-oriented subcommands."""
    parser = argparse.ArgumentParser(
        prog="hvac-cycle",
        description="Explore and learn idealized vapor-compression HVAC cycles.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {package_version()}")
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
        required=True,
    )

    simulate_parser = subparsers.add_parser(
        "simulate",
        help="run a cycle from command-line inputs",
        description=(
            "Simulate an idealized steady-state vapor-compression HVAC cycle. "
            "Evaporating and condensing temperatures are saturation temperatures."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_simulation_arguments(simulate_parser)

    subparsers.add_parser(
        "learn",
        help="build and explore a cycle through an interactive lesson",
        description=(
            "Start an interactive lesson that explains each input, validates the "
            "operating point and walks through the four cycle states."
        ),
    )
    return parser


def inputs_from_args(args: argparse.Namespace) -> CycleInputs:
    """Translate parsed CLI arguments into domain inputs."""
    return CycleInputs(
        fluid=normalize_refrigerant(args.fluid),
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


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def prompt_value(
    prompt: str,
    default: float,
    input_fn: InputFunction,
    output_fn: OutputFunction,
    validator: Callable[[float], bool] | None = None,
    validation_message: str = "Value is outside the allowed range.",
) -> float:
    """Prompt until the learner enters a valid numeric value."""
    while True:
        raw_value = input_fn(f"{prompt} [{default:g}]: ").strip()
        if not raw_value:
            value = default
        else:
            try:
                value = float(raw_value)
            except ValueError:
                output_fn("Please enter a number, or press Enter to keep the default.")
                continue
        if validator is not None and not validator(value):
            output_fn(validation_message)
            continue
        return value


def prompt_refrigerant(
    default: str,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> str:
    """Let the learner select a documented refrigerant by number, name or alias."""
    output_fn("Supported refrigerants:")
    for number, refrigerant in enumerate(SUPPORTED_REFRIGERANTS, start=1):
        output_fn(f"  {number}. {refrigerant.name} - {refrigerant.description}")

    while True:
        answer = input_fn(f"Refrigerant [{default}]: ").strip()
        if not answer:
            return normalize_refrigerant(default)
        if answer.isdigit():
            selection = int(answer)
            if 1 <= selection <= len(SUPPORTED_REFRIGERANTS):
                return SUPPORTED_REFRIGERANTS[selection - 1].name
            output_fn(f"Choose a number from 1 to {len(SUPPORTED_REFRIGERANTS)}.")
            continue
        try:
            return normalize_refrigerant(answer)
        except ValueError as exc:
            output_fn(str(exc))


def collect_learning_inputs(
    defaults: CycleInputs,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> CycleInputs:
    """Collect a cycle operating point while explaining every input."""
    output_fn("\nBUILD YOUR CYCLE")
    output_fn(
        "The refrigerant determines the saturation pressures and thermodynamic properties."
    )
    fluid = prompt_refrigerant(defaults.fluid, input_fn, output_fn)

    output_fn(
        "\nEvaporating temperature is the low-side saturation temperature, not the "
        "final evaporator-outlet temperature."
    )
    evaporating_temperature = prompt_value(
        "Evaporating saturation temperature [degC]",
        defaults.evaporating_temperature_c,
        input_fn,
        output_fn,
    )

    output_fn(
        "\nCondensing temperature is the high-side saturation temperature and must "
        "be above the evaporating temperature."
    )
    condensing_temperature = prompt_value(
        "Condensing saturation temperature [degC]",
        defaults.condensing_temperature_c,
        input_fn,
        output_fn,
        validator=lambda value: value > evaporating_temperature,
        validation_message=(
            "Condensing temperature must be greater than the evaporating temperature."
        ),
    )

    output_fn("\nSuperheat keeps liquid refrigerant away from the compressor inlet.")
    superheat = prompt_value(
        "Superheat [K]",
        defaults.superheat_k,
        input_fn,
        output_fn,
        validator=lambda value: value >= 0,
        validation_message="Superheat cannot be negative.",
    )

    output_fn("\nSubcooling ensures liquid refrigerant reaches the expansion valve.")
    subcooling = prompt_value(
        "Subcooling [K]",
        defaults.subcooling_k,
        input_fn,
        output_fn,
        validator=lambda value: value >= 0,
        validation_message="Subcooling cannot be negative.",
    )

    output_fn(
        "\nIsentropic efficiency compares the real compressor with an ideal, "
        "constant-entropy compression."
    )
    efficiency = prompt_value(
        "Compressor isentropic efficiency [0-1]",
        defaults.compressor_isentropic_efficiency,
        input_fn,
        output_fn,
        validator=lambda value: 0 < value <= 1,
        validation_message="Efficiency must be greater than 0 and no greater than 1.",
    )

    output_fn("\nMass flow scales capacities and compressor power.")
    mass_flow = prompt_value(
        "Refrigerant mass flow [kg/s]",
        defaults.mass_flow_kg_s,
        input_fn,
        output_fn,
        validator=lambda value: value > 0,
        validation_message="Mass flow must be greater than zero.",
    )

    return CycleInputs(
        fluid=fluid,
        evaporating_temperature_c=evaporating_temperature,
        condensing_temperature_c=condensing_temperature,
        superheat_k=superheat,
        subcooling_k=subcooling,
        compressor_isentropic_efficiency=efficiency,
        mass_flow_kg_s=mass_flow,
    )


def format_input_summary(inputs: CycleInputs) -> str:
    """Format the learner's selected operating point for confirmation."""
    return "\n".join(
        (
            f"Refrigerant:                 {inputs.fluid}",
            f"Evaporating temperature:     {inputs.evaporating_temperature_c:.1f} degC",
            f"Condensing temperature:      {inputs.condensing_temperature_c:.1f} degC",
            f"Superheat:                    {inputs.superheat_k:.1f} K",
            f"Subcooling:                   {inputs.subcooling_k:.1f} K",
            f"Compressor efficiency:        {inputs.compressor_isentropic_efficiency:.0%}",
            f"Mass flow:                    {inputs.mass_flow_kg_s:.3f} kg/s",
        )
    )


def confirm(
    prompt: str,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> bool:
    """Prompt until the learner provides a recognizable yes/no answer."""
    while True:
        answer = input_fn(f"{prompt} [Y/n]: ").strip().lower()
        if answer in {"", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        output_fn("Please answer y or n.")


def pause(input_fn: InputFunction) -> None:
    """Pause an interactive walkthrough until the learner is ready."""
    input_fn("Press Enter to continue...")


def walk_through_cycle(
    result: CycleResult,
    input_fn: InputFunction,
    output_fn: OutputFunction,
) -> None:
    """Explain the four canonical states in physical flow order."""
    state1, state2, state3, state4 = result.states
    explanations = build_explanations(result)
    state_details = (
        (
            "STEP 1 - EVAPORATOR OUTLET",
            explanations[3],
            state1,
        ),
        (
            "STEP 2 - COMPRESSOR OUTLET",
            explanations[0],
            state2,
        ),
        (
            "STEP 3 - CONDENSER OUTLET",
            explanations[1],
            state3,
        ),
        (
            "STEP 4 - EXPANSION VALVE OUTLET",
            explanations[2],
            state4,
        ),
    )
    for title, explanation, state in state_details:
        output_fn(f"\n{title}")
        output_fn(explanation)
        output_fn(
            f"P = {state.pressure_pa / 100_000:.2f} bar(a), "
            f"T = {state.temperature_k - 273.15:.2f} degC, "
            f"h = {state.enthalpy_j_kg / 1000:.2f} kJ/kg, "
            f"phase = {describe_phase(state)}"
        )
        pause(input_fn)

    output_fn("\nENERGY BALANCE")
    output_fn(format_performance_summary(result))


def run_learning_session(
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> int:
    """Run an interactive, repeatable lesson around the cycle solver."""
    output_fn("HVAC CYCLE LEARNING LAB")
    output_fn(
        "Build a vapor-compression cycle, then inspect what happens in each component."
    )
    current_inputs = CycleInputs()

    while True:
        current_inputs = collect_learning_inputs(current_inputs, input_fn, output_fn)
        output_fn("\nYOUR OPERATING POINT")
        output_fn(format_input_summary(current_inputs))
        if not confirm("Run this simulation?", input_fn, output_fn):
            output_fn("Lesson cancelled.")
            return 0

        try:
            result = simulate_cycle(current_inputs)
        except ValueError as exc:
            output_fn(f"Simulation failed: {exc}")
            output_fn("Review the inputs and try again.")
            continue

        walk_through_cycle(result, input_fn, output_fn)

        while True:
            output_fn("\nWHAT WOULD YOU LIKE TO DO?")
            output_fn("1. Change inputs and simulate again")
            output_fn("2. Show the complete state table")
            output_fn("3. Export the result as JSON")
            output_fn("4. Exit")
            choice = input_fn("Choose [1-4]: ").strip()
            if choice == "1":
                break
            if choice == "2":
                output_fn("\n" + format_state_table(result))
                continue
            if choice == "3":
                output_fn(json.dumps(result_as_dict(current_inputs, result), indent=2))
                continue
            if choice == "4":
                output_fn("Lesson complete. Try changing one variable next time.")
                return 0
            output_fn("Please choose 1, 2, 3 or 4.")


def run(
    argv: Sequence[str] | None = None,
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> int:
    """Run the CLI and return a process exit code."""
    parser = create_parser()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if (
        arguments
        and arguments[0].startswith("-")
        and arguments[0] not in {"-h", "--help", "--version"}
    ):
        parser.error(
            "a subcommand is required before options; "
            "use 'hvac-cycle simulate' or 'hvac-cycle learn'"
        )
    args = parser.parse_args(arguments)
    if args.command == "learn":
        try:
            return run_learning_session(input_fn=input_fn, output_fn=output_fn)
        except EOFError:
            output_fn("\nNo more input. Lesson ended.")
            return 0
        except KeyboardInterrupt:
            output_fn("\nLesson interrupted.")
            return 130

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
