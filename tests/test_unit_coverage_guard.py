"""Guard: track merged units missing from config.

Every unit in merged data that is unique to one faction (not a cross-faction
ally like Knights/Assassins imported across many catalogues) should appear in
that faction's config (squads/weapon_options/characters/vehicles). If it
doesn't, it's either a curated model-variant (grouped into a parent config
unit) or a genuinely missing unit (a regression — like when DA's
characters.json was symlinked to SM and lost Lion El'Jonson).

KNOWN_MISSING lists the units confirmed missing at audit time. The test
fails if a NEW missing unit appears (not in the known list) — so a future
symlink/strip regression is caught immediately. Curating a unit and removing
it from KNOWN_MISSING is the expected path to shrink the list over time.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO / "data" / "merged"
CONFIG_DIR = REPO / "data" / "config"

# Confirmed-missing at audit time. Curate these → remove from this list.
KNOWN_MISSING: dict[str, list[str]] = {
    "adepta-sororitas": ["Celestian Sacresant (Anointed Halberd)", "Celestian Sacresant (Hallowed Mace)", "Geminae Superia", "Repentia Squad", "Sister Novitiate (Autogun)", "Sister Novitiate (Melee Weapon)"],
    "aeldari": ["Hand of the Archon", "Scourges with Heavy Weapons", "Scourges with Shardcarbines", "Vyper"],
    "black-templars": ["Librarian in Phobos Armour", "Librarian in Terminator Armour"],
    "chaos-daemons": ["Soul Grinder"],
    "chaos-titan-legions": ["Chaos Reaver Titan", "Chaos Warbringer Nemesis Titan", "Chaos Warhound Titan", "Chaos Warlord Titan"],
    "dark-angels": ["Land Speeder Vengeance", "Nephilim Jetfighter", "Ravenwing Command Squad", "Ravenwing Dark Talon", "Ravenwing Darkshroud"],
    "death-guard": ["Miasmic Malignifier", "Myphitic Blight-Haulers"],
    "deathwatch": ["Decimus Kill Team", "Indomitor Kill Team"],
    "drukhari": ["Avatar of Khaine", "Wraithknight with Ghostglaive"],
    "genestealer-cults": ["Centaur RSV", "Commissar Graves on Foot", "Death Korps of Krieg", "Gaunt\u2019s Ghosts", "Hippogriff AFV", "Parasite of Mortrex", "Von Ryan's Leapers"],
    "imperial-knights": ["Sydonian Dragoons with radium jezzails", "Sydonian Dragoons with taser lances"],
    "necrons": ["Convergence Of Dominion", "Tomb Citadel Walls"],
    "orks": ["Big\u2019Ed Bossbunka", "Burna Boy", "Loota", "Nob on Smasha Squig", "Runtherd", "Spanner", "Squighog Boy", "Squighog Boyz"],
    "space-marines": ["Adrax Agatone", "Aethon Shaan", "Caanok Var", "Captain Titus", "Cato Sicarius", "Chief Librarian Tigurius", "Darnath Lysander", "Iron Father Feirros", "Kayvaan Shrike", "Kor\u2019Sarro Khan", "Marneus Calgar In Armour Of Antilochus", "Pedro Kantor", "Roboute Guilliman", "Suboden Khan", "Tor Garadon", "Uriel Ventris", "Victrix Honour Guard", "Vulkan He\u2019Stan"],
    "space-wolves": ["Hunting Wolves", "Wolf Guard Headtakers", "Wolf Scout", "Wolf Scout Pack Leader", "Wolf Scout w/ haywire mine", "Wolf Scout w/ plasma gun", "Wolf Scout w/ runic stave and Thunderclap", "Wulfen"],
    "tau-empire": ["Tidewall Droneport", "Tidewall Gunrig", "Tidewall Shieldline"],
    "world-eaters": ["Jakhal"],
}


def _unit_factions():
    """Map unit name → set of faction ids it appears in (merged)."""
    uf = defaultdict(set)
    for mf in sorted(MERGED_DIR.glob("*.json")):
        fid = mf.stem
        for u in json.load(open(mf))["units"]:
            uf[u["name"]].add(fid)
    return uf


def _config_names(fid):
    names = set()
    fp = CONFIG_DIR / fid
    for sub in ("squads.json", "weapon_options.json", "characters.json", "vehicles.json"):
        p = fp / sub
        if not p.exists():
            continue
        for k, v in json.load(open(p)).items():
            if not str(k).startswith("_") and isinstance(v, dict):
                names.add(k)
    return names


def test_no_new_missing_units():
    """No new genuinely-missing units beyond the known audit list."""
    uf = _unit_factions()
    new_missing = []
    for unit, fids in uf.items():
        if len(fids) != 1 or unit.startswith("[") or "[Crucible]" in unit:
            continue
        fid = next(iter(fids))
        cfg = _config_names(fid)
        if unit in cfg:
            continue
        # skip model-variants covered by a parent config unit
        base = unit.split(" (")[0]
        if any(c.startswith(base) and c != unit for c in cfg):
            continue
        if unit in KNOWN_MISSING.get(fid, []):
            continue
        new_missing.append(f"{fid}/{unit}")

    if new_missing:
        pytest.fail(
            f"{len(new_missing)} NEW missing units (not in KNOWN_MISSING):\n"
            + "\n".join(f"  {m}" for m in new_missing)
            + "\n\nEither curate the config entry, or add to KNOWN_MISSING if "
            "intentionally excluded."
        )


def test_known_missing_still_tracked():
    """Known-missing units should still be absent from config (sanity: nobody
    curated a unit and forgot to remove it from KNOWN_MISSING)."""
    stale = []
    for fid, units in KNOWN_MISSING.items():
        cfg = _config_names(fid)
        for u in units:
            if u in cfg:
                stale.append(f"{fid}/{u}")
    if stale:
        pytest.fail(
            f"{len(stale)} known-missing units are NOW in config — remove from "
            f"KNOWN_MISSING:\n" + "\n".join(f"  {m}" for m in stale)
        )