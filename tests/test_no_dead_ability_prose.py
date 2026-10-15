"""Guard the rule-text invariant: no ability description is committed at all.

`data/merged/*.json` used to carry a `description` on all 2706 abilities —
~530KB of verbatim Games Workshop rule text, which AGENTS.md forbids
("⛔ No verbatim rule text (ability descriptions...)"). It was reduced in two
steps: first `scripts/strip_ability_prose.py` dropped the 2,364 descriptions
nothing read, then `adapter/merge.py` began deriving the 342 that did drive
something into machine-readable fields (`reroll`, `army_wide_reroll`,
`damage_boost`, `transport_capacity`, `fnp`) and dropping their prose too.

So the invariant is now absolute rather than relative: **zero descriptions**.

Two things are pinned here, because the artifact alone cannot do either:

1. `test_derive_ability_fields_drops_text_with_nothing_derived` — the strip in
   `adapter/merge.py` is unconditional. An earlier cut only deleted the text
   when a field had been derived, and a test that mutated it back to that
   conditional form still passed the whole suite, so nothing in the corpus
   could enforce it. This calls the function directly instead.
2. `test_committed_faction_is_reproducible_from_bsdata` — regenerates a faction
   through the real pipeline and compares it to the committed file. That gives
   the stored field *values* an independent source, which the stripped artifact
   cannot provide: the old prose could be re-parsed, the stored spec cannot.
   It also catches a hand-edited spec and a stale file from a partial re-merge.
   Sampled, not exhaustive — see REPRODUCED_FACTIONS.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dpp import transport_capacity_of  # noqa: E402
from fnp_detect import detect_fnp  # noqa: E402
from reroll_detect import detect_army_wide_reroll, detect_reroll_ability  # noqa: E402

MERGED = REPO_ROOT / "data" / "merged"

# The fields adapter/merge.py derives, in the order it derives them.
DERIVED_FIELDS = ("reroll", "army_wide_reroll", "damage_boost", "transport_capacity", "fnp")

# Recorded 2026-10-09 from a bsdata cc58ee3 / mfm 8e0e635 corpus (MFM v1.5),
# immediately before the descriptions were replaced by these fields. This pins
# the *count* per field, which catches an ability that should have gained a field
# and didn't. It does not catch a value drifting, and it does not catch a field
# moving from one ability to another — the count is an aggregate. Value drift is
# covered by the reproducibility test below, on the sampled factions.
#
# The v1.5 delta is corpus shrink, not detector regression: army_wide_reroll and
# transport_capacity each fell by 12 with the units reclassified as Legends or
# removed; fnp rose by 1.
FIELD_BASELINE = {
    "reroll": 32,
    "army_wide_reroll": 116,
    "damage_boost": 1,
    "transport_capacity": 122,
    "fnp": 48,
}

# Transport abilities, and how many resolve a headline number. Two legitimately
# carry none (the Manta's "of all of the following", the Night Scythe's unit
# count), so this is an exact pair rather than a majority threshold.
TRANSPORT_TOTAL = 124
TRANSPORT_WITH_CAPACITY = 122

# Factions regenerated end-to-end and compared to the committed file, chosen to
# cover every derived field: grey-knights has transports + rerolls + fnp,
# genestealer-cults is fnp-heavy across characters.
#
# space-marines is deliberately absent. It is the one faction with cross-faction
# fallback units, and regenerating it alone silently produces those units with no
# abilities at all (17 of them, confirmed against merge.py at 834b61e — pre-existing,
# not something this change introduced). `--all` is the only correct way to
# regenerate it, which is too slow to run per-test. Until that path is fixed, the
# reproducibility guarantee is partial and the FIELD_BASELINE count is what covers
# the other 28 factions.
REPRODUCED_FACTIONS = ("grey-knights", "genestealer-cults")

# Fictional fixtures in the *shape* BSData uses, so the detectors are exercised
# without putting rule text in the repo. Each is the minimal form that makes the
# corresponding regex fire.
PROSE_REROLL = (
    "Whenever this model attacks a ^^**CHARACTER^^** enemy unit, you may re-roll "
    "the Hit roll."
)
PROSE_TRANSPORT = "This unit has a transport capacity of 12."


def _all_abilities():
    for path in sorted(MERGED.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for unit in data.get("units", []):
            for ability in (unit.get("profile") or {}).get("abilities") or []:
                if isinstance(ability, dict):
                    yield path.name, unit.get("name"), ability


ABILITIES = list(_all_abilities())


def test_merged_corpus_has_abilities():
    assert len(ABILITIES) > 2000, "merged corpus looks unpopulated — is the submodule present?"


# -- The strip itself (not the artifact) --------------------------------------
# These call adapter.merge.derive_ability_fields directly. Nothing else in the
# suite exercises that function, which is how a conditional strip shipped green.

def test_derive_ability_fields_drops_text_with_nothing_derived():
    """Prose nothing consumes must still go — that is 2,364 of the 2,706."""
    from adapter.merge import derive_ability_fields

    ability = {
        "name": "Relentless",
        "description": "This model can make one additional attack with this weapon.",
    }
    assert derive_ability_fields(ability) == []      # no field, and that is fine
    assert "description" not in ability, (
        "the text was kept because no field was derived — that reintroduces "
        "committed rule text on every ability the detectors ignore"
    )


def test_derive_ability_fields_derives_field_and_drops_text():
    """The other half: a consumed description becomes a field, not a deletion."""
    from adapter.merge import derive_ability_fields

    ability = {"name": "Foesight (Psychic)", "description": PROSE_REROLL}
    assert derive_ability_fields(ability) == ["reroll"]
    assert ability["reroll"]["reroll_hits"] == "all"
    assert ability["reroll"]["targets"] == ["CHARACTER"]
    assert "raw" not in ability["reroll"], "raw is the rule text under another name"
    assert "description" not in ability


def test_derive_ability_fields_derives_transport_capacity():
    from adapter.merge import derive_ability_fields

    ability = {"name": "Transport", "description": PROSE_TRANSPORT}
    assert derive_ability_fields(ability) == ["transport_capacity"]
    assert ability["transport_capacity"] == 12
    assert "description" not in ability


# -- The committed artifact ---------------------------------------------------

def test_no_ability_description_is_committed():
    """The invariant AGENTS.md asks for, in its strictest form: none at all."""
    offending = [(f, u, a.get("name")) for f, u, a in ABILITIES if a.get("description")]
    assert not offending, (
        f"{len(offending)} merged ability description(s) are committed rule text. "
        f"Regenerate with adapter/merge.py, which derives {DERIVED_FIELDS} and drops "
        f"the prose. first 3: {offending[:3]}"
    )


def test_derived_field_counts_match_recorded_baseline():
    """Catches an ability that should have gained a field and didn't.

    The prose is gone, so nothing in the artifact can prove a detector would
    have fired. The aggregate count is the proxy: if the merge silently skipped
    abilities, this drops.
    """
    counts = {f: sum(1 for _, _, a in ABILITIES if a.get(f) is not None) for f in DERIVED_FIELDS}
    assert counts == FIELD_BASELINE, (
        "derived ability field counts moved. If a bsdata bump caused this, update "
        f"FIELD_BASELINE in this test in the same commit. Got: {counts}"
    )


def test_derived_specs_never_carry_the_raw_text():
    """`raw` is the rule text. Dropping it is what makes these fields committable."""
    offenders = []
    for f, u, a in ABILITIES:
        for key in ("reroll", "army_wide_reroll", "damage_boost"):
            spec = a.get(key)
            if isinstance(spec, dict) and ("raw" in spec or "ability_name" in spec):
                offenders.append((f, u, a.get("name"), key))
    assert not offenders, (
        f"{len(offenders)} derived spec(s) still embed the rule text: {offenders[:3]}"
    )


def test_transport_abilities_still_yield_a_capacity():
    """The delivery path must keep working now that it reads a field, not prose."""
    transports = [a for _, _, a in ABILITIES if str(a.get("name", "")).upper() == "TRANSPORT"]
    assert len(transports) == TRANSPORT_TOTAL, (
        f"expected {TRANSPORT_TOTAL} Transport abilities, found {len(transports)}"
    )
    with_capacity = [a for a in transports if transport_capacity_of(a) is not None]
    assert len(with_capacity) == TRANSPORT_WITH_CAPACITY, (
        f"only {len(with_capacity)}/{len(transports)} Transport abilities yield a capacity "
        "— the merge-time derivation is not populating transport_capacity"
    )
    assert all(isinstance(a["transport_capacity"], int) for a in with_capacity), (
        "capacity must be stored as an int, not a parsed string"
    )


def test_engine_reads_the_field_not_prose():
    """A detector must prefer the stored field over a description.

    Prose is gone from the corpus, so a detector that ignored the field would
    just return None and quietly drop 341 rerolls/boosts/capacities while the
    rest of the suite stayed green. Feeding a *contradicting* description is the
    only way to show the field wins rather than the two agreeing by accident.
    """
    fielded = [a for _, _, a in ABILITIES if a.get("reroll") is not None]
    assert fielded, "no ability carries a reroll field"
    decoy = "Each time this model makes an attack, you can re-roll one Hit roll."
    for a in fielded[:20]:
        poisoned = dict(a, description=decoy)
        assert detect_reroll_ability(poisoned) == a["reroll"], (
            f"detector disagreed with the stored spec for {a.get('name')!r}"
        )

    army = [a for _, _, a in ABILITIES if a.get("army_wide_reroll") is not None]
    assert army, "no ability carries an army_wide_reroll field"
    for a in army[:20]:
        poisoned = dict(a, description=decoy)
        assert detect_army_wide_reroll(poisoned) == a["army_wide_reroll"], (
            f"detector disagreed with the stored spec for {a.get('name')!r}"
        )


def test_fnp_reads_the_field():
    """gen_config.py's FNP parse runs on config regeneration, which is why fnp exists."""
    fielded = [a for _, _, a in ABILITIES if a.get("fnp") is not None]
    assert fielded, "no ability carries an fnp field"
    for a in fielded[:20]:
        assert detect_fnp(dict(a, description="Feel No Pain 6+")) == a["fnp"], (
            f"fnp detector did not prefer the stored value for {a.get('name')!r}"
        )
        assert 2 <= a["fnp"] <= 6, f"fnp outside the wound-ignore range: {a['fnp']}"


# -- The committed artifact is reproducible -----------------------------------

@pytest.mark.parametrize("slug", REPRODUCED_FACTIONS)
def test_committed_faction_is_reproducible_from_bsdata(slug):
    """Regenerate through the real pipeline and compare to the committed file.

    The point is the comparison, not the smoke test: a stored spec is only worth
    as much as the prose it replaced if re-running the merge still produces it.
    A hand-edited value, a stale file from a partial re-merge, and a detection
    that stopped firing all show up as a diff here and nowhere else.
    """
    if not list((REPO_ROOT / "bsdata").glob("*.json")):
        pytest.skip("bsdata submodule not populated")

    from adapter.bsdata_parser_11e import BSDataParser11e
    from adapter.merge import load_mfm_faction, merge_faction

    committed_path = MERGED / f"{slug}.json"
    assert committed_path.exists(), f"no committed merged file for {slug}"

    generated = merge_faction(slug, load_mfm_faction(slug), BSDataParser11e("bsdata"))
    committed = json.loads(committed_path.read_text(encoding="utf-8"))

    if generated == committed:
        return

    diffs = []
    gen_units = {u["name"]: u for u in generated.get("units", [])}
    com_units = {u["name"]: u for u in committed.get("units", [])}
    for name in sorted(set(gen_units) | set(com_units)):
        gen_abs = (gen_units.get(name, {}).get("profile") or {}).get("abilities") or []
        com_abs = (com_units.get(name, {}).get("profile") or {}).get("abilities") or []
        if json.dumps(gen_abs, sort_keys=True) == json.dumps(com_abs, sort_keys=True):
            continue
        gen_by_name = {a.get("name"): a for a in gen_abs if isinstance(a, dict)}
        com_by_name = {a.get("name"): a for a in com_abs if isinstance(a, dict)}
        for an in sorted(set(gen_by_name) | set(com_by_name)):
            g, c = gen_by_name.get(an), com_by_name.get(an)
            if json.dumps(g, sort_keys=True) != json.dumps(c, sort_keys=True):
                diffs.append(f"{slug}/{name} [{an}]:\n      merge: {json.dumps(g)}\n      file:  {json.dumps(c)}")
    for key in sorted(set(generated) | set(committed)):
        if key != "units" and generated.get(key) != committed.get(key):
            diffs.append(f"{slug}.{key} differs from a fresh merge")
    assert not diffs, "committed data is not reproducible — run adapter/merge.py:\n" + "\n".join(diffs[:8])


# -- The config generation path (scripts/gen_config.py) -----------------------

def test_config_fnp_reads_the_field_not_prose():
    """gen_config.py writes config info.FNP from this parse — guard the read path.

    This is the regression the field exists to prevent. Before it, the parse
    read ability descriptions, which the merge no longer commits: reverting
    parse_fnp_from_rules to the prose-only version loses 44 of 46 FNP values on a
    config regeneration, and nothing else in the suite noticed.
    """
    from gen_config import parse_fnp_from_rules

    # The merged shape: a field and no description at all.
    assert parse_fnp_from_rules([], [{"name": "Feel No Pain", "fnp": 4}]) == 4
    # A rule *name* carrying the value, which is how some units state it.
    assert parse_fnp_from_rules(["Feel No Pain 3+"], []) == 3
    # Split across the two: keyword in the name, threshold in the description.
    assert parse_fnp_from_rules(
        [], [{"name": "Feel No Pain", "description": "ignore 4+ wounds"}]
    ) == 4
    # Legacy prose still works, for hand-built ability lists.
    assert parse_fnp_from_rules([], [{"name": "Feel No Pain", "description": "Feel No Pain 2+"}]) == 2
    # And an ability with no FNP statement yields nothing rather than a number.
    assert parse_fnp_from_rules([], [{"name": "Relentless"}]) is None


def test_extract_info_gets_fnp_from_merged_units():
    """End of the chain: the value reaches config for every real unit that has one."""
    from gen_config import extract_info

    fielded = [
        (f, u) for f, u, a in ABILITIES if a.get("fnp") is not None
    ]
    assert fielded, "no ability carries an fnp field — merge is not deriving it"
    for f, u in fielded[:20]:
        units = json.loads((MERGED / f).read_text(encoding="utf-8"))["units"]
        profile = next(x for x in units if x["name"] == u)["profile"]
        assert extract_info(profile).get("FNP") is not None, (
            f"{f}/{u} has an fnp field but extract_info produced no config FNP"
        )


# -- The other committed data trees -------------------------------------------

def test_ability_text_outside_merged_is_not_leaking():
    """Guard the same rule for data/config. Needs are drawn from real rule text."""
    needles = (
        "transport capacity of",
        "capacity is reduced",
        "select one enemy unit",
    )
    offenders = []
    for path in sorted((REPO_ROOT / "data" / "config").rglob("*.json")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for needle in needles:
            if needle in text.lower():
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {needle!r}")
                break
    assert not offenders, f"config trees contain rule text: {offenders[:3]}"


