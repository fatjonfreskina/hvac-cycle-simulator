from typing import Optional, Dict
from CoolProp.CoolProp import PropsSI

def get_state_PT(P: float, T: float, fluid: str) -> Dict[str, Optional[float]]:
    """
    Compute thermodynamic state from pressure and temperature.

    This function works reliably in single-phase regions. At saturation
    conditions, (P, T) is not sufficient to uniquely define the state,
    so the function returns saturation bounds instead of a single value.

    Parameters
    ----------
    P : float
        Pressure in Pascal [Pa]

    T : float
        Temperature in Kelvin [K]

    fluid : str
        Fluid name as expected by CoolProp (e.g. "R1234ZE", "R134a")

    Returns
    -------
    dict
        Dictionary with the following keys:

        - "P" (float): pressure [Pa]
        - "T" (float): temperature [K]
        - "T_sat" (float): saturation temperature at given pressure [K]
        - "phase" (str): one of:
            "subcooled liquid", "superheated vapor", "saturated"
        - "h" (float | None): specific enthalpy [J/kg]
        - "s" (float | None): specific entropy [J/kg/K]
        - "h_liq" (float | None): saturated liquid enthalpy [J/kg]
        - "h_vap" (float | None): saturated vapor enthalpy [J/kg]
        - "s_liq" (float | None): saturated liquid entropy [J/kg/K]
        - "s_vap" (float | None): saturated vapor entropy [J/kg/K]

    Notes
    -----
    - In single-phase regions, "h" and "s" are defined and saturation values are None.
    - At saturation, "h" and "s" are not uniquely defined and are set to None.
      Instead, saturation bounds (liq/vap) are returned.
    - A small tolerance is used to classify states near saturation.
    """

    tol = 1.0   # 1 J/kg is already very precise

    result: Dict[str, Optional[float]] = {
        "P": P,
        "T": T,
        "T_sat": None,
        "phase": None,
        "h": None,
        "s": None,
        "h_liq": None,
        "h_vap": None,
        "s_liq": None,
        "s_vap": None,
    }

    # Saturation temperature at given pressure
    T_sat = PropsSI("T", "P", P, "Q", 0, fluid)
    result["T_sat"] = T_sat

    # Phase detection
    if T < T_sat - tol:
        result["phase"] = "subcooled liquid"
        result["h"] = PropsSI("H", "P", P, "T", T, fluid)
        result["s"] = PropsSI("S", "P", P, "T", T, fluid)

    elif T > T_sat + tol:
        result["phase"] = "superheated vapor"
        result["h"] = PropsSI("H", "P", P, "T", T, fluid)
        result["s"] = PropsSI("S", "P", P, "T", T, fluid)

    else:
        result["phase"] = "saturated"

        # Saturation bounds
        result["h_liq"] = PropsSI("H", "P", P, "Q", 0, fluid)
        result["h_vap"] = PropsSI("H", "P", P, "Q", 1, fluid)

        result["s_liq"] = PropsSI("S", "P", P, "Q", 0, fluid)
        result["s_vap"] = PropsSI("S", "P", P, "Q", 1, fluid)

    return result


def get_state_PH(P: float, h: float, fluid: str) -> Dict[str, Optional[float]]:
    """
    Compute thermodynamic state from pressure and enthalpy.

    This is the preferred state definition for refrigeration cycles because
    (P, h) uniquely identifies the state even in the two-phase region.

    Parameters
    ----------
    P : float
        Pressure in Pascal [Pa]

    h : float
        Specific enthalpy in Joule per kilogram [J/kg]

    fluid : str
        Fluid name as expected by CoolProp (e.g. "R1234ZE", "R134a")

    Returns
    -------
    dict
        Dictionary with the following keys:

        - "P" (float): pressure [Pa]
        - "T" (float): temperature [K]
        - "phase" (str): one of:
            "subcooled liquid", "superheated vapor", "saturated"
        - "h" (float): specific enthalpy [J/kg]
        - "s" (float): specific entropy [J/kg/K]
        - "Q" (float | None): vapor quality (0-1 if two-phase, else None)

    Notes
    -----
    - In the two-phase region, vapor quality Q is computed from enthalpy.
    - Entropy is interpolated linearly between saturated liquid and vapor.
    - A small tolerance is used to handle numerical precision issues.
    """

    tol = 1.0   # 1 J/kg is already very precise

    result: Dict[str, Optional[float]] = {
        "P": P,
        "T": None,
        "phase": None,
        "h": h,
        "s": None,
        "Q": None,
    }

    # Temperature from (P, h)
    result["T"] = PropsSI("T", "P", P, "H", h, fluid)

    # Saturation limits at given pressure
    h_liq = PropsSI("H", "P", P, "Q", 0, fluid)
    h_vap = PropsSI("H", "P", P, "Q", 1, fluid)

    s_liq = PropsSI("S", "P", P, "Q", 0, fluid)
    s_vap = PropsSI("S", "P", P, "Q", 1, fluid)

    # Phase detection
    if h < h_liq - tol:
        result["phase"] = "subcooled liquid"
        result["s"] = PropsSI("S", "P", P, "H", h, fluid)

    elif h > h_vap + tol:
        result["phase"] = "superheated vapor"
        result["s"] = PropsSI("S", "P", P, "H", h, fluid)

    else:
        result["phase"] = "saturated"

        # Vapor quality
        Q_raw = (h - h_liq) / (h_vap - h_liq)

        # Clamp for numerical stability
        if Q_raw < -1e-6 or Q_raw > 1 + 1e-6:
            raise ValueError("Inconsistent state: enthalpy outside saturation bounds")

        Q = max(0.0, min(1.0, Q_raw))
        # snap to boundaries
        if abs(Q) < 1e-6:
            Q = 0.0
        elif abs(Q - 1.0) < 1e-6:
            Q = 1.0
        result["Q"] = Q

        # Entropy interpolation
        result["s"] = s_liq + Q * (s_vap - s_liq)

    return result

if __name__ == "__main__":
    P = 101325
    fluid = 'R1234ZE'
    h_liq = PropsSI('H', 'P', P, 'Q', 0, fluid)
    h_vap = PropsSI('H', 'P', P, 'Q', 1, fluid)
    
    print(get_state_PH(P, h_liq, fluid))
    print(get_state_PH(P, h_liq - 1000, fluid))
    print(get_state_PH(P, h_vap, fluid))
    print(get_state_PH(P, h_vap + 1000, fluid))
