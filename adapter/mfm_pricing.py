"""Canonical MFM price-tier selection.

MFM lists some units more than once: the second entry carries `groupTitle`
— the sub-group the unit happens to be listed under — at a different rate.
Per `mfm/specs/data-model.md:84`, groupTitle is *omitted for the base
roster*, so the entry WITHOUT groupTitle is the unit's base price and the
group entry is an opt-in tier.

imperial-agents is the only file where both exist (29 units, 14 with
divergent rates). A plain last-wins `name -> unit` map charges the opt-in
tier as the base price, which overstates points and understates
DPP-per-point — and that number reaches MCP answers.

Every consumer that needs "the price of this MFM unit" must go through
here, or the copies drift apart again. Routed through this module:

- `adapter/merge.py`                    — the merged dataset
- `scripts/audit_curated_vs_bsdata.py`  — the audit oracle (via `base_points`)

Still carrying their own copy of the rule (same outcome today, but nothing
keeps it that way): `scripts/sync_config_pts.py` (the sanctioned config
writer), `tests/test_config_points_match_mfm.py` (the config guard).

Callers normalise names with their own `_norm`, so keying here stays on the
original MFM name.
"""


def iter_base_entries(units):
    """Yield (name, unit) once per unit name, preferring the plain entry.

    Falls back to a groupTitle entry only when no plain entry exists, which
    is load-bearing: 11 factions carry 390 entries under a sub-group title
    ("Space Marines", Ynnari, Harlequins) and no plain entry of their own.
    Dropping the fallback collapses blood-angels from 83 merged units to 14.
    """
    plain, group = {}, {}
    for u in units or []:
        if not isinstance(u, dict):
            continue
        name = u.get("name")
        if not name:
            continue
        (group if u.get("groupTitle") else plain)[name] = u
    for name, u in plain.items():
        yield name, u
    for name, u in group.items():
        if name not in plain:
            yield name, u


def tier_costs(unit):
    """All priced cost rows for a unit, in MFM tier order."""
    return [c for pr in (unit.get("pricing") or [])
            for c in (pr.get("costs") or [])
            if c.get("points") is not None]


def base_points(units):
    """name -> first-tier points for each unit in `units`.

    The first cost row, matching how adapter/merge.py and
    scripts/sync_config_pts.py read a base price.
    """
    out = {}
    for name, u in iter_base_entries(units):
        costs = tier_costs(u)
        if costs:
            out[name] = costs[0]["points"]
    return out
