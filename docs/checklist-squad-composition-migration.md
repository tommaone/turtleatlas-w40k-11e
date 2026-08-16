# Squad Composition Migration — Checklist

How to migrate a faction's squad composition to the complex layer
(`alloc` parallel-variant greedy, `slots` wargear choices, `pool_min`
nested pools, multi-weapon fixed lists).

Two valid end-states (both let the engine pick the optimal loadout):

- **Generator + alloc** — `scripts/gen_squad_composition.py` writes one
  `Default` build; the engine distributes models across variants per
  target. Pilot: Aeldari.
- **Curated discrete builds** — human enumerates the legal loadouts
  (e.g. GK: Melee / Incinerator / Psycannon / Psilencer). Pilot: GK.

Decide per faction which end-state before running the generator —
the generator overwrites curated builds with a single `Default`+alloc.

## Checklist (per faction)

```
1. Pre-flight: verify slug → BSData catalogue mapping resolves to the
   faction's OWN catalogue. Known trap: drukhari slug fell through to
   Aeldari composition — would have written Aeldari data over Drukhari
   squads. Any faction whose extraction returns another faction's unit
   names is a blocker, not a migration.
2. python3 scripts/gen_squad_composition.py --faction X --dry-run
   → review replaced / skipped (parallel variants) / kept (no composition)
3. Curate by hand:
   - skipped units → build alloc payloads (parallel-variant models)
   - kept units → confirm existing builds are correct, or curate
4. --force to apply
5. python3 scripts/validate_configs_vs_bsdata.py --faction X
   → catalog/choice/max constraints
6. python3 scripts/validate_squad_configs.py --faction X
   → default-weapon & special-cap sanity
7. python3 -m pytest   (full suite)
8. Add per-faction complex-unit test file (mirror
   tests/test_aeldari_complex_units.py): assert STRUCTURE (alloc
   distribution, weapon names/counts, melee reduction), never damage
   values — one source of computation.
9. PYTHONHASHSEED=1 python3 scripts/gen_findings_html.py --faction X,
   then --index (must be seeded — unseeded runs flip tie-breaks and
   combo counts; verify diff scope == only factions whose configs
   changed this commit, else stale findings from a skipped regen)
10. Diff unit-name sets old vs new HTML before trusting a count change
    (Vyper lesson: a drop of 1 can be a removed phantom row or a real
    regression — identify the dropped unit first).
11. Commit + ask before push ("pushito").
```

## Blockers discovered 2026-08-06

1. **Drukhari slug fallback** — `extract_squad_composition('drukhari')`
   returned Aeldari's composition (46 units, identical names). Fixed by
   resolving the slug to the faction's own catalogue and treating a
   fallback as an error. Anrathe allied units are NOT modeled until they
   appear in the codex book.
2. **Cross-faction shared units (chaos god-marines)** — Noise/Plague/
   Rubric/Berzerkers were synced from god factions into CSM. If allies
   are not in the book, they are out: kicked from CSM raw data, sync
   map removed, guard test updated.

## Complexity scores (from BSData composition, 2026-08-06)

| Tier | Factions (score) |
|------|------------------|
| heavy | Space Wolves 354, Dark Angels 323, Blood Angels 322, Space Marines 299, Astra Militarum 273 |
| medium | Deathwatch 228, GSC/BT/IK/AdMech ~195, Drukhari 179, Sororitas 173, Chaos trio 157, Custodes 147 |
| light | Agents 122, Orks 84, Tau 80, Votann 56, TS 52, WE 51, DG 49, EC 43, Tyranids 35, Necrons 25 |

Scores sum parallel-variant (×3), mixed-model-type (×2), slot, pool_min
and multi-weapon-list units per faction. Aeldari = 179, GK = 163 — the
two completed factions at creation. Since then done: SM/DA/BA/SW + BT/DW
(2026-08-06→10), Chaos Daemons (2026-08-11), CSM/EC/Orks (2026-08-13),
and the 9-faction caps sweep (2026-08-15). The table is historical —
treat it as difficulty ranking, not a done/remaining list (see Migration
order below for the real status).

## Gotchas learned (BT/DW wave, 2026-08-10)

1. **min==1 is NOT always a leader** — `make_build` treated any model with
   `min == 1` as a leader (fixed count 1). The DW Deathwatch Terminator
   base model (`min: 1, max: 9` — "at least 1", not "exactly 1") consumed
   the whole squad budget as a "leader" and the squad resolved 2/5 models.
   Fix: a leader is `min == 1 AND max == 1`; a min==1 base model stays in
   the pool and its min counts toward the mandatory requirement. Verified
   behavior-neutral for all shipped factions (SM/DA/BA/SW/aeldari/GK).
2. **Characters that snuck into squads.json** — BT's Chaplain Grimaldus
   (n=1, points, info, builds) was filed under squads.json. Characters
   must live in characters.json with the `weapon_options.builds` schema
   (fixed + slots — legacy ranged/melee/choices keys are FORBIDDEN since
   2026-08-11, see scripts/migrate_characters_to_slots.py), not the squads
   `builds` schema. The two old plasma builds (Standard/Supercharge)
   collapse to one bare `"Plasma Pistol"` — the choice-profile max-over fix
   resolves it.
3. **Kept units still need curation** — DW's Decimus Kill Team was kept
   (no BSData composition) but its config was broken: the plasma swap was
   backwards (ranged 'Plasma pistol - Standard' / melee 'Plasma pistol -
   Supercharge' — a ranged weapon in the melee slot). Datasheet default is
   Plasma pistol + Power weapon. "Kept" is not "done" — review every kept
   unit's existing builds.
4. **Invader ATV false-positive class** — the Outrider Squad composition
   embeds the ATV (mount) as an alloc variant with a Bolt pistol wargear
   slot. The validator flags the ATV's weapons as EXTRA for Outrider
   Squad. Same class as the standalone ATV flag already accepted in
   SM/BA/SW — documented, not fixed.
5. **Legacy resolver ties are hash-order; slots are insertion-order** —
   the legacy build path dedups choices via a set comprehension
   (`all_options = list({opt for cl in ...})`), so in a DPP tie the
   winner follows CPython string-hash order. The slots schema iterates
   choices in config order. The 2026-08-11 slots migration flipped 16
   loadouts (Autarch Fusion Pistol→Gun, plasma supercharge→standard, etc.)
   — every flip was a zero-delta tie; optimal DPP unchanged. Diff
   legacy-vs-slots loadouts only counts as a regression if the chosen
   weapon's DPP differs by more than epsilon. Proof: A/B harness
   (`scripts/snapshot_char_loadouts.py` before/after +
   `scripts/compare_char_loadouts.py`).

## Migration order

### Done ✅

- **Pilot:** Aeldari (generator + alloc) and GK (curated discrete builds).
- **Wave 1 — big marine codexes:** Space Marines → Dark Angels → Blood
  Angels → Space Wolves (BA/SW parallelisable). Then Black Templars,
  Deathwatch. ✅ BT + DW done 2026-08-10 (30 BT squads replaced, 29 DW
  replaced + Decimus Kill Team curated; Grimaldus moved to characters;
  generator leader fix for min=1/max>1 base models).
- **Chaos Daemons book scoping + composition** (2026-08-11) — locked to the
  book roster (17 squads); builds exist, most daemons have no wargear
  variants so alloc pools aren't needed (fixed-wargear end-state is valid).
- **Wave 2 — CSM + EC + Orks** (2026-08-13): CSM slot migration (Fabius
  Bile 2-model character, choice weapons → group names), EC complex units,
  Orks generator one-way-substring fix + 10 regenerated / 7 kept.
- **Caps sweep on the 9 alloc-layer factions** (2026-08-15, commit
  `3370194`): aeldari/BT/BA/DA/DW/GK/orks/SM/SW regenerated through the caps
  mechanism (FLAT_CAPS + shared group_max) — validator issues strictly
  down, 8 stale tests corrected to datasheet truth.

### Next — Wave 3 (changed 2026-08-15, user decision)

- ~~Chaos Knights + Imperial Knights — slot-completion audit~~ ✅ DONE
  (2026-08-15, commits `2ca0b40` + `a33c65e`) — see Wave 3a below.
- **World Eaters — generator migration.** 10 squads, light tier (score 51):
  Bloodcrushers, Bloodletters, Chaos Spawn, Chaos Terminators (4 builds),
  Eightbound, Exalted Eightbound, Flesh Hounds, Goremongers (2 builds),
  Jakhals, Khorne Berzerkers. All flat builds today. Book-scope first (WE is
  a god-marine — the shared-units question from Wave 2 blockers was settled:
  sync map removed, roster = own MFM book).

**Commit + push the IK/CK batch BEFORE starting WE** (explicit user request,
2026-08-15).

### Wave 3a — IK/CK slot-completion audit ✅ (2026-08-15, commit `2ca0b40`)

Audit verdict: the 0-slot / discrete-build end-state is **correct as
shipped** — verified every in-scope unit against `extract_wargear_constraints`
+ raw BSData containers:

- **Castellan/Valiant** (2 builds each): BSData `Carapace-mounted Weapons`
  is a pick-1 group (min1/max1) with two bundles — 2 shieldbreakers + 1
  siegebreaker / 1 + 2. Both builds cover exactly those bundles, components
  split into fixed (they resolve; only the bundle names don't — documented
  gap, Despoiler precedent).
- **Tyrant** (4 builds): BSData Main weapons (pick-1: volcano+ecto /
  darkflame+harpoon) x Carapace weapons (pick-1: gheist-heavy / desecrator-
  heavy). The 4 builds cover all 2x2 combos. The parser's `count: 2` on the
  carapace choice is its flattening of the two SE bundles — raw group is
  min1/max1; config follows the raw.
- **Cerastus x4 (IK+CK)** + **Rampager/Ruinator/Abominant**: zero choice
  slots in BSData — fixed loadouts only; 0-slot end-state is correct.
- **Canis Rex / Defender / Magaera / Styrix**: already complete (2026-08-13).
  Canis Rex = Knight only (Hekhtur out); Defender/Canis Rex dual-profile
  guns already on group names.

Changes applied (all DPP-neutral, verified by before/after harness on
GEQ/MEQ/TEQ/Knight):

- Consolidated **profile-split melee entries to GROUP names** — the same
  double-entry class the IK `FORBIDDEN_PROFILES` lock forbids in ranged,
  leftover from the pre-slots pattern: IK Cerastus Lancer + CK Cerastus
  Acheron/Castigator/Lancer + CK Rampager + CK Ruinator. Melee is maxed so
  the pairs were harmless; group entries resolve with variants the engine
  maxes per target.
- **Cerastus Lancer (IK+CK)**: kept the ranged `Cerastus shock lance`
  profile (12" A6 S6 AP0 D2, Assault Sustained 2 — real 11e ranged profile;
  the CK parser models it ranged, IK parser models it melee; merged catalog
  has both).

New locks: 27 tests — IK `GROUP_NAMES` extended to all 3 Cerastus melee
units (so the no-profile-suffix + group-name tests now cover them) + new
`TestCerastusFixedBuilds` (IK) and `TestWave3CerastusAndMiscBuilds` (CK)
locking fixed inventories, slots==[], no ` - ` profile suffixes, resolution,
and the Lancer dual-profile ranged+melee shape.

Validator: IK 16 / CK 11 MEDIUM (unchanged, all accepted noise). Deterministic:
0 CRITICAL/MAJOR both factions. Full seeded suite: 3621 passed / 36 skipped /
1 xfailed.

### Wave 3b — World Eaters generator migration ✅ (2026-08-15, commit `81c3123`)

10 squads, light tier. `gen_squad_composition --faction world-eaters`
replaced 9 flat builds with composition builds; Jakhals kept curated (data
gap — BSData composition holds only the 2 Dishonoured variants, max 2 each,
no base Jakhal model, so budget 10 is inexpressible; stays flat Autopistol +
Chainblades x10).

Regenerated:
- **Bloodcrushers** (2 base Hellblade+Bladed horn + 1 Bloodhunter),
  **Bloodletters** (9 + Bloodreaper), **Chaos Spawn** (2), **Eightbound**
  (2 + champion), **Exalted Eightbound** (2 + champion, Chainblades — the
  old curated build said 'Close combat weapon'), **Flesh Hounds** (4 + 1
  Gore Hound — only the Gore Hound has Burning roar; the old flat build
  gave it to all 5), **Goremongers** (7 alloc: harpoon/2-pistols/chainblade
  + Blood Herald).
- **Chaos Terminators** (n=5): heavy-weapon alloc pool x4 — combi-bolter/
  weapon x accursed/chainfist/power-fist with shared group_max (chainfist
  1, power fist 3), paired accursed weapons, heavy weapon variant (flamer/
  autocannon slot) + Terminator Champion Weapons slot (paired accursed /
  combi-weapon / combi-bolter default).
- **Khorne Berzerkers** (n=10): base Chainblade alloc min5 max9 + 3 swap
  variants max2 each (eviscerator+bolt, eviscerator+plasma, chainblade+
  plasma) + Champion Pistol slot (bolt/plasma).

Validator noise dropped **36 → 21** (the old flat configs carried 15 HIGH
alloc-cap findings — the validator expects parallel-variant pools to be
alloc builds; all cleared). Remaining 21 = pre-existing vehicle/
weapon_options MEDIUM/LOW. Squad configs: 0 issues. Deterministic: 0.

**Parser fix (book-first weapon names):** WE's Bloodcrushers SE lives in
the linked Chaos Daemons catalogue, so composition carried the daemons-local
name `Juggernaut's bladed horn` — which does not resolve against the WE
catalog (book-first merge; WE book calls it `Bladed horn`, identical
profile A4 S6 AP-1 D1 Extra Attacks Lance). Added `_BOOK_WEAPON_NAMES` map
in `_parse_composition_model` so the generator emits the faction book's
name; regenerated squads reference `Bladed horn`. Regression tests:
`test_we_book_first_weapon_names` + `test_we_book_first_weapons_resolve`
(test_gen_squad_composition.py) + 14 locks in
tests/test_world_eaters_complex_units.py (structure-only, Jakhals kept,
all squads resolve per target).

Also removed the dead `'world-eaters': ['Jakhal']` KNOWN_MISSING entry
(test_unit_coverage_guard.py) — it was a singular/plural spelling mismatch;
'Jakhals' has always been in config.

Full seeded suite: **3636 passed / 36 skipped / 1 xfailed**.

### Later waves

- **Wave 4 — major non-marine:** Astra Militarum → Adeptus Mechanicus
  (moved from the original Wave 2 by the 2026-08-15 decision).
- **Wave 5 — remaining god-marines:** Death Guard → Thousand Sons (CSM + EC
  + WE handled; WE moved up to Wave 3).
- **Wave 6 — quick wins:** Necrons → Tyranids → Tau (Orks done in Wave 2;
  also gives the T3-benchmark factions engine attention).

Note on marine codexes: chapter catalogs are SM base + chapter addons
(verify overlap before treating BA/DA/SW scores as independent work —
see the marine-duplicity analysis in the session).

*Created 2026-08-06. Companion to docs/roadmap.md.*
