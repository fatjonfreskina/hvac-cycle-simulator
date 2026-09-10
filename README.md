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

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev,notebooks]"
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Run the example

```bash
hvac-cycle
```

## Run the tests

```bash
pytest
```

## Project direction

See [ROADMAP.md](ROADMAP.md) for the planned evolution toward an interactive
HVAC Learning Lab for students, educators and firmware/control engineers.

## Disclaimer

This software is intended for education and early engineering exploration. It
must not be used as the sole basis for equipment selection or safety decisions.
