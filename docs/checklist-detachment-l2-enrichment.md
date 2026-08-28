# Checklist — L2 Detachment Expert Review (346 detachmentov, 28 frakcií)

> **Účel:** podklad pre ľudský review gate (turtle-dojo / Marcel rule: každý kompilát
> overí človek). Keď je frakcia odsúhlasená, reviewner otočí `_meta.human_reviewed: true`.
> Automatické zámky: `tests/test_detachment_validation.py` — Tier 4 (scaffold L0-traceable)
> + Tier 5 (L2 enrichment gate). Zelená sada = skeleton; review je ľudská robota.

## Ako použiť tento dokument

1. Vyber frakciu zo stavovej matice (nižšie).
2. Načítaj si L0 fakty o jej detachmentoch:
   - `data/merged/<frakcia>.json` → `detachments[]` (name, dp, objective, enhancements — MFM, overené)
   - `data/config/<frakcia>/detachments.json` → scaffold (generovaný, L0-traceable)
3. Pre každý detachment dohľadaj pravidlo a slabé/tuhé miesta v **Wahapedia/NewRecruit**
   (Wahapedia vracia 403 na boty — odkazy si reviewner otvorí ručne; do `_source` sa píšu URL).
4. Doplň L2 polia (schéma nižšie) a otoč `human_reviewed: true`.
5. Pusher frakciu samostatne (jeden PR-ekvivalent na frakciu, žiadne miešanie).

## Stavová matica (2026-08-28)

| frakcia            | detachments | human_reviewed | reviewner / dátum |
|--------------------|------------:|:--------------:|-------------------|
| adepta-sororitas   | 8           | ✗              | |
| adeptus-custodes   | 9           | ✗              | |
| adeptus-mechanicus | 10          | ✗              | |
| aeldari            | 15          | ✗              | |
| astra-militarum    | 11          | ✗              | |
| black-templars     | 20          | ✗              | |
| blood-angels       | 24          | ✗              | |
| chaos-daemons      | 9           | ✗              | |
| chaos-knights      | 8           | ✗              | |
| chaos-space-marines| 17          | ✗              | |
| dark-angels        | 24          | ✗              | |
| death-guard        | 9           | ✗              | |
| deathwatch         | 17          | ✗              | |
| drukhari           | 9           | ✗              | |
| emperors-children  | 10          | ✗              | |
| genestealer-cults  | 9           | ✗              | |
| grey-knights       | 9           | ✗              | |
| imperial-agents    | 5           | ✗              | |
| imperial-knights   | 8           | ✗              | |
| leagues-of-votann  | 10          | ✗              | |
| necrons            | 12          | ✗              | |
| orks               | 13          | ✗              | |
| space-marines      | 23          | ✗              | |
| space-wolves       | 23          | ✗              | |
| tau-empire         | 7           | ✗              | |
| thousand-sons      | 9           | ✗              | |
| tyranids           | 10          | ✗              | |
| world-eaters       | 8           | ✗              | |
| **SPOLU**          | **346**     | **0**          | |

Presný zoznam detachmentov na frakciu: `data/config/<frakcia>/detachments.json`
(slugs), prípadne `python3 -c "import json;d=json.load(open('data/merged/<frakcia>.json'));[print(x['name']) for x in d['detachments']]"`.

## Schéma L2 — čo reviewner dopĺňa (per detachment)

```
rule: {
  text: "<KRÁTKY PARAPHRASE pravidla, 1-3 vety; NIKDY verbatim GW text>",
  _paraphrase: true,                    // povinné — IP pravidlo
  affects: ["FACTION", "PSYKER", ...],  // kľúčové slová/jednotky, ktoré pravidlo ovplyvňuje
  _source: ["https://wahapedia.ru/...", "https://newrecruit.eu/..."]
},
best_units: [ { unit, why, _source: [...] } ],   // prečo koreluje s pravidlom → traceable
scoring_units / support_units / hammer_units: ["<názvy>"],
spam: [ { unit, count, with, why, _source } ],   // čo stavať, s ktorým leaderom
combos: [ { combo, effects, _source } ],          // LEN interné (v rámci detachmentu)
strength: "Strong|Moderate|Situational|Weak",
strength_notes: "<traceable na L0 — nebezpečná formulka bez zdroja je fabrikácia>",
limitations: ["<čo detachment nerobí>"],
play_style: { summary: "<2-3 vety>", tempo_axis: "infiltration|attrition|stat-augment|castle|rush" }
```

**Význam `strength` (orientačne, nie dogma):**
- **Strong** — flexibilný naprieč väčšinou matchupov, jasný best-in-slot pre svoju obj.
- **Moderate** — konkurencieschopný v rámci svojej obj, má slabé miesta.
- **Situational** — silný len proti konkrétnym buildom; inde ho prekoná iný detachment.
- **Weak** — všeobecne prekonaný; uviesť v `limitations` prečo.

## IP pravidlo (AGENTS.md — nekompromisné)

- ⛔ **Žiadny verbatím GW rule text** — detachment pravidlá sú GW IP.
  `rule.text` = parafráza s `_paraphrase: true`; Tier 5 test to vynucuje
  (max 600 chars — skutočná parafráza je kratšia, verbatím pravidlá dlhšie).
- ✅ Body, objectives, dispositions, enhancements — MFM dáta, komitnuteľné.
- ✅ Vlastná analýza (rating, best_units why, play_style) — komitnuteľné, s `_source`.

## Otvorený konflikt — rozhodnúť pred prvým review

`docs/detachment-info-architecture.md` §5 príklad ukazuje `rule.text: "<verbatim
detachment rule text, overený Wahapedia + NewRecruit>"` — to **protirečí** AGENTS.md IP
clause („NO verbatim rule text"). Tento checklist vynucuje parafrázu. Ak chceme verbatím
text komitnúť, treba to rozhodnúť explicitne (a upraviť architektonický doc + Tier 5 test).
Dovtedy: **parafráza**.

## Review gate (per frakcia)

1. L2 polia doplnené, `human_reviewed: true` ← RUČNE reviewnuté
2. `python3 -m pytest tests/test_detachment_validation.py -q` → zelená
3. Commit len s touto frakciou; push; merge do mainu; zmazať vetvu (dojo)
4. Aktualizovať maticu (reviewner/dátum)

## Známe edge cases (dočasne akceptované)

- `imperial-agents`: slugy s čiarkou (`ordo-hereticus,-purgation-force`) — slugify
  nanormalizuje čiarky; konzistentné s merged kľúčmi, ale ugly. Prípadná úprava slugify
  = samostatný ticket (dotkne sa kľúčov).
- `leagues-of-votann`: diakritika v slugoch (`dêlve-assault-shift`) — zachovaná, konzistentné.
- `orks`: výkričníky v slugoch (`more-dakka!`) — zachované, konzistentné.