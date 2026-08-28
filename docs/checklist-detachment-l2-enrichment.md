# Checklist — L2 Detachment Expert Review (346 detachmentov, 30 frakcií)

> **Browser view:** `docs/detachment-atlas/` — per-army pages s oddelenými vrstvami
> L0–L4 (`index.html` + `<faction>.html`; generuje `scripts/gen_detach_review_html.py`,
> Tier 6 test drží current). Jeden spoločný workbook už NEEXISTUJE (2026-08-28).
> **Účel:** podklad pre ľudský review gate (turtle-dojo / Marcel rule: každý kompilát
> overí človek). Keď je frakcia odsúhlasená, reviewner otočí `_meta.human_reviewed: true`.
> Automatické zámky: `tests/test_detachment_validation.py` — Tier 4 (scaffold L0-traceable)
> + Tier 5 (L2 enrichment gate) + Tier 6 (HTML atlas current). Zelená sada = skeleton;
> review je ľudská robota.

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
  text: "<KRÁTKY PARAPHRASE pravidla (mechanika, 1-3 vety, ANGLICKY);
         NIKDY verbatím GW text, NIKDY lore>",
  _paraphrase: true,                    // povinné — IP pravidlo
  _lang: "en",                          // povinné — anglicky
  affects: ["FACTION", "PSYKER", ...],  // kľúčové slová/jednotky, ktoré pravidlo ovplyvňuje
  _source: ["https://www.40k.app/factions/..."]
},
strength: "Strong|Moderate|Situational|Weak",
strength_notes: "<traceable na L0/11e analytika — nebezpečná formulka bez zdroja je fabrikácia>",
limitations: ["<čo detachment nerobí>"]
```

> **LEGO PRAVIDLO (2026-08-28):** L2 = statické fakty len. `best_units`,
> `scoring_units`/`support_units`/`hammer_units`, `spam`, `combos`, `play_style`
> NIE SÚ v L2 — LLM ich skladá **naživo** z `rule.affects` + L0 datasheetov + L3
> rankov. Persistovať ich = destilát destilátu = KB poison (Tier 5/6 to vynucuje).

**Význam `strength` (AI rating, nie human-verifikovaný fakt):**
- **Strong** — flexibilný naprieč väčšinou matchupov, jasný best-in-slot pre svoju obj.
- **Moderate** — konkurencieschopný v rámci svojej obj, má slabé miesta.
- **Situational** — silný len proti konkrétnym buildom; inde ho prekoná iný detachment.
- **Weak** — všeobecne prekonaný; uviesť v `limitations` prečo.

> **11e cutoff (2026-08-28):** `strength_notes` sa opierajú o články z 11th edition
> (≥ 2026-06-01). 10e články = historické, flagované, nikdy autorita pre strength.

## IP pravidlo + rule.text pravidlá (rozhodnuté 2026-08-28)

`rule.text` je **parafráza mechaniky**, nie GW text a nie lore:

- ⛔ **Žiadny verbatím GW rule text** — detachment pravidlá sú GW IP.
  Parafráza bez GW-specifickej formulácie (vlastné slová, nie GW frázovanie).
- ⛔ **Žiadny lore** — žiadne príbehové/flavour vety („ancient relics of…", „tales of…").
  Text opisuje IBA mechanické efekty (čo pravidlo robí herne).
- 🇬🇧 **Anglicky** — `_lang: "en"` (vynútené Tier 5).
- 🔑 **Názvy detachmentov a keywordy PRESNE** — „Cabal Of Chaos", „PSYKER",
  „FACTION: …" sa nemenia, neprekladajú, neskracujú. Sú to dáta (identifikátory),
  nie proza. To isté pre `rule.affects[]`.
- ✅ Body, objectives, dispositions, enhancements — MFM dáta, komitnuteľné.
- ✅ Vlastná analýza (`strength`/`strength_notes`) — komitnuteľné, s `_source`.

## Otvorený konflikt — rozhodnuté

`docs/detachment-info-architecture.md` §5 príklad ukazoval `rule.text: "<verbatim
detachment rule text, overený Wahapedia + NewRecruit>"` — protirečilo AGENTS.md IP
clause („NO verbatim rule text"). **Rozhodnuté (2026-08-28): parafráza**, anglicky, bez
lore, názvy/keywordy presne. Architektonický doc už hovorí parafrázu; Tier 5 test
vynucuje `_paraphrase: true`, `_lang: "en"`, max 600 chars.

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