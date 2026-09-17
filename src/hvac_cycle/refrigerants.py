from dataclasses import dataclass


@dataclass(frozen=True)
class Refrigerant:
    """A refrigerant intentionally supported by the educational cycle model."""

    name: str
    description: str
    aliases: tuple[str, ...] = ()


SUPPORTED_REFRIGERANTS = (
    Refrigerant("R134a", "widely used reference refrigerant", ("R-134a",)),
    Refrigerant(
        "R1234ze(E)",
        "low-GWP HFO",
        ("R1234ze", "R-1234ze", "R-1234ze(E)"),
    ),
    Refrigerant("R1234yf", "low-GWP HFO", ("R-1234yf",)),
    Refrigerant("R32", "higher-pressure HFC", ("R-32",)),
    Refrigerant("R290", "propane; flammable refrigerant", ("R-290", "propane")),
)


def _normalization_key(value: str) -> str:
    return value.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def supported_refrigerant_names() -> tuple[str, ...]:
    """Return canonical refrigerant names in display order."""
    return tuple(refrigerant.name for refrigerant in SUPPORTED_REFRIGERANTS)


def normalize_refrigerant(value: str) -> str:
    """Resolve a canonical name or friendly alias, case-insensitively."""
    key = _normalization_key(value)
    for refrigerant in SUPPORTED_REFRIGERANTS:
        candidates = (refrigerant.name, *refrigerant.aliases)
        if key in {_normalization_key(candidate) for candidate in candidates}:
            return refrigerant.name

    supported = ", ".join(supported_refrigerant_names())
    raise ValueError(f"Unsupported refrigerant '{value}'. Choose one of: {supported}")
