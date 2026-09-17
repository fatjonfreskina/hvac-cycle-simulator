from dataclasses import dataclass


@dataclass(frozen=True)
class Refrigerant:
    """A refrigerant intentionally supported by the educational cycle model."""

    name: str
    description: str
    aliases: tuple[str, ...] = ()
    default_evaporating_temperature_c: float = 5.0
    default_condensing_temperature_c: float = 40.0
    default_superheat_k: float = 5.0
    default_subcooling_k: float = 5.0


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
    Refrigerant(
        "R744",
        "carbon dioxide; subcritical cycles only",
        ("R-744", "CO2", "carbon dioxide", "carbondioxide"),
        default_evaporating_temperature_c=-10.0,
        default_condensing_temperature_c=25.0,
        default_superheat_k=5.0,
        default_subcooling_k=3.0,
    ),
)

R515B_ALIASES = ("R515B", "R-515B")


def _normalization_key(value: str) -> str:
    return value.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def supported_refrigerant_names() -> tuple[str, ...]:
    """Return canonical refrigerant names in display order."""
    return tuple(refrigerant.name for refrigerant in SUPPORTED_REFRIGERANTS)


def normalize_refrigerant(value: str) -> str:
    """Resolve a canonical name or friendly alias, case-insensitively."""
    key = _normalization_key(value)
    if key in {_normalization_key(alias) for alias in R515B_ALIASES}:
        raise ValueError(
            "R515B is not available with the bundled CoolProp HEOS backend: "
            "the R1234ze(E)/R227ea binary interaction data is missing. "
            "A REFPROP-backed implementation is required for validated results."
        )
    for refrigerant in SUPPORTED_REFRIGERANTS:
        candidates = (refrigerant.name, *refrigerant.aliases)
        if key in {_normalization_key(candidate) for candidate in candidates}:
            return refrigerant.name

    supported = ", ".join(supported_refrigerant_names())
    raise ValueError(f"Unsupported refrigerant '{value}'. Choose one of: {supported}")


def get_refrigerant(value: str) -> Refrigerant:
    """Return metadata and recommended defaults for a supported refrigerant."""
    canonical = normalize_refrigerant(value)
    return next(
        refrigerant
        for refrigerant in SUPPORTED_REFRIGERANTS
        if refrigerant.name == canonical
    )
