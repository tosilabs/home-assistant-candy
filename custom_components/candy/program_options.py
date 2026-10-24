"""Display category-prefixed labels while keeping recipe identities unchanged."""
from .programs import (
    WASHING_MACHINE_PROGRAMS, WASHING_MACHINE_PROGRAMS_BY_NAME,
    WASHING_MACHINE_PROGRAM_META_SQ,
    TUMBLE_DRYER_PROGRAMS, TUMBLE_DRYER_PROGRAMS_BY_NAME,
    TUMBLE_DRYER_PROGRAM_META_SQ,
)


def _options(programs, metadata):
    labels = {
        f"{metadata.get(p.name, {}).get('category', 'Tjetër')} - {p.name}": p.name
        for p in programs
    }
    if len(labels) != len(programs):
        raise ValueError("Program labels must identify each recipe uniquely")
    return dict(sorted(labels.items(), key=lambda item: item[0].casefold()))


WASH_OPTIONS = _options(WASHING_MACHINE_PROGRAMS, WASHING_MACHINE_PROGRAM_META_SQ)
DRY_OPTIONS = _options(TUMBLE_DRYER_PROGRAMS, TUMBLE_DRYER_PROGRAM_META_SQ)
WASH_LABELS = {name: label for label, name in WASH_OPTIONS.items()}
DRY_LABELS = {name: label for label, name in DRY_OPTIONS.items()}


def resolve_wash_name(option):
    """Accept a current label or a legacy unprefixed recipe name."""
    if option in WASH_OPTIONS:
        return WASH_OPTIONS[option]
    return option if option in WASHING_MACHINE_PROGRAMS_BY_NAME else None


def resolve_dry_name(option):
    if option in DRY_OPTIONS:
        return DRY_OPTIONS[option]
    return option if option in TUMBLE_DRYER_PROGRAMS_BY_NAME else None
