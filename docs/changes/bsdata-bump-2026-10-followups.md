# BSData bump 2026-10-17 — leftover validator classes (follow-up)

Branch: `chore/bump-bsdata-2026-10-17` (bsdata `cc58ee3` → `9b8207c`).
Validator runs: baseline `/tmp/opencode/valid-baseline.txt` (main, 246 unique / 439 occ / 48 HIGH),
post-bump `/tmp/opencode/valid-after-todo2.txt` (242 unique / 454 occ / 44 HIGH).

This bump applied only **exactly-1-candidate** weapon renames (110 sites / 79 unit entries,
config old name not in that unit's merged weapons + exactly one merged name missing from config).
Everything below was left untouched: either the candidate set is ambiguous, the class needs
archaeology, or it is a pre-existing validator↔loader gap.

## Leftover classes (occurrence / unique-name counts, post-bump)

| Severity | Class | Occ | Unique names | Notes |
|----------|-------|-----|--------------|-------|
| HIGH | NOT IN DATA | 68 | 38 | Top: `Grenade Launcher` ×9 (A5 known gap — loader partial-matches fine, validator exact-match fails; fix-forward in `adapter/bsdata_parser_11e.py:38 _BOOK_WEAPON_NAMES` or validator `_base_name`), `Thunderhawk cluster bombs` ×7, `Lascannon` ×5 |
| HIGH | GROUP CAP | 5 | 5 | Skitarii data-tether/omnispex, Kroot Farstalker — pre-existing |
| HIGH | ALLOC CAP | 4 | 4 | Purifier, Kroot Farstalker, Warlock ×2 — pre-existing |
| MEDIUM | EXTRA WEAPON | 195 | 84 | Config weapon not in BSData choices — mostly curated builds that intentionally predate or extend merged choices; needs per-unit archaeology before touching |
| MEDIUM | MISSING FIXED RANGED | 108 | 58 | Ambiguous (1 old, >1 new candidate) + multi-old sets left un-renamed |
| MEDIUM | MISSING FIXED MELEE | 72 | 51 | Same as above |
| LOW | MISSING FIXED RANGED | 2 | 1 | Same |

## Un-applied rename candidates (measured, not applied)

- **26 ambiguous** (exactly 1 old name, >1 merged candidates) — e.g. `Apothecary` CCW →
  {Reductor Pistol, Servo-armature}, `Captain` CCW → 3 combined-profile names,
  `Lieutenant` CCW → 4 candidates, `Firestrike Servo-Turrets` CCW → {Firestrike Servo-Turret,
  Hovering Bulk} (attached-model names, not weapons — validator artefact).
- **123 multi-old** (>1 old name per unit/type) — top old names: `Icarus Rocket Pod` ×15,
  `Ironhail Heavy Stubber` ×15, `Armoured hull` ×14, `defensive array` ×14,
  `ironhail heavy stubbers` ×12, `Master-crafted bolter` ×11, `Plasma pistol - standard` ×11,
  `Storm bolter` ×11. Mostly Gladiator/vehicle families with several case-variant old names
  mapping onto a small merged set — needs 1:N mapping decisions, not blind renames.

## Method for the next pass

1. Per unit, list old config names + merged names (same type).
2. Archaeology: newrecruit/wahapedia to confirm which merged name each old name became
   (case-only merges are safe mechanically; semantic merges need evidence).
3. Apply only where the mapping is provably 1:1; ambiguous sets go to curation review.
4. Re-run `python3 scripts/validate_configs_vs_bsdata.py --all` and full pytest after each batch.
