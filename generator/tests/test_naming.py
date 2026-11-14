import json
from pathlib import Path

import pytest

from tropical_puzzle_lab.export import build_index
from tropical_puzzle_lab.naming import construction_name, variant_code

PUZZLES = Path(__file__).resolve().parents[2] / "puzzles"


def recipe(**overrides):
    base = {"id": "x", "convention": "min", "terms": [], "name": {"shape": "Hill", "letter": "b"}}
    return {**base, **overrides}


def test_name_and_codes():
    name = construction_name(recipe(), 16)
    assert name == "Hill 16b"
    assert variant_code(name, "relief") == "Hill 16b-r"
    assert variant_code(name, "tiling") == "Hill 16b-f"


@pytest.mark.parametrize("bad", [
    recipe(name=None),
    recipe(name={"shape": "Dome", "letter": "a"}),
    recipe(name={"shape": "Hill", "letter": "A"}),
    recipe(name={"shape": "Hill", "letter": "ab"}),
    recipe(name={"shape": "Bowl", "letter": "a"}),  # a min polynomial is a hill, not a bowl
    recipe(convention="max"),  # and a max polynomial is a bowl
    recipe(numerator=[], name={"shape": "Hill", "letter": "a"}),  # rational: Terrain or Corrugated
])
def test_invalid_names_are_rejected(bad):
    with pytest.raises(ValueError):
        construction_name(bad, 16)


def test_committed_names_are_unique_and_shared_by_both_variants():
    index = json.loads((PUZZLES / "index.json").read_text(encoding="utf-8"))
    by_construction = {}
    for e in index["puzzles"]:
        by_construction.setdefault(e["construction"], set()).add(e["name"])
        assert e["code"] == variant_code(e["name"], e["variant"])
    assert all(len(names) == 1 for names in by_construction.values())
    names = [next(iter(n)) for n in by_construction.values()]
    assert len(names) == len(set(names))


def test_index_rejects_a_reused_letter(tmp_path):
    for pid in ("new1", "new2"):
        p = json.loads((PUZZLES / pid / "puzzle.json").read_text(encoding="utf-8"))
        p["name"] = "Hill 16a"
        (tmp_path / pid).mkdir()
        (tmp_path / pid / "puzzle.json").write_text(json.dumps(p), encoding="utf-8")
    with pytest.raises(ValueError, match="new letter"):
        build_index(tmp_path)


def test_printables_link_is_carried_into_the_relief_variant_only():
    index = {e["id"]: e for e in json.loads((PUZZLES / "index.json").read_text(encoding="utf-8"))["puzzles"]}
    assert index["new2"]["printables"].startswith("https://www.printables.com/model/1914257-")
    assert "printables" not in index["new2-flat"]


@pytest.mark.parametrize("url", ["https://example.com/model/1", "https://www.printables.com/model/abc", 7])
def test_printables_link_must_be_a_printables_model(url):
    from tropical_puzzle_lab.export import printables_url
    with pytest.raises(ValueError):
        printables_url({"id": "x", "printables": url})
