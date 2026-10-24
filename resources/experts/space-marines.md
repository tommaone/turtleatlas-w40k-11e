# Space Marines — 11th Edition Expert

The Adeptus Astartes are the Imperium's elite warrior-monks. 11e SM are a flexible, durable
midrange army with strong melee and shooting. Their army-wide rule **Combat Doctrines**
gives every unit one of three doctrine states to build its turn around, and most 11e
detachments are doctrine packages rather than one-off buffs.

---

## Critical 11e Rule for SM

**COMBAT DOCTRINES:** At the start of your Command phase you select one doctrine —
Assault, Devastator or Tactical — and it is active for friendly Astartes units with the
ability until your next Command phase. Assault lets a unit charge after it Advances;
Devastator gives its ranged attacks Assault; Tactical lets it shoot and then charge after
a Fall-back. Each doctrine can be selected once per battle, and only one is active per
unit. Sourced: BSData 9b8207c (rule `Combat Doctrines`, Astartes library).

This means:
- The doctrine is chosen once per Command phase — you are picking what the unit does, not buffing a target
- Most 11e SM detachments are doctrine packages (Codex Discipline, Mastered Doctrines, Assault/Tactical/Devastator Mastery)
- A unit with no doctrine active plays as a plain marine — plan the Command phase around it

---

## Unit Profiles (from BSData 11e)

### Battleline

| Unit | M | T | SV | W | OC | Pts |
|------|---|---|----|---|----|----:|
| Intercessor Squad (×5) | 6" | 4 | 3+ | 2 | 1 | 80 |
| Assault Intercessor Squad (×5) | 6" | 4 | 3+ | 2 | 1 | 75 |

### Elites

| Unit | M | T | SV | W | OC | Pts |
|------|---|---|----|---|----|----:|
| Terminator Squad (×5) | 5" | 5 | 2+ | 3 | 1 | 160 |
| Terminator Assault Squad (×5) | 5" | 5 | 2+ | 3 | 1 | 155 |
| Sternguard Veteran Squad (×5) | 6" | 4 | 3+ | 2 | 1 | 100 |
| Bladeguard Veteran Squad (×3) | 6" | 4 | 3+ | 2 | 1 | 80 |
| Devastator Squad (×5) | 6" | 4 | 3+ | 2 | 1 | 120 |
| Hellblaster Squad (×5) | 6" | 4 | 3+ | 2 | 1 | 110 |

### Characters

| Unit | M | T | SV | W | OC | Pts |
|------|---|---|----|---|----|----:|
| Captain | 6" | 4 | 3+ | 5 | 1 | 80 |
| Captain In Terminator Armour | 5" | 5 | 2+ | 6 | 1 | 85 |
| Librarian | 6" | 4 | 3+ | 4 | 1 | 60 |
| Librarian In Terminator Armour | 5" | 5 | 2+ | 5 | 1 | 75 |
| Chaplain | 6" | 4 | 3+ | 4 | 1 | 60 |
| Chaplain In Terminator Armour | 5" | 5 | 2+ | 5 | 1 | 75 |

### Vehicles

| Unit | M | T | SV | W | OC | Pts |
|------|---|---|----|---|----|----:|
| Dreadnought | 6" | 9 | 2+ | 8 | 3 | 135 |
| Brutalis Dreadnought | 8" | 10 | 2+ | 12 | 4 | 150 |
| Ballistus Dreadnought | 8" | 10 | 2+ | 12 | 4 | 150 |
| Redemptor Dreadnought | 8" | 10 | 2+ | 12 | 4 | 195 |
| Land Raider | 10" | 12 | 2+ | 16 | 5 | 220 |
| Rhino | 12" | 9 | 3+ | 10 | 2 | 75 |
| Impulsor | 12" | 9 | 3+ | 11 | 2 | 80 |

---

## Detachments

The 11e roster is engine data, not prose: name, DP cost and the dispositions
each detachment queues for live in `data/merged/space-marines.json` (MFM 1.5,
11e) and are what the Key Insights card renders. The 11e roster
(22 detachments):

- 1DP: Assault Brethren (take and hold); Deathwatch Support (disruption); Devastator Brethren (purge the foe); Gauntlet Task Force (reconnaissance); Gravis Linebreaker Force (take and hold); Gravis Siege Force (take and hold); Ironclad Champions (priority assets); Ironstorm Spearhead (purge the foe); Phobos Shadow Force (disruption); Phobos Shock Force (disruption); Stormlance Task Force (reconnaissance); Tactical Brethren (priority assets); Tacticus Attack Force (take and hold); Tacticus Firestorm Force (priority assets); Terminator Storm Force (priority assets).
- 2DP: Ceramite Sentinels (take and hold); Forgefather’S Seekers (priority assets); Medusa'S Wrath (purge the foe); Shadowmark Talon (disruption); Spearpoint Task Force (reconnaissance).
- 3DP: Blade Of Ultramar (take and hold, priority assets); Gladius Task Force (take and hold, priority assets).

Per-detachment expert assessment (rating + research trail) is in "Detachment
Assessments" below. The blocks there are the 10e research record: a name that
still exists in 11e keeps its rating only if the 11e package still queues for
the disposition the rating was judged for, and its prose still describes the
10e rule.

## Disposition Ranking

| Tier | Disposition | Why |
|------|-------------|-----|
| 🟢 **S** | **Purge the Foe** | SM kill things. Dreadnoughts, Devastators, Terminator melee. Natural fit. |
| 🟢 **A** | **Priority Assets** | Terminators, Dreadnoughts and characters are the army's best assets. Protect key units. |
| 🟡 **B** | **Take and Hold** | SM have decent OC (Dreadnoughts OC 3-4). Solid but less kill pressure. |
| 🟠 **C** | **Reconnaissance** | Action-heavy. SM want to push and kill, not sit doing actions. |
| 🔴 **D** | **Disruption** | Screening/denial. SM lack cheap screening units compared to GK. |

---

## Top Competitive Combinations (3DP at 2000pts)

### 🟢 S-Tier

1. **Ironstorm Spearhead** (2DP, Purge) — Vehicle-focused. Dreadnoughts + Land Raider with reroll 1s. Best pure damage output.
2. **Firestorm Assault Force** (2DP, Purge) — Short-range AP bonus. Good with Melta/Plasma.

### 🟡 A-Tier

3. **Gladius Task Force** (3DP, Priority) — Default, flexible. Good for all-comers.
4. **Stormlance Task Force** (3DP, Disrupt) — Mobility focused. Bikers/jump packs.

### 🟠 B-Tier

5. **Ceramite Sentinels** (3DP, TaH) — Defensive, good for objective play.
6. **Vanguard Spearhead** (2DP, Recon) — Stealth focused, niche.

### Key Rules

**Combat Doctrines is the strongest army-wide lever in the game.** Every unit with the
ability participates, and a detachment that adds doctrine uses (Codex Discipline, Mastered
Doctrines) turns that into extra swings. Combined with high-quality weapons (Lascannons,
Melta), SM output is consistent and high.

---

## Deployment & Reserves Rules (11e)

- **No Reserves arrive Turn 1.** First arrival is Turn 2.
- **Reserves cap (Strike Force):** max 1000pts OR half your total units (whichever is more restrictive).
- SM have access to Deep Strike via Terminators and Teleport Assault.
- Land Raider can transport Terminators — useful for protected delivery.

---

## How To Play Space Marines (Turn-by-Turn)

### Deployment & Turn 1
- Deploy half your army on the board.
- Put Terminators/Deep Strike units into reserves (arrive Turn 2+).
- Dreadnoughts hold centre or push flanks.
- Use cover — SM are T4, 3+ save in power armour.

### Turn 2–3 (Strike Window)
- Deep Strike units arrive. Terminators land on objectives or behind enemy lines.
- Devastator doctrine on the units that need to shoot and close.
- Dreadnoughts push up with support.
- Devastators hold backfield and shoot.

### Turn 4–5 (Cleanup)
- Hold objectives with Terminators/Dreadnoughts.
- Switch the doctrine to match the endgame (Assault for a last-charge turn).
- Characters support with buffs.

---

## Key Gotchas

1. **Combat Doctrines is per-unit, not per-army** — a doctrine is active for units with the ability; a unit without it plays plain
2. **Terminators have 5+ invuln, not 4+** — Grey Knights have 4+, SM only 5+
3. **No native FNP on any SM unit** — unlike Grey Knights' Rhino FNP 6+ vs mortals
4. **Dreadnoughts are the DPP kings** — Multi-melta Dreadnought beats most infantry on DPP
5. **Terminators are the SURV wall** — 2.2 turns, best in the faction
6. **Land Raider is expensive but tough** — 16W, T12, 2+ save. Best transport + fire support
7. **SM lack cheap screening units** — compared to GK's 80pt Strike Squads

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/space-marines.json (2026-08-23,
packs v1.1); shared-codex deltas cross-checked against
workspace/detachment_research/_space-marines-shared.json. That shared file
warns several dispositions in the faction JSON contradict official sources
(see per-detachment ⚠️ flags) and records a three-way disagreement on 1st
Company Task Force's disposition — treat affected labels as provisional.

### Army Rule
- **Army Rule Rating**: Moderate — Combat Doctrines is the Adeptus Astartes army rule in 11e: pick one of three doctrines at the start of your Command phase, active for friendly Astartes units with the ability until the next Command phase. Assault Doctrine lets a unit charge after it Advances; Devastator Doctrine gives its ranged attacks Assault; Tactical Doctrine lets it shoot and charge after a Fall-back. Each doctrine can be selected once per battle and only one is active per unit. Sourced: BSData 9b8207c (rule `Combat Doctrines`, Astartes library) + GW Space Marines rules preview 2026-09-10.
- **Oath of Moment (RETIRED as army rule)**: Oath of Moment was the Astartes army rule through the June/July 2026 11e Faction Packs (re-roll hits against the Oath target, plus +1 wound for pure-vanilla lists). Codex: Space Marines (released 2026-10-03) removed it and replaced it with Combat Doctrines. The term survives only in BSData as a reference inside a few character/campaign entries (e.g. Master of the Deathwing, Chapter Command) — not as a rule entity. Sourced: BSData 9b8207c (no entity named "Oath of Moment" exists; SM army-rule infoLinks are `Combat Doctrines` + `Templar Vows`); GW preview 2026-09-10.
- **Play pattern** *(interpretation)*: the broadest detachment list in the game (22 packages), but 11e re-cut the roster around generic Astartes packages — Assault/Tactical/Devastator Brethren, Gauntlet, Gladius, Tacticus x2, Terminator Storm Force, Phobos x2, Gravis x2 — plus a few signature ones (Blade of Ultramar, Spearpoint, Shadowmark Talon, Stormlance, Ceramite Sentinels, Forgefather's Seekers, Ironstorm Spearhead). List identity starts with the doctrine/package choice, not with a bespoke detachment per playstyle.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Gravis Siege Force (Indomitable Defence — -1 wound on high-S attacks within objective range) and Gravis Linebreaker Force (Walking Fortress — mobile, +1-hit shooting after a move) are the objective anchors; Gladius Task Force (Codex Discipline) and Blade Of Ultramar (Mastered Doctrines) buy extra doctrine uses for the same job, and Ceramite Sentinels (Adaptive Defence) trades movement for terrain-held entrenchment. |
| Purge the Foe | Moderate | Devastator Brethren (Devastator Mastery) and Ironstorm Spearhead (Ironstorm Auto-Targeters — re-roll a hit and a wound on vehicle fire) are the dedicated killers; Medusa's Wrath gives one reroll per attack across the army. Single-roll rerolls, not the old army-wide target buff. |
| Reconnaissance | Moderate | Gauntlet Task Force (Combined Deployment — transport disembarks feed Sustained Hits 1) and Spearpoint Task Force (extra assault/tactical doctrine, +1 advance for mounted) are the movement tools; Stormlance Task Force (Lightning-Fast Strike) is the melee-tempo option. |
| Priority Assets | Strong | Gladius Task Force and Blade Of Ultramar headline, with Forgefather's Seekers (extra devastator doctrine, +1 S within 12"), Ironclad Champions (Dreadnoughts re-roll hits of 1), Terminator Storm Force (+1 charge for Terminators) and Tacticus Firestorm Force (Rapid Fire at full range). |
| Disruption | Moderate | Phobos Shadow Force / Phobos Shock Force (Vanguard Ambushers — re-roll wound 1 against a hidden Phobos) and Shadowmark Talon (Stealth, -3" detection) are the real screening tools; Stormlance/Spearpoint advance-and-charge fits melee lists, but Disruption itself stays niche. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->
<!-- one block per detachment, ordered by DP -->

#### Fulguris Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Land Speeder / Storm Speeder variants gain SPEEDER keyword; SPEEDER units make an ingress move in the first Movement phase.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Storm Speeder speeder-wing alpha strikes; no effect on standard infantry (shared-corpus note).
- **Limits**: Turn-1 ingress, SPEEDER units only; deployment mechanic with no numeric expression. ⚠️ Shared-codex delta: official sources list Fulguris as DISRUPTION, not RECONNAISSANCE.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Librarius Conclave (1DP → RECONNAISSANCE)
- **Mechanics**: Pick one Psychic Discipline per battle round for all PSYKER units (changeable): Biomancy +2" M; Divination re-roll hit/wound 1s; Pyromancy +1 AP ranged within 12"; Telekinesis -1 S vs incoming ranged; Telepathy ignore BS/WS/hit modifiers.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Chief Librarian Tigurius-led psyker density; Divination is the strongest offensive pick per the research note.
- **Limits**: Rotation means nothing is always-on; PSYKER scope only; no stratagems in this detachment per the shared corpus. ⚠️ Source conflict on scope: shared corpus reads the discipline pick as per-Librarian-and-squad; this faction file as one discipline for ALL PSYKER units — materially different strength, unresolved.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Subversion Assets (1DP → DISRUPTION)
- **Mechanics**: PHOBOS and SCOUT SQUAD units mark one visible enemy within 12" as detected in Shooting phase; detected units gain +3" detection range.
- **Rating**: Situational for Disruption
- **Synergies**: Infiltrator Squad / Incursor Squad screening packages.
- **Limits**: Detection utility unrepresentable numerically; PHOBOS/SCOUT SQUAD + LOS restrictions (research). ⚠️ Shared-codex delta: official sources list Subversion Assets as RECONNAISSANCE, not DISRUPTION.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vengeful Hosts (1DP → TAKE AND HOLD)
- **Mechanics**: In any turn a friendly FLY INFANTRY unit made an ingress or charge move, its attacks re-roll hit rolls of 1.
- **Rating**: Situational for Take and Hold
- **Synergies**: Assault Intercessors With Jump Packs charge turns.
- **Limits**: ⚠️ Research confidence LOW: disposition field taken from task brief, NOT confirmed by fetched sources; dp=1 sourced second-hand (research UNCONFIRMED FIELDS note). Reroll strictly conditional on ingress/charge that turn.
- **_source**: https://www.tabletopbattles.com/detachment-focus-vengeful-hosts

#### 1st Company Task Force (2DP → PURGE THE FOE)
- **Mechanics (10e record)**: Once per battle, activate in a Command phase: models with Oath of Moment also re-roll Wound rolls vs the current Oath target until next Command phase.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Terminator-heavy first-company pushes focusing one target.
- **Limits**: Once-per-battle; single designated target only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Anvil Siege Force (2DP → TAKE AND HOLD)
- **Mechanics**: All ranged weapons gain HEAVY; weapons that already had HEAVY gain +1 to Wound if the unit Remained Stationary that turn.
- **Rating**: Moderate for Take and Hold (static gunlines)
- **Synergies**: Devastator Squad / Desolation Squad / Eliminator Squad static fire bases.
- **Limits**: HEAVY penalizes moved-turn shooting (-1 to hit) — net value depends on how static the list plays (research stale note).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Bastion Task Force (2DP → TAKE AND HOLD)
- **Mechanics**: BATTLELINE units can shoot/charge/perform Actions after Advancing or Falling Back; after BATTLELINE attacks, one enemy unit hit becomes auspex scanned (all army attacks re-roll hit rolls of 1 vs it until end of turn).
- **Rating**: Moderate for Take and Hold
- **Synergies**: Intercessor Squad / Heavy Intercessor flood feeding scan rerolls to elite shooters.
- **Limits**: Mobility eligibility restricted to BATTLELINE; scan reroll conditional on a Battleline unit hitting the target earlier that turn (research stale note).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Emperor'S Shield (2DP → PURGE THE FOE)
- **Mechanics (10e record)**: Oath of Moment bearers re-roll Wound rolls of 1 vs the Oath target; DARNATH LYSANDER's unit re-rolls ALL Wound rolls vs the Oath target. IMPERIAL FISTS-only.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Darnath Lysander leading a Terminator Squad into the declared threat.
- **Limits (10e record)**: Chapter-locked; wound re-rolls apply only vs the single Oath target; full re-roll needs the specific character (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Firestorm Assault Force (2DP → PRIORITY ASSETS)
- **Mechanics**: All ranged weapons gain ASSAULT; ranged attacks within 12" get +1 Strength.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Infernus Squad, Eradicator Squad, Aggressor Squad — short-range volume benefits most.
- **Limits**: +1 Strength mapping depends on target Toughness — no universal modifier exists (research); ⚠️ shared-corpus delta flags official sources listing Firestorm as PURGE THE FOE, contradicting this file's PRIORITY ASSETS.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Forgefather'S Seekers (2DP → PRIORITY ASSETS)
- **Mechanics**: Same ranged buff as Firestorm (ASSAULT on all ranged, +1 Strength within 12"). With VULKAN HE'STAN, INFERNUS SQUADs can shoot after starting Actions or start Actions after Advancing. SALAMANDERS-only.
- **Rating**: Situational for Priority Assets (chapter-locked overlap with Firestorm)
- **Synergies**: Infernus Squad + Vulkan He'Stan action-shooting loops.
- **Limits**: Chapter-locked; same +1 Strength modeling limits as Firestorm.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Hammer Of Avernii (2DP → PURGE THE FOE)
- **Mechanics (10e record)**: Oath of Moment bearers re-roll Wound rolls of 1 vs the Oath target; once per battle round, if CAANOK VAR is on the field, a new visible enemy becomes the Oath target when the old one dies. IRON HANDS-only.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Caanok Var keeps the reroll engine rolling through a kill turn.
- **Limits**: Chapter-locked; base effect is reroll-1s-vs-single-target; retarget requires the character and a death trigger (research stale note).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Headhunter Task Force (2DP → PRIORITY ASSETS)
- **Mechanics**: Eligible VEHICLES gain TANK ACE (fixed 6" Advance instead of roll; re-roll Damage rolls when shooting if they did not Advance); up to three become CHARACTERS at muster.
- **Rating**: Situational for Priority Assets
- **Synergies**: Gladiator Lancer / Ballistus Dreadnought-style hull lines wanting reliable advances and stationary damage rerolls.
- **Limits**: Vehicle-scope; damage reroll lost on advancing turns; CHARACTER grant is muster-time and unlocks enhancements only (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Ironstorm Spearhead (2DP → TAKE AND HOLD)
- **Mechanics**: Once per phase per unit, re-roll a single Hit roll OR Wound roll OR Damage roll.
- **Rating**: Weak for Take and Hold
- **Synergies**: Vehicle/Dreadnought lists get insurance on key single shots.
- **Limits**: Single-die insurance, explicitly not equivalent to blanket rerolls (research wording). ⚠️ Shared-codex delta: official sources list Ironstorm Spearhead as PURGE THE FOE, not TAKE AND HOLD.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Orbital Assault Force (2DP → TAKE AND HOLD)
- **Mechanics**: Selected non-TITANIC units (2/3/4 by battle size) gain Deep Strike; models set up this turn re-roll Wound rolls of 1; DROP POD disembarkers that turn also re-roll Hit rolls of 1.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Drop Pod-delivered Eradicator/Sternguard alpha; reserves pressure across turns 1-3.
- **Limits**: Rerolls arrival-turn only; Deep Strike slots are a list-building rule (research). ⚠️ Source conflict: shared corpus describes a +1 to-hit bonus for Drop Pod arrivals; this faction file states re-roll Hit rolls of 1 — different mechanics, unresolved.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Reclamation Force (2DP → TAKE AND HOLD)
- **Mechanics**: Melee attacks vs units within range of an objective get +1 AP; attacks vs your ADEPTUS ASTARTES units subtract 1 from Wound rolls if the target is within range of an objective you controlled at phase start, or has the TITUS keyword. ULTRAMARINES-only.
- **Rating**: Moderate for Take and Hold (chapter-locked)
- **Synergies**: Objective-anchored Bladeguard Veteran Squad / Captain Titus defensive cores.
- **Limits**: Both halves conditional on objective proximity; chapter restriction (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Shadowmark Talon (2DP → DISRUPTION)
- **Mechanics**: Ranged attacks targeting your units grant Benefit of Cover unless the attacker is within 12"; with AETHON SHAAN on the field, Into Darkness stratagem costs 0CP once per battle round. RAVEN GUARD-only.
- **Rating**: Moderate for Disruption (defensive/recon hybrid)
- **Synergies**: Phobos infiltration lists; Kayvaan Shrike-style forward operating forces.
- **Limits**: Chapter-locked; save-modifier effect with no vocabulary key (research); does nothing vs close-range fire.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Spearpoint Task Force (2DP → DISRUPTION)
- **Mechanics**: Army-wide: ADEPTUS ASTARTES units may declare charges after Advancing or Falling Back; SUBODEN KHAN's unit may make a 6" Normal move at end of Fight phase after destroying units. WHITE SCARS-only.
- **Rating**: Strong for Disruption (melee/mounted lists)
- **Synergies**: Outrider Squad / Kor'Sarro Khan mounted melee waves.
- **Limits**: Chapter-locked; charge eligibility doesn't guarantee charge distance; Khan move requires kills (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vanguard Spearhead (2DP → RECONNAISSANCE)
- **Mechanics**: Ranged attacks targeting your ADEPTUS ASTARTES units give the target Benefit of Cover unless the attacking model is within 12".
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Phobos/Scout infiltration playstyle with redeploys and reserve returns (shared-corpus note; overlaps heavily with Raven Guard Shadowmark Talon).
- **Limits**: Save-modifier benefit, no vocabulary key; approximating as Stealth would be wrong (research warning).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Armoured Speartip (3DP → TAKE AND HOLD)
- **Mechanics**: Units disembarking from a non-FLY TRANSPORT that made a Normal/Advance move make a bonus Normal move (D6"; D3+3" from W14+ HEAVY TRANSPORTS). Excludes Strategic Reserve arrivals.
- **Rating**: Situational for Take and Hold
- **Synergies**: Land Raider assault-ramp melee delivery; Repulsor-class heavy transport pushes.
- **Limits**: Random move distance; requires the transport to have moved; full 3DP spend for a positional mechanic.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Blade Of Ultramar (3DP → PRIORITY ASSETS)
- **Mechanics**: Combat Doctrines as Gladius, activated in up to three Command phases; each doctrine once per battle unless MARNEUS CALGAR is on the field. Devastator = shoot after Advance; Tactical = shoot+charge after Fall Back; Assault = charge after Advance. ULTRAMARINES-only.
- **Rating**: Strong for Priority Assets (Ultramarines lists)
- **Synergies**: Marneus Calgar In Armour Of Antilochus enables doctrine reuse — the named interaction in the research file.
- **Limits**: Chapter restriction; doctrine sequencing decisions; nothing always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Ceramite Sentinels (3DP → TAKE AND HOLD)
- **Mechanics**: Models in terrain re-roll Hit rolls of 1 and Wound rolls of 1; units wholly in terrain, not set up this turn, moved ≤3", gain ENTRENCHED (powers detachment stratagems).
- **Rating**: Situational for Take and Hold
- **Synergies**: Fortification/gunline builds holding terrain anchors (Hammerfall Bunker support).
- **Limits**: Rerolls strictly terrain-conditional; ENTRENCHED consumed by stratagems rather than being a stat buff (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Gladius Task Force (3DP → PRIORITY ASSETS)
- **Mechanics**: Select one Combat Doctrine per Command phase, each once per battle, affecting all ADEPTUS ASTARTES units: Devastator (shoot after Advance), Tactical (shoot+charge after Fall Back), Assault (charge after Advance).
- **Rating**: Strong for Priority Assets (default generalist pick)
- **Synergies**: Whole roster — the doctrine system adapts each round to whatever the mission demands.
- **Limits**: Each doctrine once per battle; mode-based effects never always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Stormlance Task Force (3DP → DISRUPTION)
- **Mechanics**: Lightning Assault — all ADEPTUS ASTARTES units may declare charges in turns they Advanced or Fell Back.
- **Rating**: Strong for Disruption
- **Synergies**: Any melee core (Bladeguard Veteran Squad, Aggressor Squad) converts Advances into charge threats without a chapter lock.
- **Limits**: Full 3DP; eligibility ≠ auto-success on 8-9" charges; fall-back-then-charge granted but unmodeled (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* Gladius-family stratagem support is the documented CP sink: Storm of Fire (ignore-cover shooting under Devastator Doctrine) and Honour the Chapter (melee Lance under Assault Doctrine) per the shared corpus. Anvil Siege Force's Not One Backwards Step (double OC while stationary near an objective) is the named Take-and-Hold CP tool. Treat all as CP-gated burst options, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Space Marines win in list-building: 22 verified 11e detachments span every disposition, and the correct pattern is to pick the detachment that matches the mission pair first, then build the list around its conditions — Gladius Task Force / Blade Of Ultramar for adaptive Priority Assets control, Tacticus Attack Force / Gravis Linebreaker/Siege Force for Take and Hold grinding, Stormlance/Spearpoint when the pair rewards melee tempo. Combat Doctrines is the framework underneath: the detachment decides which doctrine you get, and the doctrine decides what the unit does with the turn. The army leans on durable bodies (Terminators as the SURV wall, Dreadnoughts as damage efficiency) plus the deepest CP toolkit in the game; its weakness is that most detachment rules are conditional or single-target, so mis-matching a detachment to the mission pair leaves you playing vanilla marines.
