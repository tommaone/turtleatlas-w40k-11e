"""Tests that all character configs use the slots schema.

Every character in characters.json must have weapon_options with builds array.
Fixed-loadout characters get a single build with all weapons as fixed and an
empty slots list. Characters with wargear choices get proper typed slots.

Locked schema (converted from legacy ranged/melee/choices — see
scripts/migrate_characters_to_slots.py):
    {name, fixed: [{name, type}], slots: [{name, choices: [{name, type, count?}]}],
     no_duplicates?: bool}

Legacy keys (ranged, melee, ranged_choices, melee_choices, max_ranged,
max_melee) are FORBIDDEN.

Run: python3 -m pytest tests/test_characters_builds_format.py -v
"""

import json
import os
from pathlib import Path

import pytest

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"

# Collect all faction character files
FACTIONS = sorted(
    d.name for d in CONFIG_DIR.iterdir()
    if d.is_dir() and (d / "characters.json").exists()
)


def _load_characters(faction: str) -> dict:
    p = CONFIG_DIR / faction / "characters.json"
    with open(p) as f:
        return json.load(f)


def _has_builds(cfg: dict) -> bool:
    return "weapon_options" in cfg and "builds" in cfg.get("weapon_options", {})


def _build_count(cfg: dict) -> int:
    return len(cfg.get("weapon_options", {}).get("builds", []))


def _has_fixed_weapons(cfg: dict) -> bool:
    """Character has ranged or melee lists (flat format)."""
    return bool(cfg.get("ranged")) or bool(cfg.get("melee"))


class TestAllCharactersHaveBuildsFormat:
    """Every character must use weapon_options.builds, not flat ranged/melee lists."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_all_characters_have_builds(self, faction):
        chars = _load_characters(faction)
        failures = []
        for name, cfg in chars.items():
            if name.startswith("_"):
                continue
            if not _has_builds(cfg):
                failures.append(name)
        assert not failures, (
            f"{faction}: {len(failures)} characters without builds format: {failures}"
        )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_no_flat_ranged_melee_lists(self, faction):
        """Flat ranged/melee lists are forbidden — use builds instead."""
        chars = _load_characters(faction)
        failures = []
        for name, cfg in chars.items():
            if name.startswith("_"):
                continue
            if _has_fixed_weapons(cfg) and not _has_builds(cfg):
                failures.append(name)
        assert not failures, (
            f"{faction}: {len(failures)} chars have flat ranged/melee without builds: {failures}"
        )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_every_build_has_slots_schema(self, faction):
        """Slots schema is MANDATORY: every build has fixed + slots; legacy
        ranged/melee/choices keys are forbidden."""
        chars = _load_characters(faction)
        required = {"fixed", "slots"}
        optional = {"name", "no_duplicates"}
        legacy = {"ranged", "melee", "ranged_choices", "melee_choices",
                  "max_ranged", "max_melee"}
        for name, cfg in chars.items():
            if name.startswith("_"):
                continue
            if not _has_builds(cfg):
                continue
            for i, build in enumerate(cfg["weapon_options"]["builds"]):
                keys = set(build.keys())
                assert required.issubset(keys), (
                    f"{faction}/{name} build[{i}]: missing required {required}, got {keys}"
                )
                legacy_present = legacy & keys
                assert not legacy_present, (
                    f"{faction}/{name} build[{i}]: legacy keys present {legacy_present} — "
                    f"slots schema is mandatory (see scripts/migrate_characters_to_slots.py)"
                )
                extra = keys - required - optional
                assert not extra, (
                    f"{faction}/{name} build[{i}]: unexpected keys {extra}"
                )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_builds_have_at_least_one_weapon(self, faction):
        chars = _load_characters(faction)
        merged_path = Path(__file__).resolve().parent.parent / "data" / "merged" / f"{faction}.json"
        merged_weapons = {}
        if merged_path.exists():
            with open(merged_path) as f:
                merged = json.load(f)
            for u in merged.get("units", []):
                profile = u.get("profile") or {}
                wpns = profile.get("weapons", [])
                merged_weapons[u["name"]] = len(wpns)

        for name, cfg in chars.items():
            if name.startswith("_"):
                continue
            if not _has_builds(cfg):
                continue
            for i, build in enumerate(cfg["weapon_options"]["builds"]):
                # Count weapons from slots schema (fixed + slots)
                total = len(build.get("fixed", []))
                for slot in build.get("slots", []):
                    for c in slot.get("choices", []):
                        # Skip Crusade/upgrade entries that aren't real weapons
                        cn = c.get("name", "").lower()
                        if "weapon modification" in cn or "crusade relic" in cn:
                            continue
                        total += 1
                # Allow zero weapons if merged data also has zero (BSData gap)
                merged_count = merged_weapons.get(name, -1)
                if total == 0 and merged_count == 0:
                    continue
                assert total > 0, (
                    f"{faction}/{name} build[{i}]: has zero weapons"
                )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_no_duplicate_build_names(self, faction):
        chars = _load_characters(faction)
        for name, cfg in chars.items():
            if name.startswith("_"):
                continue
            if not _has_builds(cfg):
                continue
            builds = cfg["weapon_options"]["builds"]
            names = [b.get("name", f"build_{i}") for i, b in enumerate(builds)]
            dupes = [n for n in names if names.count(n) > 1]
            assert not dupes, (
                f"{faction}/{name}: duplicate build names {set(dupes)}"
            )
