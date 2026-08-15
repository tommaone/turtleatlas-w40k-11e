#!/usr/bin/env python3
"""Inventory: what would the caps mechanism change in each committed config?

Runs make_build (single source of truth) for every unit in every alloc-layer
faction and reports, per unit, the alloc variants whose committed max/group_max
differ from the mechanism, plus slot choices the mechanism would add/remove.
Pure read-only — writes nothing.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from adapter.bsdata_parser_11e import BSDataParser11e
from gen_squad_composition import fuzzy_find_composition, make_build

FACTIONS = sys.argv[1:] or ["aeldari", "black-templars", "blood-angels",
                            "dark-angels", "deathwatch", "grey-knights",
                            "orks", "space-marines", "space-wolves"]

parser = BSDataParser11e(str(REPO / "bsdata"))


def _slot_diffs(owner: str, cur, exp) -> list[str]:
    """Slot-choice diffs between a current model/variant and its expected
    counterpart. `cur`/`exp` are dicts carrying an optional 'slots' list."""
    out = []
    for slot in cur.get("slots", []) or []:
        exp_slot = next(
            (s for s in (exp.get("slots") or []) if s["name"] == slot["name"]), None
        )
        if exp_slot is None:
            out.append(f"-slot {owner}:{slot['name']}")
            continue
        exp_names = {c.get("name") for c in exp_slot.get("choices", [])}
        cur_names = {c.get("name") for c in slot.get("choices", [])}
        if exp_names != cur_names:
            only_exp = sorted(exp_names - cur_names)
            only_cur = sorted(cur_names - exp_names)
            if only_exp:
                out.append(f"+{owner}:{slot['name']} choices {only_exp}")
            if only_cur:
                out.append(f"-{owner}:{slot['name']} choices {only_cur}")
    return out


for faction in FACTIONS:
    comps = parser.extract_squad_composition(faction)
    path = REPO / "data" / "config" / faction / "squads.json"
    squads = json.loads(path.read_text())
    print(f"\n=== {faction} ===")
    for unit_name, unit_cfg in squads.items():
        if unit_name.startswith("_"):
            continue
        comp = fuzzy_find_composition(comps, unit_name)
        if not comp:
            continue
        build = make_build(unit_cfg, comp, faction, unit_name)
        if build is None:
            print(f"  {unit_name}: SKIPPED by generator")
            continue
        actual_models = (unit_cfg.get("builds") or [{}])[0].get("models", [])
        exp_models = build.get("models", [])
        diffs = []
        # map expected alloc variants
        exp_alloc = {}
        for em in exp_models:
            for ev in em.get("alloc", []):
                exp_alloc[ev["name"]] = ev
        cur_alloc = {}
        for am in actual_models:
            for av in am.get("alloc", []):
                cur_alloc[av["name"]] = av
        for name, ev in exp_alloc.items():
            av = cur_alloc.get(name)
            if av is None:
                diffs.append(f"+variant {name} max={ev.get('max')} g={ev.get('group_max')}")
                continue
            if av.get("max") != ev.get("max"):
                diffs.append(f"~{name} max {av.get('max')}->{ev.get('max')}")
            if (av.get("group_max") or 0) != (ev.get("group_max") or 0):
                diffs.append(f"~{name} group_max {av.get('group_max')}->{ev.get('group_max')}")
        for name in cur_alloc:
            if name not in exp_alloc:
                diffs.append(f"-variant {name}")
        # slot choice diffs for models present in both
        for am in actual_models:
            exp_m = next((e for e in exp_models if e["name"] == am["name"]), None)
            if exp_m is None:
                continue
            diffs += _slot_diffs(am["name"], am, exp_m)
            # alloc-variant slots too (the model-level loop misses variant
            # slots like the Terminator heavy-weapon melee slot)
            exp_alloc_by_name = {ev["name"]: ev for ev in (exp_m.get("alloc") or [])}
            for av in am.get("alloc", []) or []:
                exp_av = exp_alloc_by_name.get(av["name"])
                if exp_av is None:
                    continue
                diffs += _slot_diffs(f"{am['name']}:{av['name']}", av, exp_av)
        if diffs:
            print(f"  {unit_name}:")
            for d in diffs:
                print(f"    {d}")
