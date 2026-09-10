from .cycle import CycleInputs, simulate_cycle


def main() -> None:
    result = simulate_cycle(CycleInputs())
    print("Educational HVAC cycle - R134a")
    print(f"Cooling capacity: {result.cooling_capacity_w / 1000:.2f} kW")
    print(f"Compressor power: {result.compressor_power_w / 1000:.2f} kW")
    print(f"Cooling COP: {result.cooling_cop:.2f}")


if __name__ == "__main__":
    main()
