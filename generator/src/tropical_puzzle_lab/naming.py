"""Puzzle names: `<Shape> <pieces><letter>`, and `-r` / `-f` for the relief and flat variants.

The recipe stores only the shape and the letter (`"name": {"shape": "Hill", "letter": "b"}`); the piece
count comes from the construction, so a name cannot disagree with its puzzle. See docs/puzzle-format.md.
"""
from __future__ import annotations

import re

#: Roof shape -> the kind of function that produces it, so a shape cannot be given to the wrong maths.
SHAPES = {
    "Bowl": "max polynomial",
    "Hill": "min polynomial",
    "Terrain": "rational",
    "Corrugated": "rational",
}

#: Variant -> code suffix.
SUFFIXES = {"relief": "r", "tiling": "f"}

LETTER = re.compile(r"[a-z]")


def function_kind(recipe: dict) -> str:
    if "numerator" in recipe:
        return "rational"
    return f"{recipe.get('convention', 'max')} polynomial"


def construction_name(recipe: dict, piece_count: int) -> str:
    """`Hill 16b`: the name shared by both variants of a construction."""
    spec = recipe.get("name")
    if not isinstance(spec, dict):
        raise ValueError(f"{recipe['id']}: recipe needs \"name\": {{\"shape\", \"letter\"}}")
    shape, letter = spec.get("shape"), spec.get("letter")
    if shape not in SHAPES:
        raise ValueError(f"{recipe['id']}: shape {shape!r} is not one of {', '.join(SHAPES)}")
    if SHAPES[shape] != function_kind(recipe):
        raise ValueError(f"{recipe['id']}: {shape} is for a {SHAPES[shape]}, not a {function_kind(recipe)}")
    if not isinstance(letter, str) or not LETTER.fullmatch(letter):
        raise ValueError(f"{recipe['id']}: letter {letter!r} must be one lower-case letter")
    return f"{shape} {piece_count}{letter}"


def variant_code(name: str, variant: str) -> str:
    """`Hill 16b-r` / `Hill 16b-f`: one variant, for print listings, file names and conversation."""
    return f"{name}-{SUFFIXES[variant]}"
