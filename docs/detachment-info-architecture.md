# Detachment Info Architecture — izolované vrstvy, žiadny kompilát kompilátu

> **Status:** platný (2026-08-28), revidovaný na **lego-kockový model** —
> docs sú STATICKÉ kocky, LLM skladá interpretácie NAŽIVO z L0–L3.
> Nadväzuje na retire mechanical detachment modifiers.
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
army + detachments sa deje **až v konkrétnom kontexte** (archetype / roster) — a to výhradne
**naživo v LLM odpovedi**, nie v žiadnom statickom súbore.

```
L4  EXPERT FILE (cache / výstup, NIE zdroj)
      resources/experts/<faction>.md  →  human-readable summary, "platný k <dátum>"
      │  ↑ LLM zlepí L0 + L2 + L3 + kontext, človek overí, uloží ako orientáciu budúcich session
      │
L3  KALKULOVANÝ RANKING (engine output — generalist, best gear)
      │  ↑ rank_units / get_findings / compute_dpp / compute_surv / compute_mob
      │    (už existujú, engine = jediné miesto výpočtu)
      │
L2  DETACHMENT VRSTVA (STATICKÉ FAKTY, nasadzovaná) — per-detachment info:
      rule (parafráza, affects, _source) + strength/strength_notes/limitations (AI rating)
      │  ↑ detach sa vyhodnocuje v kontexte army rule svojej frakcie; každý fakt má _source
      │
L0  PRVO-ZDROJE (overené, 1-kompilované, machine-readable)
      • MFM        → points, detachments[] {name, dp, objective, enhancements}
      • Wahapedia  → detachment rule text (verbatim), unit datasheets
      • NewRecruit → 2. overený zdroj (cross-check detachment/unit info)
      • BSData     → unit profily, keywords, wargear constraints
      • 40k.app    → funkcionálny cross-check detachment rules (Wahapedia 403 na botov)
```

**Jednosmerná závislosť (žiadne cykly):**

```
L0 ──▶ L2 (detach) ──▶ kontext (archetype/roster) ──▶ L4 (expert)
L0 ──▶ L3 (engine) ──┘        ↑        │
                                  LLM (NAŽIVO) ◀─┘
                               human review gate ◀─┘
```

**NIKDY:**
- ❌ L1/L2 vygenerované z L4 (expert file) — to je kompilát kompilátu
- ❌ L3 (engine) poháňaný z L1/L2/L4 — engine zostáva čistý generalist + best gear
- ❌ army-level dáta (disposition/army rule/3DP combos) vlezené do L2 — izolácia vrstiev
- ❌ unit roles / combos / play_style / "best units" uložené ako statické dáta — interpretácie
  (destilát destilátu) sa skladajú NAŽIVO LLM-om z L0–L3, nikdy sa nepersistujú
- ❌ detach pred armádou: L2 (detach) vždy odkazuje na L1 (army rule) ako svoj kontext

---

## 3. Izolácia vrstiev — prečo

Hráč / agent sa pýta na **dve rôzne veci**, ktoré sa nesmú miešať:

| Vrstva | Čo je staticky uložené | Čo odpovedá NAŽIVO |
|--------|------------------------|--------------------|
| **L0 prvo-zdroje** | fakty (body, pravidlo, datasheety) | — |
| **L2 Detachment** | STATICKÉ FAKTY: `rule` (parafráza + affects + _source), `strength`/`strength_notes`/`limitations` (AI rating, traceable) | "Čo TENTO detachment robí?" |
| **LLM (naživo)** | — | "Na aké unity bonus najlepšie platí? Kto je scoring/support?" — **skladá z L0+L2+L3**, nič neukladá |

**Detachment info = izolovaná vrstva (L2), ale nie ignorantská.** Detachment neobsahuje army
rule mechanicky — má naň **odkaz ako na svoj kontext** (`_meta.army_rule_ref`). Army rule a
kríženie medzi detachmentami (3DP combos) sú v L0/L2 datasetoch; ich **interpretácia** (ktorý
detachment s ktorým, archetypy) je výhradne **naživo v LLM odpovedi** — nikdy sa nepersistuje
(combos = destilát destilátu = KB poison).

---

## 4. Prvo-zdrojové fakty (L0) — čo zachytiť z každého zdroja

| Zdroj | Čo dáva | Overenosť | Presun |
|-------|---------|-----------|--------|
| **MFM** (`mfm/data/<slug>.yaml` → `data/merged/<slug>.json`) | `detachments[]`: name, dp, objective, enhancements; points | reviewované, community-maintained | `gen_config.py` už mapuje do `supported.json` `dispositions` |
| **Wahapedia** | detachment rule text (parafráza — verbatím text je GW IP, pozri §5/AGENTS.md), ktoré keywords/jednotky ovplyvňuje | golden/cross-check (AGENTS.md: Wahapedia nie je primárny, slúži na validáciu) — ale 403 na botov | nový scrape→`detachment_facts/` vrstva |
| **NewRecruit** | alternatívny text detachment rules + unit info | 2. overený zdroj | cross-check voči Wahapedia |
| **40k.app** | detachment rules (funkcionálne znenie) | cross-check, keď Wahapedia blokuje botov | používa sa v draftoch ako `_source` |
| **Goonhammer (tabletopbattles)** | analytické hodnotenia detachmentov/armád | analytik — **LEN 11e články** (cutoff: 11e launch jún 2026) sú autoritou pre strength; 10e články = historické, flagované, nikdy nie autorita | citácie v `strength_notes` |
| **BSData** | unit profily, keywords, wargear, squad/vehicle constraints | primárny | už v `data/merged/` |

> **11e cutoff pravidlo (2026-08-28):** analysis/strength/meta tvrdenia sa opierajú VÝHRADNE o
> články z 11th edition (vydané ≥ 2026-06-01). 10e články sa smú použiť len na mechanickú
> cross-check pravidiel, ktoré prežili nezmenené — nikdy ako autorita na strength/GT claim v 11e.

**Kľúč: `data/merged/<faction>.json` už niesie `detachments[]` z MFM** (name/dp/objective/
enhancements) — MCP `get_detachment` a `list_factions` ho dnes **nečítajú**. To je najlacnejší
overený základ L0, len ho treba sprístupniť.

---

## 5. TEMPLATE L2 — Detachment info (statické fakty, vie o army rule)

Schéma `data/config/<faction>/detachments.json` (jeden detachment). MCP `get_detachment`
render už túto schému anticipuje (`dp_cost, disposition, strength, best_for, strength_notes,
limitations, source`).

> **Každý fakt musí byť traceable na L0.** Matematika/body → MFM. Pravidlo text → Wahapedia
> verbatim + NewRecruit cross-check + 40k.app. Žiadny odkaz na expert file.
>
> **LEGO PRAVIDLO (2026-08-28):** L2 obsahuje LEN statické fakty (to, čo reviewner overí)
> + AI rating. **Unit roles, combos, spam, play_style, best units NIE SÚ v L2** — skladajú sa
> naživo LLM-om z L0+L2+L3 pri odpovedi. Ukladať ich = destilát destilátu = KB poison.

```jsonc
{
  "_meta": {
    "faction": "chaos-space-marines",
    "layer": "L2-detachment",
    "generated_from": ["mfm", "wahapedia", "newrecruit", "40k.app"],
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
      // ---- ZL2a — čo detachment robí (pravidlo, overené parafrázou) ----
      "rule": {
        "text": "<parafrázované pravidlo (mechanika, anglicky; NIKDY verbatím GW text / lore; názvy a keywordy presne)>",
        "_paraphrase": true,
        "_lang": "en",
        "_source": ["https://www.40k.app/factions/chaos-knights/detachments/..."],
        "affects": ["FACTION", "PSYKER", "DAEMON_PRINCE", "KHORNE-exclusion"]
      },
      // ---- hodnotenie (AI rating — user ho neoveruje, verí mu; traceable) ----
      "strength": "Moderate",            // Strong/Moderate/Situational/Weak
      "strength_notes": "<traceable na L0/analytika — 11e zdroje>",
      "limitations": ["<čo detachment nerobí>"]
    }
  }
}
```

### Čo L2 odpovedá (a čo NIE)

| Hráč sa pýta | Odkiaľ odpoveď |
|--------------|---------------|
| Čo TENTO detachment robí? | L2 `rule` (statický fakt) |
| Má to detach vôbec cenu? | L2 `strength`, `strength_notes`, `limitations` (AI rating) |
| Na aké unity bonus najlepšie sadne? Kto je scoring/support/hammer? Čo stavať? Ako sa hrá? | **NAŽIVO** — LLM skladá z `rule.affects` + L0 datasheetov + L3 rankov; NIKDY nie zo statického súboru |

---

## 6. L1 Army vrstva — ŽIADNY statický súbor (rozhodnuté 2026-08-28)

**`army_profile.json` (archetypes, 3DP combos, play_style armády) je ZRUŠENÝ.** Pokus:
"L2 detached facts + L1 army profile = kompletný expert model" — REJECTED userom.

Dôvod: 3DP combos a army archetypy sú **kompozícia** (A + B + army rule → herný štýl).
Ak ich LLM zapíše do súboru, vzniká statická odvodenina, ktorú:
- človek neoveril (combine facts sa nedajú "reviewovať" izolovane),
- LLM neskôr bude citovať ako fakty (destilát destilátu = KB poison),
- vrstvy sa začnú navzájom inšpirovať (L2 inšpirované L1 inšpirovaným L2).

**Namiesto súboru:** army rule + dispositions sú L0 dáta (MFM/BSData). Odpoveď na
"Ako sa hrá celá armáda / ktorý detach s ktorým?" skladá LLM **naživo** z:
- L0: army rule, dispositions, detachment constrainy (dp, tagy)
- L2: statické fakty o detachmentoch
- L3: engine ranky
- kontext otázky (roster, súper, detach point budget)

Toto je LEGO model: kocky sú statické a overené, kompozícia je vždy čerstvá a
kontextová. Skladanie je LLM silná stránka; ukladanie kompozície je jeho slabina.

---

## 7. TEMPLATE L4 — Expert file (cache, výstup)

Expert `.md` je **čitateľný súhrn pre ľudí / budúce session**, s hlavičkou platnosti.
Môže zostať v súčasnom formáte (parse_expert ho už číta), ale musí byť **labelovaný**:
*"interpretation layer, platný k <dátum>, NIE zdroj pravdy"*.

```markdown
# <Faction> — Expert Assessment (LLM reasoning cache)

> **PLATNÝ K:** 2026-08-27   |   **ZDROJE:** MFM, Wahapedia, NewRecruit, 40k.app, BSData
> **STATUS:** LLM reasoning, overený človekom ✓/✗. NIE je zdrojom pipeline.
> Vzhľad na detachment dáta: `get_detachment` (L2) — nie z tohto súboru.
```

**Pravidlo:** tento súbor sa NIKDY nečítal pipeline-om na generovanie L2. Ak áno — bug.

---

## 8. MCP tooling — alignment

| Existujúci tool | Zmena / nové |
|-----------------|--------------|
| `get_detachment` | ✅ už číta `detachments.json` (L2) — schéma sedí. Rozšíriť: čítať aj MFM `detachments[]` z `data/merged` (name/dp/objective/enhancements = overené základy). |
| `list_factions` | vypísať aj počet detachmentov z L2 + z MFM array |
| **`get_llm_contract` (NOVÉ)** | turtle-dojo mandát. Prvý tool. Definuje hranicu truth vs interpretation, `_classification: engine_output|heuristic|verbatim`, `_source` povinnosť. |
| `rank_units` / `get_findings` / `compute_*` | bez zmeny — čistý engine (generalist, best gear). |
| `get_stratagem` | detachment param už prijíma; presmerovať na L2 detached facts (ak budú). |

**Dôležité:** L2 sú **heuristic/verbatim** dáta s `_source` a `classification`. Engine (L3)
je `engine_output` a sám sa nikdy neriadi L2. MCP nesmie kombinovať detach dáta do engine
rankov — to je tá stará chyba. **Žiadny tool neukladá army tips / combos / play_style** — LLM
ich skladá naživo pri odpovedi a označuje ako interpretation (turtle-dojo output tiering).

---

## 9. Review gate — človek overí každý kompilát (Marcel rule)

Vrstvy L2/L4 sú **kompiláty** → musia prejsť ľudským overením pred tým, než sa považujú za
podklad pre odporúčanie. Pipeline:

```
1. generovať L0 fakty (MFM + Wahapedia verbatim + NewRecruit/40k.app cross-check)
2. AI zlepí L2 (detach info) — každý fakt s _source; rule = overiteľný fakt,
   strength = AI rating (traceable na 11e analytika; človek ho NEoveruje — verí mu)
3. HUMAN REVIEW: človek prejde L2 → overí rule parafrázu voči L0 → _meta.human_reviewed=true
4. Engine L3 beží nezávisle (generalist, best gear)
5. L4 expert file = merge L0+L2+L3, tiež human review
6. Odsúhlasené vrstvy → odkazy budúcich session cez MCP
```

**Hranica review:** človek overuje **fakty** (rule parafráza, affects, _source, body).
**strength/strength_notes/limitations = AI rating** — user sa vyjadril (2026-08-28): *"ja neviem
urcit strength detachmentu... budem musiet tomu verit"*. Rating sa commitne ako AI-heuristika
s traceable source, NIE ako human-verified fakt. Z toho dôvodu Tier-5 gate nevyžaduje
best_units/play_style pre `human_reviewed` — tie sú live kompozícia a v L2 vôbec nežijú.

**Shredder gate (turtle-dojo):** každý výstup ktorý interpretuje dáta prejde shredder review —
kontrola: "best" bez kontextu, implicitné role z keywordu, epistemic collapse, absent `_source`,
re-computation, ability chaining certainty, chýbajúca assumption registry.

---

## 10. Čo je *nie* v scope tohto návrhu (rozhodnuté)

- **Engine** (L3) ostáva čistý generalist + best gear. Žiadne detachment modifikátory.
- **Dispositions** (`supported.json`) ostávajú — legit MFM dáta.
- **`workspace/detachment_drafts/`** (gitignored LLM drafts) je pracovný index —
  nemožno ho považovať za overený zdroj pravdy; ide o L4-ekvivalent.
- Pipeline implementácia (scrape Wahapedia/NewRecruit/40k.app, generátory L2) je **ďalší krok**
  — tento dokument fixuje architektúru a template.

---

## 11. Otvorené otázky

1. ~~Wahapedia v AGENTS.md je "cross-check, nie primárny" — povýšiť na zdroj **verbatim detachment
   rule text**?~~ **Rozhodnuté (2026-08-28): NIE.** `rule.text` je parafráza mechaniky
   (anglicky, bez lore, názvy/keywordy presne) — verbatím pravidiel je GW IP. Body ostávajú MFM.
2. NewRecruit — verifikovať dostupnosť/scrapovateľnosť detachment rules (licencia/robots);
   Wahapedia zatiaľ 403 na botov → drafty používajú **40k.app** ako funkcionálny cross-check.
3. `get_llm_contract` — kam patriť (mcp-server/index.js), a či sa má líšiť `_classification`
   label schéma od turtle-dojo štandardu.
4. `detachments.json` L2 file — generovať do `data/config/<faction>/` (gitignored scratch) alebo
   commitnúť? (Odporúčanie: scratch + human review, commit až po odsúhlasení.)
5. ~~Ako sa L2 `army_profile.json` napája na findings gen / MCP bez leakov do L1.~~
   **ZRUŠENÉ (2026-08-28):** armáda sa nepersistuje; kompozícia je naživo v LLM.
