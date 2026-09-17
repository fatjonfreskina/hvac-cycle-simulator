# HVAC Cycle Simulator

An educational vapor-compression cycle simulator for future HVAC engineers.
The project aims to become an interactive learning lab where students can
change operating conditions, inspect thermodynamic states and explain the
physical consequences.

## Current capabilities

- Steady-state four-component refrigeration cycle
- CoolProp refrigerant properties
- Compressor isentropic efficiency
- Evaporator superheat and condenser subcooling
- Cooling capacity, compressor power and COP
- Typed state and result models
- Physical-input validation and energy-balance tests

The model is intentionally idealized. Pressure drops, heat exchanger sizing,
compressor maps and transient behavior are not yet represented.

## Setup

Python 3.11 or newer is required.

### Windows PowerShell

Check which Python versions are available and create the environment explicitly
with Python 3.11 or newer. Using `python -m venv` may otherwise select an older
installation such as Python 3.9.

```powershell
py --list
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Alternatively, `python -m pip install -r requirements.txt` performs the minimal
installation, including the `hvac-cycle` command.

## Command-line interface

```bash
hvac-cycle --help
```

Run a simulation with the default operating point:

```bash
hvac-cycle simulate
```

Simulate a custom operating point:

```bash
hvac-cycle simulate --fluid R134a --evap-temp 0 --cond-temp 45 \
  --superheat 7 --subcooling 3 --efficiency 0.70 --mass-flow 0.04
```

Use `--output summary` for a compact result or `--output json` for a
machine-readable result suitable for scripts and future user interfaces.

Supported refrigerants are `R134a`, `R1234ze(E)`, `R1234yf`, `R32`, `R290` and
`R744` (CO2).
Common aliases are accepted case-insensitively; for example, `R1234ze` is
normalized to the CoolProp name `R1234ze(E)`. These choices are supported by
the current subcritical educational model and do not imply safety or equipment
compatibility approval.

R744 automatically uses a subcritical default operating point of -10 degC
evaporation and 25 degC condensation. Transcritical CO2 cycles are not yet
modeled. R515B is recognized but cannot be calculated with the bundled CoolProp
HEOS backend because the required R1234ze(E)/R227ea binary interaction data is
not available; validated R515B support requires an optional REFPROP backend.

Start an interactive lesson that explains every input and walks through the
four cycle states:

```bash
hvac-cycle learn
```

The subcommand is always required. Use `simulate` for direct calculations and
`learn` for the guided lesson; options are never routed implicitly.

The equivalent module invocation is useful if the shell has not refreshed its
command lookup after installation:

```bash
python -m hvac_cycle
```

## Run the tests

```bash
python -m pytest
```

Using `python -m pytest` ensures that tests run with the interpreter from the
active virtual environment rather than a different global `pytest` executable.

## Troubleshooting

Verify that all commands resolve to the active environment:

```powershell
python --version
python -m pip --version
python -m pip show hvac-cycle-simulator
Get-Command python
Get-Command hvac-cycle
```

If `python --version` reports Python 3.9, deactivate and recreate `.venv` using
the explicit `py -3.11 -m venv .venv` command above. Python 3.9 is not supported.

## Project direction

See [ROADMAP.md](ROADMAP.md) for the planned evolution toward an interactive
HVAC Learning Lab for students, educators and firmware/control engineers.

## Disclaimer

This software is intended for education and early engineering exploration. It
must not be used as the sole basis for equipment selection or safety decisions.
