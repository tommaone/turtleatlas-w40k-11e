# Army Config Refresh Playbook

How to refresh any faction's config to the **builds format with modes** —
the repeatable recipe distilled from the Grey Knights conversion (squads,
vehicles, characters) and the vehicles.json shadow removal.

## Goal

Every unit in `data/config/<faction>/` resolves through the engine with:

1. **Builds format** — `builds: [{name, fixed, slots, ...}]` (or squad
   `builds: [{name, weapon, n}]`) instead of flat `ranged`/`melee` lists
2. **Modes** — `builds[].name` becomes a mode; `compute_ranking(mode=...)`
   filters each unit to its named build; multimodal units expose
   `modes`/`multimodal` in ranking results
3. **Correct pts** — every value verified against `mfm/data/<faction>.yaml`
   (MFM is the only source of truth for points; see the standing rule)
4. **11e-legal loadouts** — no duplicate gun choices on the same slot,
   correct slot counts per datasheet
5. **No shadowed files** — a unit lives in exactly ONE config file;
   `weapon_options.json` is authoritative for vehicles, `vehicles.json`
   is only a fallback for units with no builds

## When to run this

- New edition (11e → 12e etc.) — **all MFM points must be recalculated**
- A faction was auto-generated flat and never curated
- A faction has shadowed `vehicles.json` entries (same unit in both
  `vehicles.json` and `weapon_options.json`)
- Ranking output disagrees with your tabletop instinct (usually a data
  error, not an engine error)

## Phase 0 — Census

Before touching anything, know the state:

```bash
python3 - <<'EOF'
import json, glob
slug = "<faction>"
# weapon_options format census
wo = json.load(open(f'data/config/{slug}/weapon_options.json'))
units = {k: v for k, v in wo.items() if isinstance(v, dict) and not k.startswith('_')}
n_builds = sum(1 for v in units.values() if isinstance(v.get('builds'), list) and v['builds'])
n_flat = len(units) - n_builds
print(f'weapon_options: units={len(units)} builds_format={n_builds} flat={n_flat}')
# squads census
sq = json.load(open(f'data/config/{slug}/squads.json'))
sunits = {k: v for k, v in sq.items() if isinstance(v, dict) and not k.startswith('_')}
n_sb = sum(1 for v in sunits.values() if isinstance(v.get('builds'), list) and v['builds'])
n_legacy = sum(1 for v in sunits.values() if 'specials' in v and v.get('specials'))
print(f'squads: units={len(sunits)} builds={n_sb} legacy_specials={n_legacy}')
# shadow census
v = json.load(open(f'data/config/{slug}/vehicles.json'))
vunits = {k: x for k, x in v.items() if isinstance(x, dict) and not k.startswith('_')}
shadowed = [k for k in vunits if k in units]
only_v = [k for k in vunits if k not in units]
print(f'vehicles.json: units={len(vunits)} shadowed={len(shadowed)} only_in_vehicles={len(only_v)}')
EOF
```

Decision matrix:

| State | Action |
|-------|--------|
| builds in weapon_options + builds in squads + 0 shadowed | **done** — verify only |
| flat weapon_options | run `migrate_vehicle_builds.py` (see Phase 2) |
| legacy specials squads | manual curation (see Phase 3) — no script exists |
| shadowed vehicles.json | delete the shadowed entries (Phase 5) |

## Phase 1 — Verify the pipeline baseline

Run the full suite BEFORE changes and save the failure set. You compare
against this later:

```bash
python3 -m pytest --tb=no -q -rf 2>&1 | grep -E "^FAILED" | sed 's/ - .*//' | sort > /tmp/opencode/failures_before.txt
python3 -m pytest -q --tb=no 2>&1 | tail -1   # note the pass/fail counts
```

**The baseline failure set is expected to be non-empty** (pre-existing
non-GK failures). The rule: after your refresh, `diff failures_before.txt
failures_after.txt` must show **0 new failures**. Pre-existing failures
are NOT yours to fix in this ticket.

## Phase 2 — Regenerate from BSData

**WARNING — read this first.** The BSData constraint extractor
(`extract_wargear_constraints`) is INCOMPLETE for vehicles. Verified
losses on grey-knights: Thunderhawk 6 real weapons → 2 constraints,
Land Raider 6 → 1, Stormraven 9 → 3. The generator produces a SEED,
never a finished build set, and **running it on a curated faction
CLOBBERS the curated builds** (verified: GK Thunderhawk lost its
Lascannon + heavy cannon + twin heavy bolter build, replaced with a
single "Lascannon").

Rules:
- Run the generator ONLY as a first pass on legacy/flat configs
- NEVER re-run it on a faction that has curated builds — back it up
  first, and diff the result before accepting
- Always cross-check generated builds against the merged weapon list
  (the merged data has ALL weapons; the constraints do not)

```bash
python3 scripts/generate_configs_from_bsdata.py --faction <slug> --dry-run   # review
python3 scripts/generate_configs_from_bsdata.py --faction <slug>             # apply (seed only)
```

Then migrate flat vehicle configs to builds:

```bash
python3 scripts/migrate_vehicle_builds.py --faction <slug> --dry-run
python3 scripts/migrate_vehicle_builds.py --faction <slug>
```

**Gotchas learned the hard way:**

- The generators used to **dual-write every vehicle** to both
  `vehicles.json` and `weapon_options.json` — that is what created the
  shadow. Both generators are now fixed to write each vehicle to exactly
  ONE file (`weapon_options.json` if it has builds, `vehicles.json` as
  pure fallback). If you regenerate and see units appear in BOTH, stop —
  the generator regressed.
- `generate_vehicle_config()` produces builds at TOP LEVEL
  `{pts, info, builds: [...]}` — NOT nested under a `weapon_options` key.

## Phase 3 — Curate squads

The legacy squad format (`ranged`/`melee` + `specials`/`special_max`) does
not survive regeneration. Convert each squad to named builds.

**Bulk path (preferred):** `scripts/convert_squad_builds.py <slug>` converts
all legacy squads in a faction mechanically — no-option squads get a single
`Melee` build, special squads get `Melee` + one mode per special
(`Nx <special>`), with legacy `_eval_squad_variant` semantics preserved.
It also verifies MFM pts and weapon resolution (exit 2 on unresolved names).
`--all-legacy` runs every unconverted faction. After the bulk pass, hand-
curate only what the script flags or what the datasheet demands beyond the
legacy data (e.g. legal Mixed combos, apothecary slots, squads whose legacy
config was missing datasheet specials entirely).

**Manual path** (for squads the script can't express — datasheet facts below).

### 3a. Gather the datasheet facts

For each squad, load the Wahapedia/BSData datasheet and the expert file:

```bash
# expert file if one exists
cat resources/experts/<faction>.md
# BSData constraints for the squad (the generator used these)
python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from adapter.bsdata_parser_11e import BSDataParser11e
# FACTION_MAP in scripts/migrate_vehicle_builds.py has the BSData names
EOF
```

You need, per squad:
- **n** — how many models the pts covers
- **Special weapon allowance** — e.g. "2 per 5 models, 4 per 10"
- **What the special replaces** — e.g. "replaces storm bolter and Nemesis
  force weapon with special and Close combat weapon" (GK case)
- **Default loadout** — every model's base ranged + melee

### 3b. Build the modes

Each squad gets `builds: [{name, models: [{count, ranged, melee}]}]`. Each
model entry is one weapon-group; `count` is the number of models carrying
that loadout. The engine sums count × weapon per entry (see
`_eval_squad_build` in `engine/ranking.py`):

```json
"Strike Squad": {
  "pts": 115,
  "n": 5,
  "info": {...},
  "builds": [
    {"name": "Melee", "models": [
      {"count": 5, "ranged": "Storm bolter", "melee": "Nemesis force weapon"}
    ]},
    {"name": "Incinerator", "models": [
      {"count": 1, "ranged": "Incinerator", "melee": "Close combat weapon"},
      {"count": 4, "ranged": "Storm bolter", "melee": "Nemesis force weapon"}
    ]}
  ]
}
```

Mode conventions (curated, from the GK session):

| Squad | Modes |
|-------|-------|
| Squad with specials | `Melee`, one mode per special (`Nx <special>`), `Mixed` (if the datasheet allows a mix) |
| Squad with no options | single `Melee` build |
| Vehicles | curated archetypes with real names (`Anti-tank`, `Clearing`, `Greatsword + Psycannon + Incinerator`) — NOT generic "default" |
| Characters with options | named builds from BSData constraints |

**`count` is the number of models carrying that loadout, not the squad
size.** The engine multiplies each weapon entry by its count. A "Psycannon"
build on a 5-model squad is 1 model with Psycannon + 4 models with the
default loadout — the two model entries split the squad. The winning
build's DPP is per-model (total squad damage / n), so mixed entries are
the norm for squads with specials.

### 3c. Remove legacy fields

Once converted, delete `special_max`, `specials`, `sp_loses_*`,
`apoth_loses_*` from the squad entry. `builds` must be the last key.

## Phase 4 — Verify points against MFM

**Standing rule: all MFM points must always be recalculated when a new
edition hits.** MFM is the only source of truth for points.

```bash
python3 - <<'EOF'
import json, yaml
slug = "<faction>"
mfm = yaml.safe_load(open(f'mfm/data/{slug}.yaml'))
cfg = json.load(open(f'data/config/{slug}/weapon_options.json'))
# Compare cfg[unit]["pts"] against the MFM entry for the same unit
# (normalize names: lowercase, strip, normalize apostrophes)
EOF
```

Watch for units where the config pts and MFM pts disagree — the config
is wrong (e.g. GK Strike Squad was 120, MFM says 115; Rhino was 80 in
the shadowed file, MFM says 70).

## Phase 5 — Kill the shadow

Every unit must live in exactly ONE config file.

- If `weapon_options.json` has the unit with builds → the `vehicles.json`
  entry is shadowed. **Delete it** (or the whole file if all entries are
  shadowed — grey-knights had 19/19 shadowed, so the file was deleted).
- The engine (post-fix) treats `weapon_options.json` as authoritative in
  BOTH `resolve_loadout()` AND `get_unit_info()`. `vehicles.json` is only
  a fallback for units without builds.
- If a unit exists ONLY in `vehicles.json` (no builds), leave it there —
  that's the legitimate fallback case.

Verify after cleanup:

```bash
python3 - <<'EOF'
from engine.ranking import RankingEngine
eng = RankingEngine("<slug>")
print("vehicles dict empty:", len(eng.config.vehicles) == 0)
prof = {"stats": {}, "keywords": []}
print(eng.get_unit_info("<vehicle-name>", prof))  # must come from weapon_options
print(eng.resolve_loadout("<vehicle-name>", None if False else __import__("engine.gk_ranking", fromlist=["MEQ"]).MEQ)[0])  # pts
EOF
```

## Phase 6 — Verify modes in the engine

```bash
python3 - <<'EOF'
from engine.gk_ranking import compute_ranking  # or the faction's ranking module
res = compute_ranking()
for r in res:
    if r.get("multimodal"):
        print(r["name"], r["modes"])
# mode filter: each named mode must resolve
m = compute_ranking(mode="<mode-name>")
EOF
```

- Multimodal units must expose `modes` and `multimodal: true`
- `compute_ranking(mode=X)` must filter correctly; units lacking mode X
  stay unchanged (no-op filter)
- A mode name that doesn't exist must raise (direct API) or no-op (ranking)

## Phase 7 — Full test verification

```bash
python3 -m pytest --tb=no -q -rf 2>&1 | grep -E "^FAILED" | sed 's/ - .*//' | sort > /tmp/opencode/failures_after.txt
diff /tmp/opencode/failures_before.txt /tmp/opencode/failures_after.txt
```

Acceptable outcome: `diff` shows only PRE-EXISTING failures (may reorder
param keys — compare by test function, not `[keyN-cfgN]` suffix):

```bash
sed 's/\[.*\]//' failures_before.txt | sort -u > /tmp/opencode/fn_before.txt
sed 's/\[.*\]//' failures_after.txt  | sort -u > /tmp/opencode/fn_after.txt
diff /tmp/opencode/fn_before.txt /tmp/opencode/fn_after.txt   # must be empty
```

## Phase 8 — Commit discipline

One faction = one ticket = one commit (or a small scoped set). Never
bundle a faction refresh with engine changes or another faction.

```bash
git checkout -b fix/<faction>-builds-refresh
git add data/config/<faction>/ engine/<faction>_ranking.py  # scoped
git commit -m "fix: <faction> builds refresh — modes, MFM pts, shadow cleanup"
```

Ask before pushing. Never force-push. Take a backup branch before any
history rewrite.

## Checklist (ticket-scope)

```
1. ❌ Census run and recorded?
2. ❌ Baseline failure set saved?
3. ❌ Generators run — no dual-write regression?
4. ❌ All squads in builds format (no legacy specials)?
5. ❌ Modes named per convention (Melee/Nx special/Mixed, real archetypes)?
6. ❌ All pts verified against MFM (no edition leakage)?
7. ❌ 11e legality: no duplicate gun choices per slot?
8. ❌ Shadowed vehicles.json entries deleted (or whole file)?
9. ❌ get_unit_info + resolve_loadout verified for a sample vehicle?
10. ❌ Modes exposed + mode filter verified?
11. ❌ Full suite: 0 new failures vs baseline?
12. ❌ Single scoped commit, ask before push?
```

## Engine invariants (do not re-break)

These fixes from the GK session are load-bearing. If a future change
touches them, the playbook must be re-verified:

1. **`get_unit_info` precedence** — `weapon_options.json` is checked
   BEFORE `vehicles.json`; both share unified keyword logic (WALKER from
   `info.invuln`, DREADNOUGHT from name, DEEP STRIKE from info)
2. **`resolve_loadout` precedence** — `weapon_options` before `vehicles`
3. **Selection == ranking** — squad build selection uses `n_models=cfg["n"]`
   (legacy path) and `n_models=n` (`_best_squad_build`); the two paths
   must always agree, or melee-heavy lists underrank
4. **`Armoured hull` is melee type** — check the catalog, don't assume
   "hull = ranged"
5. **One formula, one source** — tests import engine functions; they
   never re-implement DPP math
6. **`_eval_squad_build` drops `innate`** — the builds path returns
   `innate: []`, so squads with squad-level innate weapons (e.g. GK
   Purifier's Purifying Flame) lose them when converted to builds format.
   Known gap from the GK conversion; fix the engine to carry
   `cfg["innate"]` through before converting such squads
