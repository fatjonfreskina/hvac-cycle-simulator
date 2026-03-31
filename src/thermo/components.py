from CoolProp.CoolProp import PropsSI
from state import get_state_PH

def expansion_valve(P_in, h_in, P_out, fluid):
    h_out = h_in
    return get_state_PH(P_out, h_in, fluid)

if __name__ == "__main__":
    fluid = "R1234ZE"
    P_high = 8e5   # condenser pressure
    P_low  = 2e5   # evaporator pressure
    T_sub = PropsSI('T', 'P', P_high, 'Q', 0, fluid) - 13
    h_in = PropsSI('H', 'P', P_high, 'T', T_sub, fluid) 
    state_out = expansion_valve(P_high, h_in, P_low, fluid)
    print(state_out)
