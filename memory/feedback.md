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

## Choice profiles (frag/krak, standard/supercharge, strike/sweep) score as MAX-over-group
A choice weapon is ONE weapon with multiple profiles; the shooter picks ONE profile per attack. Scoring must be max over the group, never entries[0] (data-order).

**Why:** entries[0] made results catalog-merge-order dependent (SW plasma = 'standard', SM = 'supercharge'; Cyclone launcher resolved as storm-bolter-only and under-rated missile slots; Devastator picked Multi-melta over Plasma cannon because supercharge was invisible). Pins flip, but they pin the old bug.
**How:** `WeaponProfile.variants` holds the other choice profiles; `compute_weapon_dpp` returns max over base+variants. The loader NEVER collapses distinct ' - variant' profile names (the plain-profile preference applies only within one profile name — it dedupes catalogue copies, not choice profiles). Base name is deterministic: prefer 'standard', then a plain no-suffix profile, so SM/SW/DA/BA display identically. Variants recursion must strip variants (dataclasses.replace) or it loops forever.
**Test pins that flipped:** SM/BA/DA Devastator heavy slot Plasma cannon (supercharge) over Multi-melta vs 2W MEQ; SW Intercessor Sergeant / Grey Hunter Pack Leader Plasma pistol over Hand flamer; SM Tactical specials to Plasma; DA Deathwing heavy to Plasma cannon; Chaos Knight Despoiler swaps a gatling arm for the chainsword arm (sweep-scored, verified 19.14 > 17.52 on the competitive meta).

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
`write_report()` iterates dicts during ranking; without a fixed `PYTHONHASHSEED` every run produces different floats AND different file bytes — a 12k-line diff on every regen, drowning real changes. Fixed: `write_report` now JSON-dumps with `sort_keys=True` and the canonical regen is `PYTHONHASHSEED=1 python3 -m pytest tests/test_truth_roles_report.py`. Byte-identical across runs (verified). Do NOT regen with a bare `python3 -c "from tests...write_report()"`.
**Corrected 2026-08-09:** the OLD documented command `PYTHONHASHSEED=1 python3 -m tests.test_truth_roles_report` was a NO-OP — the module has no `__main__` block, so `python3 -m` exits silently without running the session fixture. The report only (re)writes when PYTEST executes the module (its session-scoped fixture writes the file). The "seeded regen" that produced the stale commit `1a2c541` was this no-op; the report is now regenerated only via pytest. Verify a regen actually ran: check the report mtime, don't trust the exit code.
**Why it matters:** a churny artifact makes every report PR an unreviewable diff; reviewers can't tell the 10 semantic leaf changes (a real drift) from 12k lines of hash noise. And a silent no-op regen makes a STALE report look freshly rebuilt.

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

## Unseeded full pytest churns the truth report — verify runs must be seeded
`python3 -m pytest -q` (no PYTHONHASHSEED) rewrites `reports/crossfaction_truth_report.json` via the session fixture in `test_truth_roles_report.py` — with a random hash seed the floats churn and the WORKING TREE gets a false diff in OTHER factions (CSM/EC/TS this session) before any change is made. The committed report was seed-1 generated; an unseeded full run makes a 200-line noise diff appear as if the migration caused it.

**Why:** the report is regenerated by ANY pytest execution, not just a targeted run; the baseline run alone dirtied the tree.
**How:** baseline AND final verification runs use `PYTHONHASHSEED=1 python3 -m pytest -q` (byte-identical to the committed report — verified twice). If an unseeded run dirties the report, `git checkout -- reports/crossfaction_truth_report.json` restores it; the only legitimate report delta for a faction migration is within that faction's own block (BA: hunks 2384–3060, no `"faction"` header lines changed).

## Blood Angels migration validator delta = same Outrider false positive
BA went 127 → 128 validator issues after the migration. The ONE new issue: `EXTRA WEAPON (not in BSData choices): 'Bolt pistol'` on Outrider Squad — identical to the SM-migration false positive: the Outrider alloc pool includes the Invader ATV variant and the extractor mis-reads squad model entries as weapons. Pre-existing Outrider noise (`MISSING FIXED RANGED 'Invader ATV'`, EXTRA 'Twin bolt rifle'/'Astartes Chainsword'/'Heavy Bolt Pistol') is the same class. Migration added no real defect.

**How:** diff issue-line sets old vs new (`sort` both validator outputs, `diff`), identify the single new line, confirm it matches a known false-positive class before judging the migration.

## No-Legends rule in fuzzy_find_composition (Dark Angels migration)
`[Legends]`/`Legends` BSData composition entries are NEVER matched — exact,
case-insensitive exact, or substring. A config unit whose only BSData entry is
Legends (Deathwing Command Squad → 'Deathwing Command Squad [Legends]') must be
KEPT (no composition), not rewritten with a Legends payload.

**Why:** config is the curated, current-edition roster; Legends entries are
game-legacy content. Writing a Legends payload into a current config silently
corrupts the loadout. DA had TWO stale config units from this: Deathwing Command
Squad (only exists as `[Legends]`) and Ravenwing Talonmaster (in NO BSData
catalogue at all) — both removed from `data/config/dark-angels/squads.json`
(35→33). Invader ATV is a REAL squad variant (slot choice), NOT a legends unit —
don't confuse the two.

**How:** `_is_legends_name()` checks `"legends" in name.lower()`; every return
path in `fuzzy_find_composition` filters through it. Regression tests in
`tests/test_gen_squad_composition.py::test_no_legends_*` (4 cases) +
`tests/test_dark_angels_complex_units.py::test_no_legends_unit_removed_from_config`.
Before adding a no-legends rule, SURVEY the corpus first: 335 BSData composition
entries are [Legends]/Legends across 30 factions, but only 2 config units
(DA Deathwing Command Squad, SW Wolf Scouts) would be polluted by Legends-only
matching. SW Wolf Scouts is a current-edition unit (in merged data, no legends
flag) — its BSData catalogue has BOTH `Wolf Scouts` and `Wolf Scouts [Legends]`,
so the no-legends rule must not remove real units.

## Detachment modifiers are BLOCKED until every army is on the slot setup
No detachment work (SM/DA/others) until all factions run the slot-based
configs (weapon_options/builds, slots, alloc pools). Until then the engine's
loadouts are generic configs, not real gear.

**Why:** (2026-08-10 decision) a detachment bonus applied to an imaginary
loadout is a lie — it models a modifier over wargear the army doesn't actually
resolve. GK/CK/Daemons detachments exist, but they predate the slot setup and
must be re-verified against slot configs once those factions migrate.
**How:** the roadmap gate is: squad-composition migration for all 30 factions
FIRST (Wave 1: Black Templars / Deathwatch), detachment modifiers second.
Never start detachment work on a faction that isn't on the slot setup.

## min==1 is NOT always a leader (Deathwatch Terminator bug)
`make_build` treated ANY model with `min == 1` as a leader (fixed count 1).
The DW Deathwatch Terminator base model is `min: 1, max: 9` — "at least 1",
not "exactly 1". It consumed the whole squad budget as a "leader" and the
squad resolved 2/5 models (2 leaders, pool empty, budget lost).

**Why:** BSData uses min==1 for two different things: fixed single-model
leaders (Exarch, Felarch, Lead Player, Terminator Sergeant — min==1 AND
max==1) and base-pool types that must be present ("at least 1" — min==1,
max>1, e.g. Deathwatch Terminator). Treating the latter as a leader silently
collapses the squad to the leader count.
**How:** leader = `min == 1 and max == 1`; a min==1 base model stays in the
pool and its min contributes to the mandatory requirement (pool_mandatory).
Verified behavior-neutral for shipped factions (SM/DA/BA/SW/aeldari/GK: 0
build diffs after the change; the only diffs were pre-existing BSData
`group_max` source drift on Corsairs, unrelated). Regression pins:
`tests/test_deathwatch_complex_units.py::test_deathwatch_terminator_squad_all_default`
(5 storm bolters + 5 power fists, not 2).

## "Kept" units still need curation — check their builds
The generator's `kept (no composition)` bucket means "no BSData composition
match", NOT "config is correct". DW's Decimus Kill Team was kept with a
broken config: `ranged: 'Plasma pistol - Standard'` / `melee: 'Plasma pistol
- Supercharge'` — a ranged weapon (Hazardous) in the melee slot, the plasma
swap backwards. Datasheet default is Plasma pistol + Power weapon.

**Why:** kept units ride whatever hand-curated builds they already had; a
misplaced weapon or a stale loadout survives the migration untouched.
**How:** review EVERY kept unit's existing builds during curation (step 3 of
the checklist), not just the skipped ones. Decimus fixed to `ranged:
"Plasma pistol"` + `melee: "Power weapon"` — the bare plasma resolves via the
choice-profile max-over fix. Pin: `test_deathwatch_complex_units.py::test_decimus_kill_team_curated`.

## Characters that snuck into squads.json
BT's Chaplain Grimaldus (n=1, pts, info, builds) was filed under
`data/config/black-templars/squads.json` — he is a character, not a squad.
The two files use different build schemas: squads use flat `builds` with
model entries; characters use `weapon_options.builds` with `ranged`/`melee`
arrays + `ranged_choices`/`melee_choices` lists.

**Why:** a character in squads.json resolves via `_best_squad_variant` (the
wrong path) and never gets the character treatment; the generator skips it
(the "skipped (parallel variants)" bucket) so it stays stuck in the wrong
schema.
**How:** move characters to characters.json, convert to the
`weapon_options.builds` schema. Two old plasma builds (Standard/Supercharge)
collapse to one bare `"Plasma Pistol"` — the max-over choice fix resolves it
deterministically. Pin: `test_black_templars_complex_units.py::TestBlackTemplarsCharacters`.

## Truth-report regeneration is NOT byte-reproducible from committed state
The committed `reports/crossfaction_truth_report.json` is not reproducible by
regenerating from HEAD under any seed: with configs stashed to pristine HEAD,
`PYTHONHASHSEED=1 pytest tests/test_truth_roles_report.py` still produced a
26-line drift in untouched factions (AM Commissar armor_share 0.4→0.3333, CSM
Aggressor armor_share 0.6338→0.5357, etc.). Tried seeds 0,1,2,3,7,42,123,999,
20260722; best match was seed 2 with a 2-line residual. The report's own
comment says "byte-identical" but that claim is stale in this environment.

**Why:** `write_report()` runs the ranking funnel over every faction; float
results carry hash-order dependence deeper than the sort_keys guard, and the
committed artifact was generated in a session whose seed/state we can no
longer reproduce (possibly an older interpreter or dependency version).

**How (proven isolation for a faction migration):**
1. Regenerate with configs applied → regenerate with configs stashed (same seed).
2. Diff the two: the ONLY blocks that differ must be the migrated faction(s).
   BT/DW migrated blocks were byte-identical across seeds 1, 2, 42 — seed-stable.
3. Commit = committed report with ONLY the migrated factions' blocks replaced
   by the regenerated ones. All other factions stay byte-identical to committed.
This produced a clean report diff: exactly 2 changed blocks (BT, DW), no
`"faction"` header lines changed. Do NOT commit a full-seed regen — it drags
noise from untouched factions into the migration diff.

## Legacy build resolver ties are hash-order, slots schema is insertion-order
The legacy character build path dedups choice lists with
`all_options = list({opt for cl in ranged_choice_lists for opt in cl})` — a
set comprehension. Iteration order follows CPython string hashes, NOT
insertion order. In a DPP tie (`>` strict comparison, first max wins) the
picked weapon depends on the hash permutation. The slots schema
(`_resolve_slots_build`) iterates choices in config order — deterministic.
`scripts/migrate_characters_to_slots.py` preserves insertion order.

**Why:** the A/B parity harness
(`scripts/snapshot_char_loadouts.py` before/after +
`scripts/compare_char_loadouts.py`) surfaced 16 loadout flips after the
slots migration (Autarch Fusion Pistol→Gun, Commissar plasma
supercharge→standard, Desecrator Warpstrike claw→Reaper chainsword). Every
flip was a zero-delta tie (delta=0.00000 on the target) — optimal DPP value
and optimal set unchanged; only the tie-break member changed.

**How:** treat legacy-vs-slots diff as regression ONLY if the chosen
weapon's DPP differs by more than epsilon. Tie flips are the migration
working correctly (deterministic > hash-order). Parity harness before
conversion is the proof; re-run it after any future schema change.

## Character schema LOCKED to slots (2026-08-11)
All 30 factions' characters are now on the slots schema:
`{name, fixed: [{name, type}], slots: [{name, choices: [{name, type, count?}]}], no_duplicates?}`.
Legacy keys (`ranged`, `melee`, `ranged_choices`, `melee_choices`,
`max_ranged`, `max_melee`) are FORBIDDEN — guard test
`tests/test_characters_builds_format.py::test_every_build_has_slots_schema`
enforces it. Convert with `scripts/migrate_characters_to_slots.py`
(idempotent, `--dry-run`/`--faction` flags).

**Why:** roadmap gate — every army must run the slot setup
(weapon_options/builds, slots, alloc pools) before detachment modifiers
can be trusted; a bonus over an imaginary loadout is a lie.

**How:** 476 builds converted in one pass (rest already slotted or
buildless). max=N maps to N slots over the DEDUPED union + `no_duplicates`
(capped at min(N, len(union))); max=1 is one slot over union; no-max is one
slot per choice list. `no_duplicates` is build-level and applies across ALL
slots (ranged+melee) — check for cross-type name collisions when a build
has pick-N melee AND ranged choices (Knight Despoiler is clean: no overlap
between ranged union and melee union).

## Knight arm bundles + mount slots (2026-08-11)
BSData models the Knight Despoiler's arm bundles as single upgrade entries:
"Gatling cannon and flamer" and "Battle cannon and heavy stubber". The weapon
loader resolves those bundle names to ONLY the primary profile (gatling
cannon; battle cannon) — the bundled secondary (Heavy darkflamer; Diabolus
heavy stubber) is SILENTLY LOST if you reference the bundle name in a config
slot. Split bundles into component weapons in `fixed` for full DPP.

**Why:** the curated 6-build Despoiler config used split bundles (correct for
DPP) but conflated two INDEPENDENT mounts into one "Ranged weapon 1" slot:
[Havoc missile pod, Ruinspear rocket pod, Hellstorm autocannons, Diabolus
heavy stubber, Daemonbreath meltagun] — forcing pick-one-of-five when the
datasheet allows a carapace weapon AND a shoulder weapon simultaneously. It
also omitted the Daemonbreath thermal cannon arm entirely and let a melee
slot pick "Reaper chainsword" on arm2 (BSData: arm2's melee is Warpstrike
claw only). Verified against BSData containers ("Carapace weapon", "Shoulder
weapon", "Replace reaper chainsword", "Replace warpstrike claw").

**How:** model the mounts as separate slots (Carapace weapon: pod/rocket/
autocannons; Shoulder weapon: stubber/meltagun) on every build, split arm
bundles into components, enumerate the full arm space (13 unique legal arm
sets incl. thermal arms). Titanic feet is innate (min=1/max=1 on the BSData
base) — `fixed`, never an arm slot. The parser's own
`extract_wargear_constraints` already models the 4-slot structure correctly;
hand-curated configs must not regress it. Verify a config against
`extract_wargear_constraints` output before curating by hand.

## Dual-profile weapons in `fixed`: reference the GROUP entry, never both profiles (2026-08-11)
A choice weapon (standard/supercharge, low/high intensity) is ONE catalog entry whose variants are maxed by the engine. A config build must reference the GROUP name (e.g. `Ectoplasma decimator`) in `fixed`. Referencing BOTH `- standard` AND `- supercharge` as separate `fixed` entries double-counts in RANGED: `_ld_dmg` sums every ranged entry, so the shooter "gets" both profiles per attack. Melee is immune (`_best_melee` takes max for a single model), which is why fixing strike+sweep in melee is harmless — but the ranged path sums.

**Why:** the Knight Tyrant config fixed `Ectoplasma decimator - standard` + `- supercharge` as two ranged weapons → 2x damage. Fixed by replacing both with the group entry `Ectoplasma decimator` (verified: MEQ dmg 2 → 1). Same trap found in `Chaos Cerastus Knight Atrapos` (fixes lascutter `- low/high intensity` + singularity cannon `- contained/singularity`) — flagged, separate ticket.

**How:** if a validator flags `MISSING FIXED RANGED: '<group name>'` while the config uses `- profile` names, the config has the double-count bug — swap the two profile entries for the one group entry. The validator's MISSING is the early-warning, not noise.

## BSData min2/max2 groups = N independent slots, duplicates legal (2026-08-11)
A `min=2, max=2` selection group (Porphyrion "Shoulder weapons", Moirax "Weapons") is NOT one choose-one slot: it is N picks from the group, duplicates allowed. The parser's `extract_wargear_constraints` flattens it into one slot with 2 choices — insufficient for config. Model as N slots over the same choice list, WITHOUT `no_duplicates` (AA and LL are legal).

**Why:** Porphyrion 2x autocannon is legal; a single shoulder slot would only ever pick one gun. Moirax arms: 2 independent arms x 5 options, duplicates legal → either 2 slots (bundle choice loses the claw to primary-profile resolution) or 15 enumerated builds with split components (Despoiler precedent, chosen).

**How:** read the raw BSData group constraints (`selectionEntryGroups` `constraints`), not just the parser output, when the group has min/max > 1.

## Dual-profile weapons in `fixed`: category must follow the entry's type (2026-08-11)
The slots resolver `_resolve_slots_build` originally called `W(name)` WITHOUT
category, so a dual-profile weapon in `fixed` resolved to its FIRST catalog
profile — the type field only SORTED the result into ranged/melee lists. A
Singing Spear in the melee list came back as the thrown profile (A1 S9),
and the Atrapos lascutter's melee list carried a RANGED high-intensity
variant (A3.5 S14) as a scoring option. Fix: pass `category=f["type"]`
(resp. `choice.get("type")`) to `W()` for every fixed entry and slot choice.

**Why:** the Farseer's melee Singing Spear resolved A1 S9 (ranged) instead
of A2 S3 (melee); Atrapos melee could max against a ranged variant.
Cross-faction: every faction with a dual-profile weapon in a slots config
was affected (Singing Spear, Chainsabres, lascutter, Hellspear, ...).

**How:** in `_resolve_slots_build`, `self.W(f["name"], unit_name=name,
category=f.get("type"))` and `self.W(choice["name"], unit_name=name,
category=choice.get("type"))`. The loader's category filter matches
`type_name` (Ranged Weapons/Melee Weapons), so single-category weapons are
unaffected — only dual-profile entries change behaviour.

## Process: this project ships commits to main directly, no PRs (2026-08-13)
No pull requests, no feature branches. Work lands as one commit per feature
straight on `main`, then `git push origin main`. PRs and long-lived branches
were tried and explicitly rejected by the maintainer — they add ceremony, not
value, for a single-maintainer repo.

**How:** develop on a scratch branch if useful, but merge into local `main`
(commit per feature, message tells the why), run the suite, then push `main`.
Close and delete any PRs/branches that were raised before this rule was set.


## Imperial Knights: slot-migration specifics (2026-08-13)
IK characters had the same dual-profile double-count class as CK, PLUS
missing slot structure. Fixed in one pass:

- **Group names**: Canis Rex (Las-impulsor), Cerastus Atrapos (lascutter +
  Graviton singularity cannon), Castellan (Plasma decimator), Defender
  (Plasma executor), Preceptor (Las-impulsor) — profile pairs
  (`- high/low intensity`, `- standard/supercharge`) in ranged summed.
- **Questoris knights** (Crusader/Errant/Gallant/Paladin/Warden/Preceptor)
  were missing BSData slots: Carapace-mounted Weapon + Meltagun (+ Reaper
  Chainsword where BSData offers it; Preceptor had NO melee at all).
- **'Twin Icarus autocannon' does NOT resolve** in the merged catalog
  (loader gap — profile lives in BSData Library but never merged). Use
  `Icarus autocannons` (same A3 S7 profile) in the carapace slot. Validator
  flags it EXTRA — accepted noise, same class as bundle-splits.
- **Castellan/Valiant carapace**: BSData offers shieldbreaker/siegebreaker
  bundle names that resolve to NOTHING in the merged catalog. No slot
  modeled — documented gap, not a config bug.
- **Magaera/Styrix**: mirror CK 2-build pattern (chainsword/hekaton),
  Hekaton bundle split into components. Validator EXTRA noise accepted.

**How:** run `validate_configs_vs_bsdata.py --faction imperial-knights` —
12 issues remain, ALL MEDIUM accepted-noise class (bundle-splits +
Icarus name gap), same as CK's 11. Deterministic check: 0 CRITICAL/MAJOR.
Test lock: `tests/test_imperial_knights_slots_migration.py` (67 tests).

## CSM + EC + Orks slot migration (2026-08-13)
Wave-2 completion: three factions migrated in one pass.

### CSM
- **Fabius Bile is a 2-model character unit** (Fabius Bile + Surgeon
  Acolyte, 100 pts). BSData: Fabius carries Xyclos needler + The Chirurgeon
  + Rod of Torment; the Acolyte carries Surgeon Acolyte's tools. The old
  squads.json entry gave BOTH models needler+Chirurgeon (wrong) and dropped
  the other two weapons. Lives in characters.json as ONE fixed build with
  all four weapons. No test in test_dpp_sanity/test_squad_wargear needed
  updates (Fabius stays whitelisted as support character).
- **Choice weapons reference GROUP names** (same rule as IK, extended):
  Dark Commune Warp Curse had BOTH `- witchfire` AND `- focused witchfire`
  in fixed = ranged DOUBLE-COUNT (ranged sums in _ld_dmg; melee maxes).
  Single-profile locks (Daemon Prince Hellforged weapons strike-only,
  MoP Rite of Possession focused-only, Sorcerer Infernal Gaze focused-only,
  Reave-Captain/Warpsmith Plasma pistol standard-only) permanently excluded
  the other profile. All fixed to group names — `W('Group', unit)` resolves
  to a profile WITH variants and the engine maxes per target.
- Validator noise envelope confirmed: CSM 60 issues vs DA 133 / BA 128 /
  SW 136 — the MISSING 'Legionary w/ boltgun' class is BSData composition
  model-names, not config defects.

### EC
- 9 squads, clean probe, 8-test complex-unit lock. Complex units: Chaos
  Terminators (alloc pool + champion Wargear slot), Noise Marines (alloc
  min3/max2 + Disharmonist slot), Infractors/Tormentors (Obsessionist
  two-slot). Validator 10 issues (all pre-existing noise class).

### Orks + generator fix (the real find)
- **fuzzy_find_composition substring is now ONE-WAY** (config name inside
  BSData name). The old `or bs_name.lower() in low` direction matched
  config units whose names are MORE specific than any BSData entry to the
  BASE composition: 'Boyz' in 'Burna Boyz' → Burna payload overwritten by
  base Boyz slugga/choppa; same for Squighog Boyz, Boyz (Armageddon),
  Chaos Spawn (Flesh Change), Ripper Swarms (Parasite of Mortrex). Those
  are now KEPT for manual curation. Same hazard class as the Eradicator
  fix (memory §1), one layer deeper — exact/case-insensitive-exact first
  did not save them because there IS no matching BSData entry at all.
- Cross-faction scan proved only 5 units change behavior, all correctly
  becoming kept (no legit match lost). Regression tests:
  tests/test_gen_squad_composition.py::test_substring_is_one_way_* (2).
- Orks: 10 regenerated + 7 kept (Burna Boyz, Squighog Boyz, Boyz
  (Armageddon), Gretchin, Gretchin (Armageddon), Lootas, Wartrakk). Kept
  units retain curated builds; test_orks_complex_units.py (17 tests)
  locks them. Validator 75 issues BEFORE and AFTER migration — zero new.
- Deterministic: CSM 2 INFO (Fabius Epic Hero keyword naming — benign),
  EC 0, Orks 2 INFO (Ghazghkull keyword + Kill Rig abilities).

**How:** seeded full suite 3588 passed / 36 skipped. Generator change
isolated: run `pytest tests/test_gen_squad_composition.py` (18) first,
then per-faction complex tests, then full suite.

## Anti-X keyword fixes the wound target, not just the crit threshold
The engine parsed `Anti-X Y+` into `anti_info` but only used it for the
critical-wound threshold — never to override the wound target. Result: a
Chainfist (WS4 S8 Anti-VEHICLE 3+) scored 0.670 vs a Knight (T13) while a
Power Fist (WS3 S8) scored 0.890, because the fist hit on 3+ vs 4+ and the
chainfist's anti rule never lowered the wound target. 11e rule: an
unmodified wound roll of Y+ vs the matching keyword scores a Critical Wound
= always successful regardless of S/T, so effective wound target is
min(S/T target, anti_val).

**Fix (engine/dpp.py `expected_wounds`):** when `anti_matches`, set
`wound_target = min(wound_target, anti_val)`; reuse `anti_matches` for the
crit-roll branch. The keyword match is a toughness-band heuristic
(`ANTI_KEYWORD_TOUGHNESS` in engine/dpp.py: VEHICLE 6–13, INFANTRY 3–5,
CHARACTER 3–10, etc.) because TargetProfile has no keyword field.

**How:** 3 regression tests in tests/test_dpp.py
(`test_anti_infantry_wound_target_override`, `test_anti_vehicle_punches_up`
— replaced `test_anti_infantry_increases_damage`,
`test_anti_keyword_non_matching_target`) + `Knight` fixture in
tests/conftest.py. 6 stale tests updated: 5 Aeldari (Felarch → Neuro
disruptor Anti-INFANTRY 2+, Warlock Conclave/Skyrunner → Witchblade vs MEQ,
Singing Spear vs TEQ/vehicles) + 1 SM (`test_slot_pick_chainfist_punches_up`).

## Datasheet caps like "1 chainfist per 5 models" are NOT in BSData
BSData encodes per-variant maxes (e.g. Chainfist max=1 per variant) but NOT
the shared datasheet cap. The generator copies maxes verbatim, so two
chainfist variants (combi-bolter + combi-weapon) each max=1 → engine can
take BOTH = 2 chainfists, plus heavy-weapon melee slot + champion slot =
up to 4 in a 5-man squad. CSM was worse: max=2 per variant = BSData's
10-model cap applied to an n=5 config.

**Fix:** config-level, engine mechanism already existed — `group_max` (a
value shared by variants = combined budget, enforced in
`_best_alloc_index` and `_alloc_combo_space`). Set `group_max: 1` on the
chainfist alloc variants AND strip Chainfist from the heavy-weapon melee
slot and champion Wargear slot choices (slots are per-model, group_max
cannot span them). Applied to: EC Chaos Terminators, CSM Chaos Terminator
Squad, SM-family Terminator Squads (space-marines, black-templars,
blood-angels, dark-angels, space-wolves).

**How:** `test_slot_pick_chainfist_punches_up` now asserts 1 chainfist +
4 power fists vs T10 (was 5 chainfists — that pinned the un-capped config);
EC `test_champion_wargear_slot` asserts no chainfist in champion choices.
Engine verification: every terminator squad resolves to exactly 1
chainfist vs Knight, 0 vs MEQ/TEQ.

## Per-5 caps apply to MORE than chainfist — check the whole datasheet
The "1 chainfist per 5" lesson was incomplete: Chaos Terminators also cap
heavy weapons (1), paired accursed (1), and power fists (3) per 5 models.
EC had 2 Power fist variants each max=3 with NO shared group_max → engine
could field 6; CSM had max=6 each (10-model BSData caps in an n=5 config).
The heavy-weapon model's melee slot ALSO offered Power fist (a 4th fist
outside the alloc caps) and the champion slot offered Power fist too.

**Fix:** same pattern, applied to power fists:
- `group_max: 3` on BOTH Power fist alloc variants (EC + CSM)
- heavy weapon `max: 2 → 1`, paired accursed `max: 2 → 1` (CSM 10-model
  caps scaled to n=5)
- heavy-weapon melee slot → Accursed weapon only (per datasheet the heavy
  weapon replaces the combi-bolter, NOT the melee weapon)
- strip Power fist from EC champion Wargear choices (group_max cannot
  span the champion slot)

**Lesson:** when a datasheet says "for every 5 models", audit EVERY swap
line, not just the one that bit you. Also scale BSData maxes to the config
n (BSData often encodes 10-model caps; n=5 configs inherit them wrongly).

## Default findings meta is a single-source config + renderer default
Findings default mode is `DEFAULT_META` in scripts/gen_findings_html.py
(moves the chosen slug first in meta_info; the JS renders meta_info[0]).
Metas themselves live in data/config/_base.json `meta_profiles`; 5 curated
factions (chaos-daemons, chaos-knights, dark-angels, grey-knights,
space-marines) OVERRIDE the whole dict via shallow `_extends` — adding a
meta to _base alone is NOT enough, it must be added to each override too.

**This change:** default → competitive (was all-comers); added `anti-horde`
preset (GEQ 0.5 / MEQ 0.25 / TEQ 0.05 / Light V 0.1 / Heavy V 0.05 /
Knight 0.05, melee_penalty 0.8) to _base + all 5 overrides.
