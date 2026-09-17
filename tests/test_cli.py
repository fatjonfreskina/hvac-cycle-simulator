import json

import pytest

from hvac_cycle import CycleInputs, simulate_cycle
from hvac_cycle.cli import (
    build_explanations,
    create_parser,
    describe_phase,
    format_performance_summary,
    format_state_table,
    inputs_from_args,
    prompt_refrigerant,
    prompt_value,
    run,
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


def test_parser_maps_custom_values_to_cycle_inputs() -> None:
    parser = create_parser()
    args = parser.parse_args(
        [
            "simulate",
            "--fluid", "R1234ze(E)",
            "--evap-temp", "0",
            "--cond-temp", "45",
            "--superheat", "7",
            "--subcooling", "3",
            "--efficiency", "0.7",
            "--mass-flow", "0.04",
        ]
    )

    assert inputs_from_args(args) == CycleInputs(
        fluid="R1234ze(E)",
        evaporating_temperature_c=0,
        condensing_temperature_c=45,
        superheat_k=7,
        subcooling_k=3,
        compressor_isentropic_efficiency=0.7,
        mass_flow_kg_s=0.04,
    )


def test_top_level_help_lists_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "simulate" in output
    assert "learn" in output


def test_simulate_help_lists_physical_inputs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["simulate", "--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "--evap-temp" in output
    assert "--cond-temp" in output
    assert "--efficiency" in output
    assert "saturation temperatures" in output


def test_summary_output_uses_custom_operating_point(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run(
        [
            "simulate",
            "--evap-temp", "0",
            "--cond-temp", "45",
            "--mass-flow", "0.04",
            "--output", "summary",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Evaporating pressure:" in output
    assert "Cooling COP:" in output
    assert "WHAT HAPPENS" not in output


def test_json_output_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["simulate", "--output", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["inputs"]["fluid"] == "R134a"
    assert len(payload["states"]) == 4
    assert payload["states"][0]["location"] == "Evaporator outlet"
    assert payload["performance"]["cooling_cop"] > 1


def test_invalid_cli_inputs_return_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["simulate", "--evap-temp", "50", "--cond-temp", "40"])

    assert exit_info.value.code == 2
    assert "Evaporating temperature must be below" in capsys.readouterr().err


def test_subcommand_is_required(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run([])

    assert exit_info.value.code == 2
    error = capsys.readouterr().err
    assert "the following arguments are required: COMMAND" in error


def test_simulation_options_are_rejected_without_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["--evap-temp", "0"])

    assert exit_info.value.code == 2
    error = capsys.readouterr().err
    assert "a subcommand is required before options" in error
    assert "hvac-cycle simulate" in error
    assert "hvac-cycle learn" in error


def test_prompt_value_retries_invalid_answers() -> None:
    answers = iter(["not-a-number", "-1", "0.1"])
    messages: list[str] = []

    value = prompt_value(
        "Mass flow",
        0.05,
        lambda _: next(answers),
        messages.append,
        validator=lambda candidate: candidate > 0,
        validation_message="Mass flow must be positive.",
    )

    assert value == 0.1
    assert any("Please enter a number" in message for message in messages)
    assert "Mass flow must be positive." in messages


def test_learning_session_guides_the_default_cycle() -> None:
    answers = iter(["", "", "", "", "", "", "", "", "", "", "", "", "4"])
    messages: list[str] = []

    exit_code = run(
        ["learn"],
        input_fn=lambda _: next(answers),
        output_fn=messages.append,
    )

    output = "\n".join(messages)
    assert exit_code == 0
    assert "HVAC CYCLE LEARNING LAB" in output
    assert "STEP 1 - EVAPORATOR OUTLET" in output
    assert "STEP 4 - EXPANSION VALVE OUTLET" in output
    assert "ENERGY BALANCE" in output
    assert "Lesson complete" in output


def test_learning_session_handles_end_of_input_cleanly() -> None:
    messages: list[str] = []

    exit_code = run(
        ["learn"],
        input_fn=lambda _: (_ for _ in ()).throw(EOFError),
        output_fn=messages.append,
    )

    assert exit_code == 0
    assert any("Lesson ended" in message for message in messages)


def test_simulate_accepts_r1234ze_alias(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(["simulate", "--fluid", "R1234ze", "--output", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["inputs"]["fluid"] == "R1234ze(E)"
    assert payload["performance"]["cooling_cop"] > 1


def test_refrigerant_prompt_accepts_numbered_selection() -> None:
    messages: list[str] = []

    selected = prompt_refrigerant("R134a", lambda _: "2", messages.append)

    assert selected == "R1234ze(E)"
    assert any("R1234ze(E)" in message for message in messages)


def test_learning_session_accepts_r1234ze_alias() -> None:
    answers = iter(
        ["R1234ze", "", "", "", "", "", "", "", "", "", "", "", "4"]
    )
    messages: list[str] = []

    exit_code = run(
        ["learn"],
        input_fn=lambda _: next(answers),
        output_fn=messages.append,
    )

    output = "\n".join(messages)
    assert exit_code == 0
    assert "Refrigerant:                 R1234ze(E)" in output
    assert "Lesson complete" in output


def test_simulate_uses_subcritical_defaults_for_co2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(["simulate", "--fluid", "CO2", "--output", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["inputs"]["fluid"] == "R744"
    assert payload["inputs"]["evaporating_temperature_c"] == -10.0
    assert payload["inputs"]["condensing_temperature_c"] == 25.0
    assert payload["inputs"]["superheat_k"] == 5.0
    assert payload["inputs"]["subcooling_k"] == 3.0
    assert payload["performance"]["cooling_cop"] > 1


def test_r515b_cli_error_is_actionable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["simulate", "--fluid", "R515B"])

    assert exit_info.value.code == 2
    error = capsys.readouterr().err
    assert "CoolProp HEOS" in error
    assert "REFPROP" in error


def test_learning_session_uses_subcritical_co2_defaults() -> None:
    answers = iter(["CO2", "", "", "", "", "", "", "", "", "", "", "", "4"])
    messages: list[str] = []

    exit_code = run(
        ["learn"],
        input_fn=lambda _: next(answers),
        output_fn=messages.append,
    )

    output = "\n".join(messages)
    assert exit_code == 0
    assert "Refrigerant:                 R744" in output
    assert "Evaporating temperature:     -10.0 degC" in output
    assert "Condensing temperature:      25.0 degC" in output
    assert "Subcooling:                   3.0 K" in output
