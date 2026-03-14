from __future__ import annotations

CLASS_NAMES = [
    "Carpetweed",
    "Eclipta",
    "Goosegrass",
    "Lambsquarters",
    "Morningglory",
    "Ragweed",
    "Palmer Amaranth",
    "Purslane",
    "Spotted spurge",
    "Waterhemp",
]


def normalize_class_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


CLASS_NAME_ALIASES = {
    normalize_class_name("Carpetweed"): "Carpetweed",
    normalize_class_name("Eclipta"): "Eclipta",
    normalize_class_name("Goosegrass"): "Goosegrass",
    normalize_class_name("Lambsquarters"): "Lambsquarters",
    normalize_class_name("Morningglory"): "Morningglory",
    normalize_class_name("MorningGlory"): "Morningglory",
    normalize_class_name("Ragweed"): "Ragweed",
    normalize_class_name("Palmer Amaranth"): "Palmer Amaranth",
    normalize_class_name("PalmerAmaranth"): "Palmer Amaranth",
    normalize_class_name("Purslane"): "Purslane",
    normalize_class_name("Spotted spurge"): "Spotted spurge",
    normalize_class_name("SpottedSpurge"): "Spotted spurge",
    normalize_class_name("Waterhemp"): "Waterhemp",
}

CLASS_NAME_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}


def canonicalize_class_name(name: str) -> str | None:
    return CLASS_NAME_ALIASES.get(normalize_class_name(name or ""))


def class_id_from_name(name: str) -> int | None:
    canonical = canonicalize_class_name(name)
    if canonical is None:
        return None
    return CLASS_NAME_TO_ID[canonical]