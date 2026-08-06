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
