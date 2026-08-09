# Feedback — Learned Rules (turtleatlas-w40k-11e)

Rules learned in real sessions. Newest at the bottom.

Format:
```
## Rule title
Short description.

**Why:** incident/pattern that generated it.
**How:** concrete application.
```

---

## MFM is the points source of truth
Points come from MFM (`mfm/`), stats/weapons from merged BSData (`data/merged/<faction>.json`). Never patch numbers by hand into configs.

**Why:** a one-time data patch becomes an unreviewable mystery; the pipeline is the fix point.
**How:** change the parser/generator, then regenerate configs. Data files are output, not input.

## One source of computation — no duplicated truth
Tests import the engine's functions; they never re-implement the math. No inline "expected damage" in tests.

**Why:** duplicated formulas produce false precision wars and drift undetected.
**How:** assert structure (keys, types, invariants like `len(melee) == n`), not damage values. If a number must be asserted, derive it by calling the same engine function.

## Dual-profile weapons resolve by list context
Singing Spear (Ranged + Melee) and Chainsabres (Melee + Ranged) share one catalog key. The loader selects the profile via `category="ranged"|"melee"`.

**Why:** the old first-profile convention dropped Warlocks' melee entirely (Warlocks must ALWAYS have a melee profile).
**How:** pass `category` at every load site; a dual weapon lands in BOTH lists. Config shows both: e.g. Chainsabres choice is `{"ranged": "Chainsabres", "melee": "Chainsabres"}`.

## Findings index.html is generated, never hand-edited
`scripts/gen_findings_html.py --index` rebuilds `findings/index.html` counts from the faction pages; `--all` regenerates it automatically.

**Why:** hand-maintained counts drifted (Aeldari 72 vs 71 after a config rename).
**How:** after any config/engine change that affects rankings, regenerate findings AND the index, then run `tests/test_findings_validation.py`.

## Config regeneration pipeline order
`gen_squad_composition.py` (or `generate_configs_from_bsdata.py`) → `validate_configs_vs_bsdata.py` → full pytest before commit.

**Why:** config and catalog names must align exactly; a KeyError in the validator means the config references a weapon/category missing from the merged catalog.
**How:** run in order, fix forward in the parser/engine — never patch the generated config by hand.

## workspace/ is scratch — never committed
`.gitignore` has `workspace/`. Scratch scripts and experiments live there and stay there.

## Config keys match catalog names exactly
The catalog name is canonical. A config key that doesn't match the catalog produces a phantom row or a silently-dropped unit.

**Why:** duplicate config keys → duplicate findings rows (the `Vyper`/`Vypers` 72→71 cleanup); missing key → unit silently skipped.
**How:** when findings count changes after a regen, diff unit names old vs new before trusting the change.

## Storm Guardian combo variants are intended, not a bug
BSData defines 5 special-variant options for Storm Guardians, including combo bundles ("Flamer & Power Sword", "Fusion Gun & Power Sword"). The engine greedily picks combos because they strictly dominate (same ranged + better melee).

**Why:** a strict-dominant combo wins on every target profile; the "normal" distributed loadout is a strategy preference, not a correctness issue.
**How:** don't "fix" it. Preferring plain variants is a policy decision, not a bug.

## Ask before pushing — explicit user confirmation ("pushito")
Dojo rule. The user says "pushito" when a push is authorized. Never push without it.

## After engine changes, regenerate findings before committing
Ranking changes (composition engine, dual-profile) alter DPP → top units shift (Storm Guardians became #1 Take and Hold after the composition work).

**How:** `python3 scripts/gen_findings_html.py --faction aeldari` then `--index`, run `tests/test_findings_validation.py`, then commit findings together with the engine change.

## Squad composition engine invariants
- Multi-fixed-weapon models: `ranged`/`melee` is a STRING for one fixed weapon, a LIST for ≥2 (Warlock: `["Shuriken Pistol", "Destructor"]`).
- Melee reduces to one non-Extra-Attacks weapon per model (`_reduce_squad_melee`, rule 24.11); all `[EA]` weapons are kept and added on top.
- Parallel-variant alloc models (Troupe, Windriders, Storm Guardians) are greedy: fill per-variant minimums first, then assign remaining models to the highest-damage variant with spare capacity.

## Vyper lesson — verify phantom drops before trusting a count change
A findings count drop of 1 can be a stale duplicate (removed config key) or a regression. Always identify the dropped unit first.

**Why:** the 72→71 change looked like a regression but was the removal of the phantom `Vyper` row from a pre-rename config entry (`Vypers` is canonical).
**How:** diff unit name sets old vs new HTML before deciding whether the change is good.

## Book-first merge — MFM is the roster, not just the points
The merged roster for a faction is defined by its MFM file. BSData-only units that carry the faction keyword (linked shared libraries, god-marines with `Faction: Heretic Astartes`, Imperial terrain in Chaos books) are contamination leaks, NOT roster members — no keyword filter can catch them because they carry the same Faction keyword as real units.

**Why:** Drukhari merged contained Aeldari units; CSM merged contained 4 god-marines. All carried faction keywords → keyword filtering failed. Book-first (`all_names = sorted(set(mfm_unit_map.keys()))` in `adapter/merge.py`) is the only filter that works.
**How:** profiles for MFM book units may still come from linked catalogues (cross-faction fallback), but the roster itself is `mfm_unit_map` only. `data/merged/*.json` is output; regenerate with `python3 adapter/merge.py --all --output data/merged/`.

## Book-first fallout surfaces pre-existing config gaps — curate or KNOWN_MISSING
After book-first, units that previously leaked into MULTIPLE factions' merged files (e.g. Aquila Kill Team, Cadian Shock Troops, fortifications) now appear in exactly one faction — the coverage guard (`tests/test_unit_coverage_guard.py`) stops skipping them (`len(fids) != 1`) and flags them as genuinely missing.

**Why:** multi-faction leaks masked real gaps; book-first unmasked them.
**How:** real squads get curated config entries (builds format, weapons verified via `RankingEngine.W()`); fortifications go to KNOWN_MISSING (gen_config deliberately skips Fortifications at `data/config/AGENTS.md` + `scripts/gen_config.py` line ~520).

## Test MFM counts must dedupe model-count tiers
MFM files list model-count tiers (e.g. 5-model and 10-model Aquila Kill Team) as separate rows with identical names. Tests comparing merged vs MFM counts must count unique names.

**Why:** `test_merged_count_gte_mfm[Imperial Agents]` failed: 58 MFM rows vs 29 unique units vs 29 merged units. The duplicates are tiers, not distinct datasheets.
**How:** dedupe at the loader: `units = sorted({u["name"] for u in ...})`; update `EXPECTED_COVERAGE["total_mfm"]` accordingly.

## Validator baseline is noisy — compare against HEAD, not zero
`validate_configs_vs_bsdata.py --all` exits 0 even with 1400+ MEDIUM/LOW issues (pre-existing, mostly MISSING FIXED RANGED/MELEE noise). A worktree created fresh has an EMPTY bsdata submodule until `git submodule update --init bsdata` — running the validator there reports "0 issues" and is a FALSE clean baseline.

**Why:** the worktree's bsdata submodule isn't auto-populated; a "0 issues" HEAD baseline was an artifact, not a regression signal.
**How:** to compare validator output across revisions, init the submodule in the worktree first (`git -C <wt> submodule update --init bsdata mfm`), then diff issue counts per faction. Treat the validator as advisory; pytest + findings validation are the gates.

## Shared-cap SEGs are group-level max, not per-variant
BSData encodes "Heavy weapons" on GK squads (Purgation/Purifier/Interceptor) as a nested SEG whose MAX is a combined budget shared across its model variants (Purgation max=4 specials total regardless of squad size, Purifier max=2, Interceptor max=1). The parser tags each variant with `group_max`; the generator passes it through; the engine enforces it as a SUM cap across the tagged variants in `_best_alloc_index` and `_alloc_combo_space`.

**Why:** per-variant max alone would let a 10-model Purgation take 4+4+4=12 specials. The user-confirmed correction: Purgation cap is 4 at BOTH size 5 and size 10.
**How:** `group_max` on each variant in the group; engine tracks `groups[group_max] -> [variant indices]` and skips a variant whose group is at cap.

## Dup-strip fires only when the base SE is the group's ONLY direct model
The parser strips a base model's min/max when it exactly duplicates the containing group's (BSData pattern: Purgator min=4/max=9 == '4-9 Purgators' group). But it MUST NOT strip when the group has sibling special variants in the SAME SEG (Ynnari Reavers: Reaver min=2 is a real per-variant minimum — Blaster/Heat Lance are direct siblings, stripping would let the engine drop all plain Reavers).

**Why:** Purgation specials live in a NESTED SEG (safe to strip); Reavers specials are direct siblings (must keep min). The structural difference is `len(direct_models) == 1` on the SEG.
**How:** strip condition = SE min/max == SEG min/max AND NOT leader AND the SEG has exactly one direct model SE.

## GK special weapons replace BOTH storm bolter and Nemesis force weapon
11e GK datasheets (40k.app/Wahapedia): "Up to 4 Purgators can each have their storm bolter AND Nemesis force weapon replaced with 1 incinerator and 1 close combat weapon (or psilencer/psycannon)". The special model loses its Nemesis melee for a CCW — so the alloc greedy is target-dependent: vs GEQ the torrent Incinerator wins (Purgation fills 4, Purifier 2, Interceptor 1 — the shared caps), vs MEQ/TEQ the plain Nemesis loadout wins because the melee delta outweighs the ranged gain. NOT a bug — the cap is a ceiling, not a mandate.

**Why:** a competitive list running 4x Psycannon Purgation is a strategy choice (ranged pressure), not the engine failing to fill a cap.
**How:** pin the target-dependence in tests (GEQ fills caps, MEQ goes plain); never assert "cap must be filled".

## Pricing tests resolve by config n, not first cost in tier
`test_pricing.py` originally compared config pts/pts_3rd against the FIRST cost in the MFM tier (min-size). A unit evaluated at n=5 must use the 5-model price — the engine's `_resolve_pts` matches `cost.get("models") == models`. With n=4→5 for GK Terminator/Paladin, the old test failed (expected 140/170, config 175/215).

**Why:** "config n=5 with pts 175/215" is the user-confirmed evaluation point; the test must resolve the MFM price at the same n.
**How:** `test_pricing.py` builds `(models, points)` lists per unit and picks the entry matching config `n`; falls back to min-size when n is absent.

## Findings DPP must carry its target-mix — meta presets + selector
`gen_findings_html.py` computed every faction's DPP against the default MEQ target and never exposed the meta. That made the number look objectively "low/high" when it was really "vs a MEQ list". The findings page now computes rankings against each of the faction's meta profiles (all-comers, competitive, infantry, vehicle, elite) and lets the viewer switch via a banner + `<select>` — the DPP cell and the top-# change live with the chosen composition.

**Why:** user point — "40% vehicles vs pure terminators gives a completely different DPP, and the meta moves". A number without its target mix is an epistemic trap; the dojo's formula-transparency rule demands the mix be shown with the number.
**How:** (1) `data/config/_base.json` defines canonical presets (competitive/infantry/vehicle/elite) so every faction has them; curated factions already override with the same keys. (2) `build_data` returns `{'meta': {preset: {mission: [unit]}}, 'meta_info': [...]}` instead of the old flat `{mission: [unit]}`. (3) JS reads `DATA.meta[active][mission]`, one `setMeta()` re-renders all tabs. (4) `tests/test_findings_validation.py` unwraps via `_meta_data(data)`/`_all_meta_units`/`_meta_unit_items` helpers. Weights are normalised to % in `_meta_weights_display`.

## Conditional rerolls vs MONSTER/VEHICLE are auto-detected, not configured
Units like GMNDK (Surge of Wrath), Eradicators, Fire Dragons, Sunforge carry datasheet abilities granting re-rolls vs MONSTER/VEHICLE. These are auto-parsed from the merged ability DESCRIPTION at ranking time (`engine/reroll_detect.py`), never hand-authored into config. The spec is `{reroll_hits, reroll_wounds, reroll_damage, phase, targets, ability_name, raw}`; the parser is deliberately conservative — it only claims a reroll when the text is unambiguous, and `_RE_ONES` distinguishes "of 1"/"1s" (reroll 1s) from "you can re-roll" (reroll all). Phase detection: `melee` if only melee mentioned, `ranged` if ranged/shooting mentioned, else `both`. Tile: Surge of Wrath → hit/wound/damage all, melee, [MONSTER,VEHICLE]; Assured Destruction → hit/wound all; Bring it Down! → hit/wound 1s.

**Why:** GMNDT is the flagship case — its greatsword D6 damage used to be flattened to 3.5 by the loader, making the reroll_damage worthless. Retention solves it: `WeaponProfile.damage_raw` keeps the raw D string (`"D6"`), `_damage_reroll_mean` derives the honest mean (D6 all-reroll = 4.25 → factor 1.2143), and `expected_damage` applies the factor. It's a single source of truth.
**How:** (1) loader passes `raw_d` into `WeaponProfile.damage_raw`. (2) engine computes `damage_reroll_factor` from `reroll_damage` + `damage_raw`. (3) `compute_ranking` runs the detector per unit; when a spec matches, it switches to `_ld_dmg_conditional`, which applies the reroll ONLY to targets whose toughness matches the spec's keywords (via `_anti_keyword_matches` + `ANTI_KEYWORD_TOUGHNESS`) AND only in the spec's phase. (4) meta weighted lists sum per-target damage with the right modifier. (5) `_unit_lean` in the truth-report test mirrors this — otherwise the report diverges from compute_ranking for every ability-carrying unit. (6) `test_detachment_validation.TestTier25InertFields.applied_dpp` must list `reroll_damage` (it's a live field now, not inert).

**Caveat:** the parser claims only mechanical facts from the text — it never invents rerolls absent from the description, and GMNDK is the only GK unit with Surge of Wrath (NDK does NOT have it).

## Damage rerolls are silently cancelled by the wounds-per-model cap
`expected_damage` applies the reroll damage factor BEFORE the overkill cap (`min(damage × factor, max(wounds,1))`). On a 1W GEQ or 5W MEQ the boosted mean already exceeds the cap, so `reroll_damage=all` produces an IDENTICAL number to no reroll — the honest dice math only shows on W≥6 monsters/vehicles. That is a valid game rule, but it is an assumption-registry item, not a hidden win: "damage rerolls are capped by target wounds; no mid-roll variance captured." Also note the cap slightly OVERSTATES W=4-5 targets (flat factor then cap vs. the real truncated distribution) — flagged by Shredder, accepted as modeling approximation.

**Why:** a naive reading of "Surge of Wrath gives +damage reroll" expects every target to see it. The cap is correct 40k (you can't do 8 wounds to a 5W model), but the report must say so.
**How:** mention the cap in any DPP-with-reroll presentation; do not present the damage factor as unconditional.

## Reroll detector: context keywords are false positives — FIXED 2026-08-08
"Judgement of the Omnissiah" (Space Wolves Iron Priest): "…targets an enemy unit within Engagement Range of one or more friendly ADEPTUS ASTARTES VEHICLE units, you can re-roll the wound roll." The VEHICLE there is a CONTEXT (proximity to friendly transports), not the target type — the parser naively records `targets=['VEHICLE']`, so the engine grants the reroll when the target is T≥6 rather than when the enemy is near a friendly vehicle. Same class: Mek Gunz "Splat!" rerolls at Starting Strength EXCLUDING monsters/vehicles — the M/V mention is an exclusion, not a target. Previously accepted (Shredder: ship-able), now fixed.
**How (closed):** `_target_keywords()` does a per-occurrence scan with a 60-char window back from each keyword. A keyword inside a context phrase (`friendly`, `within … of`, `excluding`) is skipped; a genuine target-class mention in the same text is kept (`Lokhust Heavy Destroyer's gauss destructor against MONSTER or VEHICLE unit`). The scan is singular/plural-aware (`MONSTERS` vs `MONSTER`) — a naive `\bmonster\b` misses the plural. Probe tests: `tests/test_reroll_detect.py::TestContextKeywordFalsePositives` (5 cases).
**Caveat**: a `friendly`/`excluding` cue within 60 chars of a later genuine M/V target in the same sentence will drop that target too — acceptable over-masking (rare, under-rates rather than fabricates) but if a datasheet shows it, widen the window or split per sentence. `within … of` only counts as context when it names a nearby entity (`within … of one or more friendly VEHICLE units`); bare range conditions (`within 6" of this model`) are NOT context — regression-tested in `TestRangeConditionNotContext`.

## Melee/range phase tokens are two sides of one classifier — fix both at once
The naivie parser only recognized "melee"/"ranged"/"shooting phase". Adding `\bshoot(?:s|ing)?\b` to the ranged side without the melee mirror (`\bfights?\b|Fight phase`) leaves the same leak on the other side: "Each time this model fights…" → phase defaulted to "both" → melee-only reroll leaked into ranged damage. Shredder lesson: when fixing a symmetric classifier bug, fix the whole polarity class in one pass.
**How:** `_RE_MELEE` covers `melee|fights?|Fight phase`; `_RE_RANGED` covers `ranged|shooting phase|shoot`. Each gets a dedicated probe test.

## Truth report regenerator must be hash-seeded or the commit diff churns
`write_report()` iterates dicts during ranking; without a fixed `PYTHONHASHSEED` every run produces different floats AND different file bytes — a 12k-line diff on every regen, drowning real changes. Fixed: `write_report` now JSON-dumps with `sort_keys=True` and the canonical regen is `PYTHONHASHSEED=1 python -m tests.test_truth_roles_report`. Byte-identical across runs (verified). Do NOT regen with a bare `python3 -c "from tests...write_report()"`.
**Why it matters:** a churny artifact makes every report PR an unreviewable diff; reviewers can't tell the 10 semantic leaf changes (a real drift) from 12k lines of hash noise.

## Reroll detector generalization: weakest-wins, aura-skip, keyword/roll boundary
Closed the M/V-only gate — class-keyed rerolls now detect CHARACTER / INFANTRY /
TITANIC / WALKER / MOUNTED too (24 → 33 datasheets).
**Weakest-wins mode rule:** when one roll noun appears in several clauses with
different modes, '1s' wins over 'all'. Upgrade clauses ("re-roll a Hit roll of 1...
if the target is a Psyker Character, you can re-roll the Hit roll instead") must
not leak a full reroll onto the whole class — 'all' would over-claim. Under-claims
the rare upgrade, never fabricates. Zero mode-conflicts in the accepted 24.
**Aura-subject skip:** "each time THAT <other> model makes an attack" hands the
reroll to a FRIENDLY unit, not the bearer (Atrapos "Consumed with Hunger" buffs War
Dogs) — skip, or every aura attaches to the bearer's own attacks. "a friendly X
model" that INCLUDES the bearer (Spirit Thief: Heretic Astartes) is kept.
**keyword/roll boundary:** `\b(hit|wound|damage)(?:\s+roll)?` without a trailing
`\b` matches "WOUND" inside "[DEVASTATING WOUNDS]" — a keyword, not a roll.
Plural-leak false positive (Emperor's Champion "Sigismund's Heir" claimed a wound
reroll from Dev-wounds). Always terminate roll-noun alternations with `\b`.
**Note:** D-Cannon "re-roll Damage 1s... *instead* all vs TITANIC" now under-claims
to 1s (the *instead* upgrade is the rare branch) — acceptable, directional.

## Generalization scope checked against corpus
Before writing code: surveyed the corpus. class-keyed rerolls = 33 abilities
(detected). Unconditional/army-wide = 150+ (76 'all' + 74 '1s') — separate
feature (needs `targets: ALL` + positional-trigger exclusion), filed on roadmap.
Bundle-of-many-abilities units mix per-datasheet.

## Space Marines squad migration — generator bugs, engine gap, validator truth
Wave-1 migration (34 squads) shipped with three real discoveries:

### 1. fuzzy_find_composition: case-insensitive exact match BEFORE substring
`'Eradicator Squad With Heavy Bolters'` in squads.json vs BSData
`'Eradicator Squad'` + `'Eradicator Squad with Heavy Bolters'`: substring
fallback matched `'eradicator squad' in 'eradicator squad with heavy bolters'`
→ wrote the melta payload onto the heavy-bolter squad. Substring is the LAST
resort; exact (then case-insensitive exact) must run first. Real-world cost:
silent wrong- weapon loadouts feeding the engine.

### 2. _alloc_model_name tie-break was hash-order nondeterministic
`max(set(stripped), key=stripped.count)` on a count tie (Outrider vs
Invader ATV, both 1) returns whichever hash-order wins — the alloc pool name
flipped between runs. Now: most-frequent, then SHORTEST name. Deterministic
across PYTHONHASHSEED values.

### 3. Engine multi-profile gap (Cyclone Missile Launcher)
frag (S4 D1 Blast) + krak (S9 AP-2 D6) live under ONE merged name; loader
resolves only `entries[0]` → Cyclone scores as S4 D1 and always LOSES the
slot to Assault Cannon (S6 D1 Devastating) vs every target incl T10/T12. This
is the desktop-not-modeled gap for missile launchers — roadmap Item 2. It
affected nothing before the migration; now pins in
tests/test_space_marines_complex_units.py document the stable (if wrong)
behavior so a future multi-profile loader makes the right test flips.

### Validator truth (the Outrider +1)
validate_configs_vs_bsdata went 128→129 issues — the ONE new issue was
`EXTRA WEAPON 'Bolt pistol'` on Outrider Squad, a FALSE POSITIVE: the
extractor mis-reads squad model entries as weapons (`fixed_ranged:
['Invader ATV']`), same pre-existing noise for every alloc-bearing unit. The
migration did not add a real defect; the diff-of-validator-issues method
(compare old/new counts) tells the story without diffing whole HTML.

### Test-discipline from this iteration
- Tests pin STRUCTURE, not damage — follow test_aeldari_complex_units.py
- MEQ fixture comes from conftest `_target_from_cfg("MEQ")` — never inline
  your own T/W/model_count (duplicated truth)
- When a test I wrote named a behavior wrong ('slot pick is target-dependent'),
  the fix is to pin the engine's ACTUAL behavior + document why, not fudge
- `len(res["ranged"]) >= n` invariant intentionally excludes melee-only-
  leader squads (Devastator sergeant, Storm Guardian platform)
- **Summoning caution**: I twice drafted edits/analyses that hallucinated
  file contents ("WKB", "Aeldari Init", nonsense strings). Always Read →
  actually inspect the file before editing; never compose oldString from
  what I think I wrote earlier.
