"""Regression lock for the Knight Despoiler build inventory.

Locks the curated 13-build structure to the BSData truth (verified
2026-08-11 against the "Chaos - Chaos Knights Library" catalogue):

- Titanic feet is the innate CCW (min=1/max=1 in the BSData base entry) —
  present as a FIXED melee weapon in every build, never an arm slot.
- Every build carries two independent mount slots:
    Carapace weapon (top pintle):  Havoc missile pod / Ruinspear rocket pod /
                                   Hellstorm autocannons
    Shoulder weapon (left pintle): Diabolus heavy stubber / Daemonbreath meltagun
- Arm space (BSData):
    arm1 ("Replace reaper chainsword"): Reaper chainsword / Daemonbreath
        thermal cannon / gatling+darkflamer / battle+stubber
    arm2 ("Replace warpstrike claw"):  Warpstrike claw / Daemonbreath
        thermal cannon / gatling+darkflamer / battle+stubber
    13 unique arm sets. Arm bundles are SPLIT into component weapons in
    fixed (gatling+darkflamer, battle+stubber) — the bundle names resolve to
    only the primary profile, silently losing the secondary.

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_chaos_knights_despoiler_builds.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
CHAOS_KNIGHTS = CONFIG_DIR / "chaos-knights" / "characters.json"

# Canonical weapon names (as they appear in the merged catalogue)
TITANIC = "Titanic feet"
CHAIN = "Reaper chainsword"
CLAW = "Warpstrike claw"
THERMAL = "Daemonbreath thermal cannon"
GATLING = "Despoiler gatling cannon"
DARKFLAMER = "Heavy darkflamer"
BATTLE = "Despoiler battle cannon"
STUBBER = "Diabolus heavy stubber"
POD = "Havoc missile pod"
ROCKET_POD = "Ruinspear rocket pod"
AUTOCANNONS = "Hellstorm autocannons"
MELTAGUN = "Daemonbreath meltagun"

# Split arm bundles (the component weapons that must appear in fixed)
GATLING_BUNDLE = frozenset({GATLING, DARKFLAMER})
BATTLE_BUNDLE = frozenset({BATTLE, STUBBER})

# Legal arm weapons per arm (BSData "Replace ..." groups)
ARM1_OPTIONS = {CHAIN, THERMAL, *GATLING_BUNDLE, *BATTLE_BUNDLE}
ARM2_OPTIONS = {CLAW, THERMAL, *GATLING_BUNDLE, *BATTLE_BUNDLE}
ALL_LEGAL_ARMS = ARM1_OPTIONS | ARM2_OPTIONS

# Canonical inventory: build name -> its arm-set (fixed weapons minus Titanic feet)
EXPECTED_BUILDS = {
    "melee_dual": frozenset({CHAIN, CLAW}),
    "gatling_one_arm": frozenset({*GATLING_BUNDLE, CLAW}),
    "battle_cannon_one_arm": frozenset({*BATTLE_BUNDLE, CLAW}),
    "gatling_dual": frozenset({*GATLING_BUNDLE, *GATLING_BUNDLE}),
    "battle_cannon_dual": frozenset({*BATTLE_BUNDLE, *BATTLE_BUNDLE}),
    "gatling_plus_battle": frozenset({*GATLING_BUNDLE, *BATTLE_BUNDLE}),
    "chain_gatling": frozenset({CHAIN, *GATLING_BUNDLE}),
    "chain_battle": frozenset({CHAIN, *BATTLE_BUNDLE}),
    "thermal_one_arm": frozenset({THERMAL, CLAW}),
    "chain_thermal": frozenset({CHAIN, THERMAL}),
    "thermal_dual": frozenset({THERMAL, THERMAL}),
    "gatling_thermal": frozenset({*GATLING_BUNDLE, THERMAL}),
    "battle_thermal": frozenset({*BATTLE_BUNDLE, THERMAL}),
}

CARAPACE_EXPECTED = {POD, ROCKET_POD, AUTOCANNONS}
SHOULDER_EXPECTED = {STUBBER, MELTAGUN}

# Sample targets for resolvability checks (GEQ horde, MEQ elite, Knight vehicle)
TARGET_SAMPLES = ["GEQ", "MEQ", "Knight"]


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("chaos-knights")


@pytest.fixture(scope="module")
def builds(engine):
    chars = json.load(open(CHAOS_KNIGHTS))
    return chars["Knight Despoiler"]["weapon_options"]["builds"]


def _build_weapons(build) -> set[str]:
    """All weapon names named by a build (fixed + slot choices)."""
    names = {f["name"] for f in build.get("fixed", [])}
    for slot in build.get("slots", []):
        names.update(c["name"] for c in slot.get("choices", []))
    return names


def _resolve(engine, build):
    """Resolve one build via the engine's slots path -> (ranged, melee) names."""
    r, m, _n = engine._resolve_slots_build(build, "Knight Despoiler",
                                           engine.resolve_target("MEQ"))
    return [w.name for w in r], [w.name for w in m]


class TestDespoilerBuildInventory:
    """The 13 builds exist with the exact canonical names — no drift."""

    def test_exact_build_names(self, builds):
        names = [b["name"] for b in builds]
        assert names == list(EXPECTED_BUILDS.keys()), (
            f"build inventory drifted: {names}"
        )

    def test_all_builds_use_slots_schema(self, builds):
        for b in builds:
            assert {"fixed", "slots"}.issubset(b.keys()), f"{b['name']}: no slots schema"
            legacy = {"ranged", "melee", "ranged_choices", "melee_choices",
                      "max_ranged", "max_melee"} & set(b.keys())
            assert not legacy, f"{b['name']}: legacy keys {legacy}"

    def test_titanic_feet_fixed_in_every_build(self, builds):
        """Innate CCW (min=1/max=1 on the BSData base) — fixed, never an arm slot."""
        for b in builds:
            feet = [f for f in b.get("fixed", [])
                    if f["name"] == TITANIC and f.get("type") == "melee"]
            assert feet, f"{b['name']}: Titanic feet missing from fixed"
            choices = {c["name"] for s in b.get("slots", []) for c in s["choices"]}
            assert TITANIC not in choices, f"{b['name']}: Titanic feet in a slot"


class TestDespoilerMountSlots:
    """Carapace (top) and Shoulder (left) are independent mounts on every build."""

    def test_every_build_has_both_mount_slots(self, builds):
        for b in builds:
            slots = {s["name"]: {c["name"] for c in s["choices"]} for s in b["slots"]}
            assert slots.get("Carapace weapon") == CARAPACE_EXPECTED, (
                f"{b['name']}: carapace slot = {slots.get('Carapace weapon')}"
            )
            assert slots.get("Shoulder weapon") == SHOULDER_EXPECTED, (
                f"{b['name']}: shoulder slot = {slots.get('Shoulder weapon')}"
            )

    def test_mounts_never_conflated(self, builds):
        """No slot may mix carapace and shoulder options (the old 5-way slot)."""
        carapace_and_shoulder = CARAPACE_EXPECTED | SHOULDER_EXPECTED
        for b in builds:
            for s in b["slots"]:
                choices = {c["name"] for c in s["choices"]}
                assert choices != carapace_and_shoulder, (
                    f"{b['name']}: slot '{s['name']}' conflates both mounts"
                )


class TestDespoilerArmSpace:
    """Fixed arms cover the BSData arm space — all 13 legal arm sets, no extras."""

    def test_arm_sets_match_canonical_inventory(self, builds):
        by_name = {b["name"]: b for b in builds}
        for name, expected_arms in EXPECTED_BUILDS.items():
            b = by_name.get(name)
            assert b is not None, f"build '{name}' missing"
            arms = frozenset(f["name"] for f in b.get("fixed", []) if f["name"] != TITANIC)
            assert arms == expected_arms, (
                f"{name}: fixed arms {arms} != expected {expected_arms}"
            )

    def test_every_arm_is_legal(self, builds):
        """Each build's arms must be drawable from arm1/arm2 BSData options."""
        all_legal = ARM1_OPTIONS | ARM2_OPTIONS
        for b in builds:
            arms = {f["name"] for f in b.get("fixed", []) if f["name"] != TITANIC}
            assert arms <= ALL_LEGAL_ARMS, f"{b['name']}: illegal arm {arms - ALL_LEGAL_ARMS}"

    def test_full_arm_space_covered(self, builds):
        """The 13 builds must reference every legal arm weapon at least once."""
        referenced = set()
        for b in builds:
            referenced |= {f["name"] for f in b.get("fixed", []) if f["name"] != TITANIC}
        assert referenced == ALL_LEGAL_ARMS, (
            f"arm space not fully covered; missing {ALL_LEGAL_ARMS - referenced}"
        )


class TestDespoilerResolvability:
    """Every named weapon resolves; resolved loadouts keep their fixed weapons
    (the slots path silently drops unresolvable fixed entries — this catches it)."""

    def test_all_weapon_names_resolve(self, engine, builds):
        for b in builds:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name="Knight Despoiler")
                except KeyError:
                    pytest.fail(f"{b['name']}: weapon '{name}' does not resolve")

    def test_melee_dual_keeps_both_melee_arms(self, engine, builds):
        b = next(x for x in builds if x["name"] == "melee_dual")
        ranged, melee = _resolve(engine, b)
        assert len(ranged) == 2, f"melee_dual ranged: {ranged}"
        assert len(melee) == 3, f"melee_dual melee: {melee}"
        assert any(m == TITANIC for m in melee)
        assert any(m.startswith(CHAIN) for m in melee)
        assert any(m.startswith(CLAW) for m in melee)

    def test_gatling_dual_keeps_both_bundles(self, engine, builds):
        b = next(x for x in builds if x["name"] == "gatling_dual")
        ranged, melee = _resolve(engine, b)
        assert len(ranged) == 6, f"gatling_dual ranged: {ranged}"
        assert len(melee) == 1 and melee[0] == TITANIC, f"gatling_dual melee: {melee}"

    def test_thermal_arms_resolvable_per_target(self, engine, builds):
        """The thermal arm must be reachable on a vehicle target."""
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout("Knight Despoiler", engine.resolve_target(t))
            assert res is not None, f"no loadout for {t}"
            _pts, ranged, melee, _inn, _info = res
            all_names = [w.name for w in ranged + melee]
            assert len(ranged) >= 2, f"{t}: missing carapace+shoulder weapons: {all_names}"
            assert len(melee) >= 1, f"{t}: no innate melee"
            assert TITANIC in all_names, f"{t}: Titanic feet missing"
