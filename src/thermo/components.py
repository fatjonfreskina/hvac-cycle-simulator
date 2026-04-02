from CoolProp.CoolProp import PropsSI
from state import get_state_PH

def expansion_valve(P_in: float, h_in: float, P_out: float, fluid: str):
    """
    Ideal expansion valve (throttling process).

    Models a pressure drop with constant enthalpy (isenthalpic transformation).

    Parameters
    ----------
    P_in : float
        Inlet pressure [Pa] (not used in ideal model, kept for API consistency)

    h_in : float
        Inlet specific enthalpy [J/kg]

    P_out : float
        Outlet pressure [Pa]

    fluid : str
        Fluid name (CoolProp format)

    Returns
    -------
    dict
        Outlet thermodynamic state computed from (P_out, h_in)

    Notes
    -----
    - The process is isenthalpic: h_out = h_in
    - No work is produced and no heat is exchanged
    - Pressure drop may cause partial evaporation (flash gas)
    """

    h_out = h_in
    return get_state_PH(P_out, h_out, fluid)


def evaporator(P, h_in, superheat, fluid):
    """
    Ideal evaporator model with optional superheating.

    The evaporator operates at constant pressure and adds heat to the fluid.
    It first brings the refrigerant to saturated vapor (Q = 1), then optionally
    adds superheat.

    Parameters
    ----------
    P : float
        Operating pressure [Pa] (assumed constant)

    h_in : float
        Inlet specific enthalpy [J/kg]

    superheat : float
        Desired superheating above saturation temperature [K]

    fluid : str
        Fluid name (CoolProp format, e.g. "R1234ZE")

    Returns
    -------
    dict
        {
            "state": dict,
                Outlet thermodynamic state at (P, h_out)

            "Q_dot": float
                Heat absorbed per unit mass [J/kg]
        }

    Notes
    -----
    - The process is isobaric (P = constant)
    - Heat is always added: h_out >= h_in
    - The fluid is brought to saturated vapor, then optionally superheated
    - If the inlet is already vapor, only superheating is applied
    - This is a simplified model (no pressure drops, no heat transfer limits)

    Key idea
    --------
    The evaporator completes evaporation and ensures dry vapor at the compressor
    inlet, often with a small superheat to avoid liquid ingestion.
    """
    T_sat = PropsSI('T', 'P', P, 'Q', 1, fluid)
    h_vap = PropsSI('H', 'P', P, 'Q', 1, fluid)
    T_target = T_sat + superheat
    h_out = PropsSI('H', 'P', P, 'T', T_target, fluid)
    Q_dot = h_out - h_in
    state_out = get_state_PH(P, h_out, fluid)
    return {
        "state": state_out,
        "Q_dot": Q_dot
    }


if __name__ == "__main__":
    P_high = 8e5
    P_low = 2e5
    fluid = "R1234ZE"

    # ingresso: liquido saturo dal condensatore
    h_in = PropsSI('H', 'P', P_high, 'Q', 0, fluid)

    # valvola
    state_valve = expansion_valve(P_high, h_in, P_low, fluid)

    # evaporatore con 5K di superheat
    state_evap = evaporator(
        P_low,
        state_valve["h"],
        superheat=5,
        fluid=fluid
    )

    print(state_valve)
    print(state_evap)
