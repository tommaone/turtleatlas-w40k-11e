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
9. python3 scripts/gen_findings_html.py --faction X, then --index
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
two completed factions.

## Migration order

- **Wave 1 — big marine codexes:** Space Marines → Dark Angels → Blood
  Angels → Space Wolves (BA/SW parallelisable). Then Black Templars,
  Deathwatch.
- **Wave 2 — major non-marine:** Astra Militarum → Adeptus Mechanicus.
- **Wave 3 — chaos:** CSM + god-marines (after the shared-units question
  is settled; sync machinery exists but may be removed — see blockers).
- **Wave 4 — quick wins:** Necrons → Tyranids → Orks → Tau (also gives
  the T3-benchmark factions engine attention).

Note on marine codexes: chapter catalogs are SM base + chapter addons
(verify overlap before treating BA/DA/SW scores as independent work —
see the marine-duplicity analysis in the session).

*Created 2026-08-06. Companion to docs/roadmap.md.*
