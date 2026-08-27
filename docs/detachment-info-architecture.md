# Detachment Info Architecture — izolované vrstvy, žiadny kompilát kompilátu

> **Status:** Návrh (2026-08-27). Nadväzuje na retire mechanical detachment modifiers.
> **Zásada (Marcel Klimo):** *všetky kompiláty musí overiť človek.* Expert file je **persistovaný
> LLM reasoning, platný v danom čase** — je to cache/výstup, NIKDY zdroj. AI si detach znalosť
> musí zlepiť z **overených 1-kompilovaných zdrojov** (Wahapedia, NewRecruit, MFM).

---

## 1. Problém, ktorý riešime

Starý mechanical detachment scoring bol fake engine output. Náhrada nesmie byť
**"kompilát kompilátu"**: expert file (`.md`) je už sám o sebe odvodenina LMM — ak z neho
vygenerujeme `detachments.json`, vznikne odvodenina odvodeniny bez overenia. Nemá to zmysel
a porušuje zásadu "všetko kompilované overí človek".

Preto: **zdrojmi pravdy sú iba 1-kompilované, overené dáta**; expert file je čitateľný výstup.

---

## 2. Vrstvy — jednosmerný tok dát (L0 → L4)

**Vrstvy sú side by side**, nie striktne hierarchické. Army rule je **fundamentálna** (definuje
herný štýl celej armády), detachmenty sa **nasadzujú na ňu** v konkrétnom kontexte a detach
**vie o army rule** (príklad: každý CSM detachment keyuje na úspešné Dark Pacts). Miešanie
army + detachments sa deje **až v konkrétnom kontexte** (archetype / roster), nie v surových vrstvách.

```
L4  EXPERT FILE (cache / výstup, NIE zdroj)
      resources/experts/<faction>.md  →  human-readable summary, "platný k <dátum>"
      │  ↑ LLM zlepí L1 + L2 + L3 + kontext, človek overí, uloží ako orientáciu budúcich session
      │
L3  KALKULOVANÝ RANKING (engine output — generalist, best gear)
      │  ↑ rank_units / get_findings / compute_dpp / compute_surv / compute_mob
      │    (už existujú, engine = jediné miesto výpočtu)
      │
L1  ARMY VRSTVA (fundamentálna) — Army Rule + DISPOSITION + herný štýl armády
      │  ↑ armáda je základ; detachmenty (L2) sa hrajú V RÁMCI army rule, nie mimo neho
      │
L2  DETACHMENT VRSTVA (nasadzovaná, S VEDOMÍM O ARMY RULE) — per-detachment info
      │  ↑ detach sa vyhodnocuje v kontexte army rule svojej frakcie; každý fakt má _source
      │
L0  PRVO-ZDROJE (overené, 1-kompilované, machine-readable)
      • MFM        → points, detachments[] {name, dp, objective, enhancements}
      • Wahapedia  → detachment rule text (verbatim), unit datasheets
      • NewRecruit → 2. overený zdroj (cross-check detachment/unit info)
      • BSData     → unit profily, keywords, wargear constraints
```

**Jednosmerná závislosť (žiadne cykly):**

```
L0 ──▶ L1 (army) ──┐
L0 ──▶ L2 (detach) ─┤──▶ kontext (archetype/roster) ──▶ L4 (expert)
L0 ──▶ L3 (engine) ─┘        ↑                                 │
L1 ───▶ L2 (detach vie o army rule)                            │
                                               human review gate ◀┘
```

**NIKDY:**
- ❌ L1/L2 vygenerované z L4 (expert file) — to je kompilát kompilátu
- ❌ L3 (engine) poháňaný z L1/L2/L4 — engine zostáva čistý generalist + best gear
- ❌ army-level dáta (disposition/army rule/3DP combos) vlezené do L2 — izolácia vrstiev
- ❌ detach pred armádou: L2 (detach) vždy odkazuje na L1 (army rule) ako svoj kontext

---

## 3. Izolácia vrstiev — prečo

Hráč / agent sa pýta na **dve rôzne veci**, ktoré sa nesmú miešať:

| Vrstva | Otázka, na ktorú odpovedá |
|--------|---------------------------|
| **L1 Army** | *"Ako sa hrá CELÁ armáda? Aký je Army Rule a herný štýl (disposition)? Ktoré detachments sa dajú nasadiť a ako tvoria kontext (3DP combos)?*" |
| **L2 Detachment** | *"Čo TENTO detachment robí — v rámci svojej frakcie? Na aké unity bonusy najlepšie platí? Kto je scoring / support? Aký spam ktorej unity s ktorým leaderom? Ako sa hrá, keď je nasadený na army rule?"* |

**Detachment info = izolovaná vrstva (L2), ale nie ignorantská.** Detachment neobsahuje army
rule mechanicky — má naň **odkaz ako na svoj kontext** (`_meta.army_rule_ref`). Army rule a
kríženie medzi detachmentami patria do **L1 (army)**. Detach `combos` v L2 sú len **interné**
(v rámci jedného detachmentu); 3DP combos (kríženie detachmentov) patria do L1 kontextu.

---

## 4. Prvo-zdrojové fakty (L0) — čo zachytiť z každého zdroja

| Zdroj | Čo dáva | Overenosť | Presun |
|-------|---------|-----------|--------|
| **MFM** (`mfm/data/<slug>.yaml` → `data/merged/<slug>.json`) | `detachments[]`: name, dp, objective, enhancements; points | reviewované, community-maintained | `gen_config.py` už mapuje do `supported.json` `dispositions` |
| **Wahapedia** | detachment rule text (verbatim), ktoré keywords/jednotky ovplyvňuje | golden/cross-check (AGENTS.md: Wahapedia nie je primárny, slúži na validáciu) | nový scrape→`detachment_facts/` vrstva |
| **NewRecruit** | alternatívny text detachment rules + unit info | 2. overený zdroj | cross-check voči Wahapedia |
| **BSData** | unit profily, keywords, wargear, squad/vehicle constraints | primárny | už v `data/merged/` |

**Kľúč: `data/merged/<faction>.json` už niesie `detachments[]` z MFM** (name/dp/objective/
enhancements) — MCP `get_detachment` a `list_factions` ho dnes **nečítajú**. To je najlacnejší
overený základ L0, len ho treba sprístupniť.

---

## 5. TEMPLATE L2 — Detachment info (nasadzovaná vrstva, vie o army rule)

Schéma `data/config/<faction>/detachments.json` (jeden detachment). MCP `get_detachment`
render už túto schému anticipuje (`dp_cost, disposition, strength, best_for, strength_notes,
limitations, source`).

> **Každý fakt musí byť traceable na L0.** Matematika/body → MFM. Pravidlo text → Wahapedia
> verbatim + NewRecruit cross-check. Žiadny odkaz na expert file.

```jsonc
{
  "_meta": {
    "faction": "chaos-space-marines",
    "layer": "L2-detachment",
    "generated_from": ["mfm", "wahapedia", "newrecruit"],
    "generated": "2026-08-27",
    "human_reviewed": false,          // ← review gate, pozri §9
    "army_rule_ref": "dark-pacts"     // ← detach VIE o army rule (L1) ako o svojom kontexte
  },
  "detachments": {
    "cabal-of-chaos": {
      "_id": "cabal-of-chaos",
      "_slug": "cabal-of-chaos",
      "dp_cost": 1,
      "disposition": "disruption",
      "name": "Cabal Of Chaos",
      "objective": "DISRUPTION",
      // ---- ZL2a — čo detachment robí (pravidlo, verbatim z Wahapedia) ----
      "rule": {
        "text": "<verbatim detachment rule text, overený Wahapedia + NewRecruit>",
        "_source": ["https://wahapedia.ru/wh40k11ed/factions/...", "https://newrecruit.eu/..."],
        "affects": ["FACTION", "PSYKER", "DAEMON_PRINCE", "KHORNE-exclusion"]
      },
      // ---- ZL2b — na aké unity bonusy najlepšie platí (synergia) ----
      "best_units": [
        {
          "unit": "Exalted Sorcerer",
          "why": "<traceable na L0: s akým bonusom pravidla koreluje, nie subjektívny dojem>",
          "_source": "..."
        }
      ],
      // ---- ZL2c — úloha v armáde v rámci tohto detachmentu ----
      "scoring_units": ["<názvy>"],
      "support_units": ["<názvy>"],
      "hammer_units": ["<názvy>"],
      // ---- ZL2d — spam + leaders (čo stavať, v čom) ----
      "spam": [
        {
          "unit": "...",
          "count": "3×",
          "with": "Leader X",
          "why": "<L0-odvodené>",
          "_source": "..."
        }
      ],
      // ---- ZL2e — komba V RÁMCI tohto detachmentu (nie kríženie detachmentov) ----
      "combos": [
        {
          "combo": "<A + B>",
          "effects": "<ako sa vzájomne podporujú v hernom štýle tohto detachmentu>",
          "_source": "..."
        }
      ],
      // ---- hodnotenie (len L2 záleží) ----
      "strength": "Moderate",            // Strong/Moderate/Situational/Weak
      "strength_notes": "<traceable na L0>",
      "limitations": ["<čo detachment nerobí>"],
      "play_style": {
        "summary": "<ako sa v ňom hrá — 2-3 vety, L0-odvodené>",
        "tempo_axis": "infiltration | attrition | stat-augment | castle | rush"
      }
    }
  }
}
```

### Polia = odpovede na "čo hráčov zaujíma"

| Hráč sa pýta | Pole v L2 |
|--------------|-----------|
| Ako sa to hrá? | `play_style.summary`, `play_style.tempo_axis` |
| Na aké unity bonus najviac sadne? | `best_units[]` (s `why` traceable) |
| Kto je scoring / support / hammer? | `scoring_units / support_units / hammer_units` |
| Aký spam ktorej unity s ktorým leaderom? | `spam[]` (unit, count, with, why) |
| Aké komba v rámci detachmentu? | `combos[]` |
| Má to detach vôbec cenu? | `strength`, `strength_notes`, `limitations` |

---

## 6. TEMPLATE L1 — Army profile (fundamentálna vrstva)

Styl hrania = **ARMY RULE + DISPOSITION** + **3DP combos** (kontext). Odvodené z L0 + L2, nie z expert.

```jsonc
{
  "_meta": {
    "faction": "chaos-space-marines",
    "layer": "L1-army",
    "generated_from": ["mfm", "supported.json", "detachments.json(L2)", "wahapedia", "newrecruit"],
    "human_reviewed": false
  },
  "army_rule": {
    "name": "Dark Pacts",
    "text": "<verbatim>",
    "_source": ["wahapedia", "newrecruit"]
  },
  "archetypes": [
    {
      "id": "disruption-infiltration",
      "disposition": "disruption",
      "play_style": "<ako hrá ako CELÁ armáda — tempo/osobitosti>",
      "core_detachments": ["deceptors", "nightmare-hunt", "cabal-of-chaos"],  // → L2 _id
      // ---- 3DP combos: max 3 detachments na 2000p (kontext, nie L2) ----
      "combos": [
        {
          "dp": 3,
          "roster": [
            { "det": "deceptors", "dp": 1, "role": "board-presence" },
            { "det": "nightmare-hunt", "dp": 1, "role": "attrition" },
            { "det": "cabal-of-chaos", "dp": 1, "role": "psyker-hammer" }
          ],
          "why": "<ako sa vzájomne podporujú — kríženie medzi detachmentami patrí TU (L1), nie do L2>",
          "synergy_notes": "<L0/L2-odvodené, v kontexte army rule>"
        }
      ],
      "net_list_priorities": ["infiltration pressure", "battle-shock attrition"],
      "scoring_hint": "<ktoré formácie držia objekty>"
    }
  ]
}
```

> **Leak guard:** 3DP combos = kríženie detachmentov → **patria do L1 (army kontext)**, NIE do L2.
> L2 `combos` sú len interné (v rámci jedného detachmentu). Ak by sa objavili v L1 combos
> per-detachment detaily, je to leak a Shredder to chytí.

---

## 7. TEMPLATE L4 — Expert file (cache, výstup)

Expert `.md` je **čitateľný súhrn pre ľudí / budúce session**, s hlavičkou platnosti.
Môže zostať v súčasnom formáte (parse_expert ho už číta), ale musí byť **labelovaný**:
*"interpretation layer, platný k <dátum>, NIE zdroj pravdy"*.

```markdown
# <Faction> — Expert Assessment (LLM reasoning cache)

> **PLATNÝ K:** 2026-08-27   |   **ZDROJE:** MFM, Wahapedia, NewRecruit, BSData
> **STATUS:** LLM reasoning, overený človekom ✓/✗. NIE je zdrojom pipeline.
> Vzhľad na detachment dáta: `get_detachment` (L1) — nie z tohto súboru.

## Army Rules & Detachments — Expert Assessment
<existujúci formát; všetky fakty traceable na L0 _source>
```

**Pravidlo:** tento súbor sa NIKDY nečítalo pipeline-om na generovanie L1/L2. Ak áno — bug.

---

## 8. MCP tooling — alignment

| Existujúci tool | Zmena / nové |
|-----------------|--------------|
| `get_detachment` | ✅ už číta `detachments.json` (L1) — schéma sedí. Rozšíriť: čítať aj MFM `detachments[]` z `data/merged` (name/dp/objective/enhancements = overené základy). |
| `list_factions` | vypísať aj počet detachmentov z L1 + z MFM array |
| **`get_llm_contract` (NOVÉ)** | turtle-dojo mandát. Prvý tool. Definuje hranicu truth vs interpretation, `_classification: engine_output|heuristic|verbatim`, `_source` povinnosť. |
| **`get_army_profile` (NOVÉ, alebo rozšíriť get_detachment)** | číta L2 `army_profile.json` — styl, archetypes, 3DP combos. |
| `rank_units` / `get_findings` / `compute_*` | bez zmeny — čistý engine (generalist, best gear). |
| `get_stratagem` | detachment param už prijíma; presmerovať na L1 detached facts (ak budú). |

**Dôležité:** L1/L2 sú **heuristic/verbatim** dáta s `_source` a `classification`. Engine (L3)
je `engine_output` a sám sa nikdy neriadi L1/L2. MCP nesmie kombinovať detach dáta do engine
rankov — to je tá stará chyba.

---

## 9. Review gate — človek overí každý kompilát (Marcel rule)

Vrstvy L1/L2/L4 sú **kompiláty** → musia prejsť ľudským overením pred tým, než sa považujú za
podklad pre odporúčanie. Pipeline:

```
1. generovať L0 fakty (MFM + Wahapedia verbatim + NewRecruit cross-check)
2. AI zlepí L1 (detach info) a L2 (army profile) — každý fakt s _source
3. HUMAN REVIEW: človek prejde L1/L2, opraví/odsúhlasí  →  _meta.human_reviewed=true
4. Engine L3 beží nezávisle (generalist, best gear)
5. L4 expert file = merge L1+L2+L3, tiež human review
6. Odsúhlasené vrstvy → odkazy budúcich session cez MCP
```

**Shredder gate (turtle-dojo):** každý výstup ktorý interpretuje dáta prejde shredder review —
kontrola: "best" bez kontextu, implicitné role z keywordu, epistemic collapse, absent `_source`,
re-computation, ability chaining certainty, chýbajúca assumption registry.

---

## 10. Čo je *nie* v scope tohto návrhu (rozhodnuté)

- **Engine** (L3) ostáva čistý generalist + best gear. Žiadne detachment modifikátory.
- **Dispositions** (`supported.json`) ostávajú — legit MFM dáta.
- **`workspace/detachment_research/`** (Faction Pack corpus) je gitignored scratch —
  nemožno ho považovať za overený zdroj pravdy; ide o L4-ekvivalent.
- Pipeline implementácia (scrape Wahapedia/NewRecruit, generátory L1/L2) je **ďalší krok**
  — tento dokument fixuje architektúru a template.

---

## 11. Otvorené otázky

1. Wahapedia v AGENTS.md je "cross-check, nie primárny" — povýšiť na zdroj **verbatim detachment
   rule text**? (Body ostávajú MFM; pravidlo text môže byť Wahapedia.)
2. NewRecruit — verifikovať dostupnosť/scrapovateľnosť detachment rules (licencia/robots).
3. `get_llm_contract` — kam patriť (mcp-server/index.js), a či sa má líšiť `_classification`
   label schéma od turtle-dojo štandardu.
4. `detachments.json` L1 file — generovať do `data/config/<faction>/` (gitignored scratch) alebo
   commitnúť? (Odporúčanie: scratch + human review, commit až po odsúhlasení.)
5. Ako sa L2 `army_profile.json` napája na findings gen / MCP bez leakov do L1.
