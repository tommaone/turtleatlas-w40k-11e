"""The ability guard must fire on corrupt data, not merely pass on good data.

A check that only ever returns green is indistinguishable from no check at all.
Each case stages one faction's committed data into a tmp dir, corrupts a single
ability, and asserts the real check_abilities path reports it. The repo's own
data/merged/ is never written to.
"""
import json
import shutil

import pytest

from adversarial import deterministic_check as dc

INT_SLUG = "adepta-sororitas"     # carries fnp and transport_capacity
SPEC_SLUG = "adeptus-custodes"    # carries reroll
BOOST_SLUG = "world-eaters"       # carries damage_boost


def _stage(tmp_path, slug):
    """Point the check at a copy of one faction's committed data."""
    staged = tmp_path / "merged"
    staged.mkdir()
    shutil.copy(dc.MERGED_DIR / f"{slug}.json", staged / f"{slug}.json")
    return staged


def _first_with(data, field):
    for unit in data.get("units", []):
        for ability in (unit.get("profile") or {}).get("abilities") or []:
            if isinstance(ability, dict) and ability.get(field) is not None:
                return ability
    pytest.skip(f"no committed ability carries {field}")


def _corrupt_and_run(tmp_path, monkeypatch, slug, field, corrupt):
    staged = _stage(tmp_path, slug)
    monkeypatch.setattr(dc, "MERGED_DIR", staged)
    path = staged / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    corrupt(_first_with(data, field))
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    result = dc.validate_faction(slug)
    assert not result.get("error"), result.get("error")
    return [f["message"] for f in result["findings"] if f["severity"] == "MAJOR"]


def test_committed_data_is_quiet(tmp_path, monkeypatch):
    """Anchor: the corpus as committed produces no ability MAJOR.

    Without this, a case below passing would prove nothing — a check that reports
    everything would satisfy the same assertions.
    """
    staged = _stage(tmp_path, INT_SLUG)
    monkeypatch.setattr(dc, "MERGED_DIR", staged)
    result = dc.validate_faction(INT_SLUG)
    assert not result.get("error"), result.get("error")
    assert [f for f in result["findings"] if f["severity"] == "MAJOR"] == []


CASES = [
    pytest.param(INT_SLUG, "fnp",
                 lambda ab: ab.update(description="Hits on a 2+ reroll"),
                 "still carries rule text", id="reinstated-rule-text"),
    pytest.param(INT_SLUG, "transport_capacity",
                 lambda ab: ab.update(transport_capacity=True),
                 "not a non-negative int", id="capacity-as-bool"),
    pytest.param(INT_SLUG, "transport_capacity",
                 lambda ab: ab.update(transport_capacity=-1),
                 "not a non-negative int", id="capacity-negative"),
    pytest.param(INT_SLUG, "transport_capacity",
                 lambda ab: ab.update(transport_capacity="12 INFANTRY"),
                 "not a non-negative int", id="capacity-as-prose"),
    pytest.param(SPEC_SLUG, "reroll",
                 lambda ab: ab["reroll"].update(reroll_hits=None, reroll_wounds=None,
                                                reroll_damage=None),
                 "sets no reroll value", id="reroll-with-no-value"),
    pytest.param(SPEC_SLUG, "reroll",
                 lambda ab: ab["reroll"].update(raw="Hits on a 2+ reroll"),
                 "embeds rule text", id="spec-re-embeds-text"),
    pytest.param(SPEC_SLUG, "reroll",
                 lambda ab: ab.update(reroll="all"),
                 "is not a spec dict", id="spec-as-bare-string"),
    pytest.param(BOOST_SLUG, "damage_boost",
                 lambda ab: ab.update(damage_boost=1),
                 "is not a spec dict", id="boost-as-bare-int"),
]


@pytest.mark.parametrize("slug,field,corrupt,expected", CASES)
def test_corrupt_ability_is_reported(tmp_path, monkeypatch, slug, field, corrupt, expected):
    majors = _corrupt_and_run(tmp_path, monkeypatch, slug, field, corrupt)
    assert any(expected in m for m in majors), f"expected {expected!r}, got {majors[:3]}"
