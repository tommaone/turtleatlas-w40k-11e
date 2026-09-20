"""Transport delivery component tests.

Covers the min-viable delivery scoring for TRANSPORT datasheets:
- parse_transport_capacity: the capacity regex helper lives in engine/dpp.py
  (single source of computation) — tests import it, never re-implement it.
- compute_mob: transport_capacity_n + is_transport output keys.
- delivery_bonus: capacity × movement delivery component, gated strictly on
  TRANSPORT keyword AND numeric capacity > 0 (byte-stable for non-transports).
  DEEP STRIKE transports (Drop Pods) deliver once at the arrival point — the
  capacity credit stands but the movement-speed term is dropped, so their
  delivery is independent of movement (one-shot arrival, no shuttling).
- mob_score integration: a transport with capacity outscores the same hull
  without capacity, and stays within the 0-100 clamp.
- Ranking integration (structural only): real merged space-marines Transport
  prose flows through compute_ranking() into each mob dict. No mob_score value
  pins here — byte-stability is verified by the full suite + findings diff.

All Transport prose strings are copied verbatim from
data/merged/space-marines.json and data/merged/necrons.json (SM and Necron
merged files). Encoding-B factions were normalized to the same "Transport"
ability shape by the adapter (2026-09-20) — the test for the Night Scythe
locks the unit-count guard that keeps "1 NECRONS INFANTRY unit" from being
misread as a 1-model capacity.

IP note (2026-09-20, Shredder): these fixtures quote the Transport ability
description verbatim. They are treated as game-mechanics data — capacity
numbers and the slot-taking rules they encode — the same class as the
points/profiles the repo already stores (see AGENTS.md "Safe to include").
If the project owner rules otherwise, rephrase the fixtures and pin the
parser against constructed strings instead; do not commit broader verbatim
rule text from other abilities.

Run: python3 -m pytest tests/test_transport_delivery.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from dpp import compute_mob, parse_transport_capacity
from ranking import RankingEngine


# ── Real merged BSData Transport ability descriptions ──────────────────────
# Copied verbatim from data/merged/space-marines.json. \xa0 is the non-breaking
# space present in the source data and part of the exact prose.

LAND_RAIDER_PROSE = (
    "This model has a transport capacity of 12 Adeptus Astartes\xa0Infantry models. "
    "Each Jump Pack, Wulfen, Gravis or\xa0Terminator model takes up the space of 2 models "
    "and each\xa0Centurion model takes up the space of 3 models."
)
IMPULSOR_PROSE = (
    "This model has a transport capacity of 7 TACTICUS or PHOBOS INFANTRY models. "
    "It cannot transport JUMP PACK models."
)
REPULSOR_EXECUTIONER_PROSE = (
    "This model has a transport capacity of 7 Adeptus Astartes\xa0Infantry models. "
    "Each Jump Pack, Wulfen, Gravis or\xa0Terminator model takes up the space of 2 models "
    "and each\xa0Centurion model takes up the space of 3 models."
)
STORMRAVEN_GUNSHIP_PROSE = (
    "This model has a transport capacity of 12 Adeptus Astartes Infantry models and 1 "
    "Dreadnought model. Each Jump\xa0Pack, Wulfen, Gravis or Terminator model takes up "
    "the\xa0space of 2 models and each Centurion model takes up the\xa0space of 3 models."
)
RHINO_PROSE = (
    "This model has a transport capacity of 12 ADEPTUS ASTARTES INFANTRY models. "
    "It cannot transport JUMP PACK, WULFEN, PHOBOS, GRAVIS, CENTURION, TERMINATOR or "
    "TACTICUS models (excluding TACTICUS CHARACTER models that began the battle attached "
    "to a non-TACTICUS unit)"
)
DROP_POD_PROSE = (
    "This model has a transport capacity of 12 Adeptus Astartes\xa0Infantry models. "
    "It cannot transport Jump Pack, Wulfen,\xa0Gravis, Centurion or Terminator models."
)
# Necron Night Scythe: unit-count capacity (verbatim from merged necrons.json).
# The transport carries ONE unit, not "1 model" — the parser must refuse the
# number so the delivery metric is not fed a false 1-model capacity.
NIGHT_SCYTHE_PROSE = "This model has a transport capacity of 1 NECRONS INFANTRY\xa0unit."
# Non-transport ability description (same file) — must yield None, not a number.
UNTO_THE_ANVIL_PROSE = (
    "While this model is leading a unit, each time a\xa0model in that unit makes a "
    "melee attack, you can re-roll the\xa0Wound roll."
)


class TestParseTransportCapacity:
    """The capacity parser is the engine's single source of computation.

    Tests feed real merged prose and assert the parsed headline number; they
    do not re-implement the regex.
    """

    @pytest.mark.parametrize("prose, expected", [
        (LAND_RAIDER_PROSE, 12),
        (IMPULSOR_PROSE, 7),
        (REPULSOR_EXECUTIONER_PROSE, 7),
        (STORMRAVEN_GUNSHIP_PROSE, 12),
        (RHINO_PROSE, 12),
    ])
    def test_real_merged_prose(self, prose, expected):
        assert parse_transport_capacity(prose) == expected

    def test_stormraven_first_number_after_of(self):
        """Stormraven prose leads with '12 ... Infantry models and 1 Dreadnought'
        — the headline capacity is the first number after 'transport capacity of'."""
        assert parse_transport_capacity(STORMRAVEN_GUNSHIP_PROSE) == 12

    def test_none_input(self):
        assert parse_transport_capacity(None) is None

    def test_empty_string(self):
        assert parse_transport_capacity("") is None

    def test_non_transport_ability_description(self):
        assert parse_transport_capacity(UNTO_THE_ANVIL_PROSE) is None

    def test_no_prose_string(self):
        assert parse_transport_capacity("no capacity prose here") is None

    def test_unit_count_capacity_is_refused(self):
        """Night Scythe carries ONE UNIT, not one model — a unit-count capacity
        must not be fed into a model-count metric as a false '1'."""
        assert parse_transport_capacity(NIGHT_SCYTHE_PROSE) is None

    def test_unit_count_capacity_with_model_word_still_parses(self):
        """Guard must not reject prose that legitimately counts models after
        the number even if 'unit' appears elsewhere."""
        assert parse_transport_capacity(
            "This model has a transport capacity of 12 Foo models which you "
            "can keep inside one unit."
        ) == 12


class TestComputeMobTransportKeys:
    """compute_mob must surface the parsed capacity and TRANSPORT flag."""

    def test_transport_capacity_n_parsed(self):
        mob = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport"], transport_capacity=LAND_RAIDER_PROSE,
        )
        assert mob["transport_capacity_n"] == 12
        assert mob["is_transport"] is True
        # Raw prose preserved for callers that want the full text.
        assert mob["transport_capacity"] == LAND_RAIDER_PROSE

    def test_no_capacity_stays_none(self):
        mob = compute_mob(movement=10, fly=False, deep_strike=False, oc=1,
                          keywords=["Vehicle", "Transport"])
        assert mob["transport_capacity_n"] is None
        assert mob["is_transport"] is True  # keyword flag is independent of prose

    def test_non_transport_stays_false(self):
        mob = compute_mob(movement=10, fly=False, deep_strike=False, oc=1,
                          keywords=["Vehicle"])
        assert mob["is_transport"] is False
        assert mob["transport_capacity_n"] is None


class TestDeliveryBonus:
    """Delivery component gates: TRANSPORT keyword AND numeric capacity > 0."""

    def test_transport_with_capacity_positive(self):
        mob = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport"], transport_capacity=LAND_RAIDER_PROSE,
        )
        assert RankingEngine.delivery_bonus(mob) > 0.0

    def test_without_transport_keyword_zero(self):
        mob = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle"], transport_capacity=LAND_RAIDER_PROSE,
        )
        assert RankingEngine.delivery_bonus(mob) == 0.0

    def test_transport_with_null_capacity_zero(self):
        mob = compute_mob(movement=10, fly=False, deep_strike=False, oc=1,
                          keywords=["Vehicle", "Transport"])
        assert RankingEngine.delivery_bonus(mob) == 0.0

    def test_unit_count_capacity_unit_stays_keyword_tier(self):
        """Night Scythe: '1 NECRONS INFANTRY unit' is not 1 model — the parsed
        capacity stays None and the unit gets no false delivery bonus."""
        mob = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport", "Fly"],
            transport_capacity=NIGHT_SCYTHE_PROSE,
        )
        assert mob["transport_capacity_n"] is None
        assert RankingEngine.delivery_bonus(mob) == 0.0

    def test_old_style_dict_without_key_zero(self):
        """Backcompat: mob dicts without transport_capacity_n must yield 0.0."""
        mob = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport"], transport_capacity=LAND_RAIDER_PROSE,
        )
        old = dict(mob)
        old.pop("transport_capacity_n")
        old.pop("is_transport")
        assert RankingEngine.delivery_bonus(old) == 0.0

    def test_deep_strike_transport_delivery_is_movement_independent(self):
        """One-shot arrival (DEEP STRIKE) drops the movement-speed term:
        same hull + same capacity must deliver identically at M6 and M14."""
        slow = compute_mob(
            movement=6, fly=False, deep_strike=True, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=DROP_POD_PROSE,
        )
        fast = compute_mob(
            movement=14, fly=False, deep_strike=True, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=DROP_POD_PROSE,
        )
        assert RankingEngine.delivery_bonus(slow) == RankingEngine.delivery_bonus(fast)
        assert RankingEngine.delivery_bonus(slow) > 0.0

    def test_deep_strike_capacity_still_counts(self):
        """DS does not zero the capacity credit — a 12-cap pod still delivers
        more than a 7-cap pod, just without the speed term."""
        big = compute_mob(
            movement=6, fly=False, deep_strike=True, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=DROP_POD_PROSE,
        )
        small = compute_mob(
            movement=6, fly=False, deep_strike=True, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=IMPULSOR_PROSE,
        )
        assert RankingEngine.delivery_bonus(big) > RankingEngine.delivery_bonus(small)

    def test_shuttling_transport_outranks_same_capacity_drop_pod(self):
        """A Rhino with the same 12-capacity shuttles bodies all game; a Drop
        Pod delivers once. The shuttler must score higher on delivery than the
        one-shot arrival (which is capped at the static floor)."""
        pod = compute_mob(
            movement=6, fly=False, deep_strike=True, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=DROP_POD_PROSE,
        )
        rhino = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=0,
            keywords=["Vehicle", "Transport"], transport_capacity=RHINO_PROSE,
        )
        assert RankingEngine.delivery_bonus(rhino) > RankingEngine.delivery_bonus(pod)


class TestMobScoreIntegration:
    """mob_score uses the delivery component; non-transports are byte-stable."""

    def test_transport_with_capacity_outscores_same_hull_no_capacity(self):
        with_cap = compute_mob(
            movement=10, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport"], transport_capacity=LAND_RAIDER_PROSE,
        )
        without_cap = compute_mob(movement=10, fly=False, deep_strike=False, oc=1,
                                  keywords=["Vehicle", "Transport"])
        assert RankingEngine.mob_score(with_cap) > RankingEngine.mob_score(without_cap)

    def test_transport_score_stays_within_clamp(self):
        mob = compute_mob(
            movement=12, fly=False, deep_strike=False, oc=1,
            keywords=["Vehicle", "Transport"], transport_capacity=LAND_RAIDER_PROSE,
        )
        score = RankingEngine.mob_score(mob)
        assert 0 <= score <= 100


class TestRankingIntegration:
    """Structural end-to-end: merged prose reaches the ranked mob dict.

    No score-value assertions here — byte-stability is covered by the full
    suite and the findings diff (parent's step).
    """

    def test_land_raider_ranked_with_transport_metadata(self):
        engine = RankingEngine("space-marines")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq)
        lr = next((r for r in results if r["name"] == "Land Raider"), None)
        assert lr is not None, "Land Raider must be in space-marines ranking"
        mob = lr["mob"]
        assert isinstance(mob.get("transport_capacity"), str)
        assert mob["transport_capacity"].strip() != ""
        assert mob["transport_capacity_n"] == 12
        assert mob["is_transport"] is True

    def test_all_keyworded_transports_carry_the_flags(self):
        """Every TRANSPORT-keyword unit exposes is_transport and a raw
        transport_capacity field (None when prose absent — Encoding B gap)."""
        engine = RankingEngine("space-marines")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq)
        transports = [r for r in results if r["mob"].get("is_transport")]
        assert transports, "no TRANSPORT units found in space-marines ranking"
        for r in transports:
            mob = r["mob"]
            assert "transport_capacity" in mob
            assert "transport_capacity_n" in mob