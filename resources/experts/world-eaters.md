# Expert Assessment: World Eaters — 11th Edition

## Faction Identity

- **Full name**: Chaos - World Eaters (BSData catalogue name)
- **Faction keyword**: Faction: World Eaters
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Blessings of Khorne (army-wide dice pool rolled each battle round; triple results activate Blessings — Angron's Reborn in Blood and Khorne Lord Of Skulls' extra D6 interact with it per merged data), melee-first unit roster, Scout/Deep Strike delivery on key units
- **Keywords every unit should carry**: Faction: World Eaters; KHORNE on everything; DAEMON on the summoned/daemon units (Bloodletters, Bloodcrushers, Flesh Hounds, Skarbrand, Bloodthirster)
- **Sub-faction keywords** (if any): none modeled as separate keywords in merged data

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/world-eaters.json (2026-08-23,
packs v1.1). Edition snapshot date mandatory on this section.

### Army Rule
- **Blessings of Khorne**: an army-wide dice pool is rolled at the start of each battle round; triple results activate Blessings that buff units for that round (the research corpus records the pool being rolled for Butchers Of Khorne's extra Blessing; merged data shows Angron spending a triple 6 on Reborn in Blood and Khorne Lord Of Skulls adding a die to the roll).
- **Play pattern**: interpretation — every non-daemon datasheet carries Blessings of Khorne in merged data, so list construction revolves around delivering melee units into combat by battle round 2 and keeping enough units alive/on-board to feed the dice pool. The random activation makes the army swingy; lists mitigate with volume of eligible units rather than relying on any one Blessing.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Two detachments target it (Butchers Of Khorne, Goretrack Onslaught) and fast melee takes mid-board objectives early, but OC is thin (small elite units, few bodies) and holding after the charge turn is the weak point. |
| Purge the Foe | Strong | The entire roster is a melee kill engine — Eightbound, Berzerkers, Angron, Maulerfiends — and the flagship 3DP detachment targets Purge. Killing is what this army does best. |
| Reconnaissance | Situational | Scout delivery exists (Chaos Spawn, Goremongers (Infiltrators), Eightbound/Lord Invocatus Scouts per merged rules) and Khorne Daemonkin targets Recon, but action-based scoring fights the army's melee tempo. |
| Priority Assets | Weak | Cult Of Blood and Vessels Of Wrath nominally target it, but both buff rather than protect; nothing in the faction defends a held asset well. |
| Disruption | Weak | Brazen Engines is the only Disruption detachment and forced Battle-shock tests are a low-leverage debuff. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Brazen Engines (1DP → DISRUPTION)
- **Mechanics**: Daemon Vehicle units can, at start of Fight phase, force one engaged enemy unit to take a Battle-shock test at -1; each enemy unit once per phase. Onslaught-tagged.
- **Rating**: Situational for Disruption — only touches enemies already engaged with your vehicles, and Battle-shock rarely decides games.
- **Synergies**: Heldrake and Maulerfiend/Forgefiend engagements (Daemon Vehicles in merged data) that are fighting anyway.
- **Limits**: not_modeled: enemy-facing debuff has no own-army modifier expression; Onslaught tag exclusivity not expressible.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Butchers Of Khorne (1DP → TAKE AND HOLD)
- **Mechanics**: at start of Fight phase, if a Terminator Squad unit is engaged, roll the Blessings of Khorne pool and activate one extra Blessing applying to Terminator Squad units that phase, stacking with normally active ones.
- **Rating**: Situational for Take and Hold — payoff depends entirely on which random Blessing comes up; value concentrates in Terminator-heavy lists.
- **Synergies**: Chaos Terminators (Deep Strike, merged data) as the objective-holding anvil.
- **Limits**: not_modeled: random Blessing outcome is non-deterministic (research lists possible effects from sustained hits to fight-on-death). Gate: requires an engaged Terminator Squad unit at phase start.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Vessels Of Wrath (1DP → PRIORITY ASSETS)
- **Mechanics**: each time a non-Epic Hero World Eaters CHARACTER is selected to fight, its Character models' melee attacks gain Cleave 1 or +1 Armour Penetration — player's choice each fight.
- **Rating**: Situational for Priority Assets — solid free buff but scoped to Character models' own attacks only, excluding Epic Heroes (no Angron/Khârn benefit).
- **Synergies**: Daemon Prince Of Khorne (With Wings), Lord On Juggernaut, Master Of Executions leading Berzerker blocks.
- **Limits**: not_modeled: binary per-fight choice, never both; attached unit models do not benefit. Gate: excludes EPIC HERO.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Goretrack Onslaught (2DP → TAKE AND HOLD)
- **Mechanics**: each time a World Eaters unit disembarks from a Transport, until end of turn it gets +1 to Charge rolls and its melee weapons gain Lance.
- **Rating**: Situational for Take and Hold — strong on the disembark-turn alpha strike, dead rule afterwards; whole list must be built around transports.
- **Synergies**: Chaos Rhino ferrying Berzerkers/Eightbound (Rhinos at 75pts per merged pricing make the taxi density workable); Chaos Land Raider for Terminators.
- **Limits**: not_modeled: +1 to Charge rolls has no vocabulary key; Lance wound bonus applies only when the model charged this turn. Gate: trigger requires disembarking that turn.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Khorne Daemonkin (2DP → RECONNAISSANCE)
- **Mechanics**: when a Blood Legions or World Eaters unit destroys an enemy unit, roll D6 — on 3+ gain a Blood Tithe point; spend points in Command phase on persistent buffs (FNP vs psychic/mortal wounds, Lance on daemon melee, 4+ invuln for daemons, or granting daemons Blessings); also permits points-capped Blood Legions allies.
- **Rating**: Situational for Reconnaissance — kill-driven economy rewards exactly what the army does, but spend choices are once-per-phase resource decisions, not passive buffs, and the ally unlock reshapes the whole list.
- **Synergies**: Bloodletters/Bloodcrushers/Flesh Hounds horde plus high-kill melee (Eightbound, Angron) feeding Tithe points; Bloodthirster/Skarbrand scaling with daemon buffs.
- **Limits**: not_modeled: spend-based economy conditional on kills and D6 rolls; ally caps game-size-dependent. Never treat any Tithe buff as always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Possessed Slaughterband (2DP → PURGE THE FOE)
- **Mechanics**: Possessed units get a reactive move — in the opponent's Shooting phase, if a model was destroyed by shooting after an enemy unit attacks, the unit may make a D6" surge move.
- **Rating**: Situational for Purge — helps close the gap under fire, but benefits only models with the POSSESSED keyword, which merged data puts on exactly one datasheet.
- **Synergies**: Slaughterbound (the sole POSSESSED-keyword unit) leading Eightbound/Exalted Eightbound blocks.
- **Limits**: not_modeled: reactive D6 surge move not expressible as static movement bonus. Gate: requires losing a model to shooting first — the buff rewards being shot, worst-case scenario for fragile units.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Cult Of Blood (2DP → PRIORITY ASSETS)
- **Mechanics**: at start of each Command phase pick ONE of three aura modes (each usable once per battle), active on Titanic/Monster units: Jakhals/Goremongers near them get +1 to hit and +1 to wound; or +1 Move plus +1 Advance/Charge rolls; or a 4+ invulnerable save. Jakhals/Goremongers become Battleline.
- **Rating**: Situational for Priority Assets — explicitly a pick-one-of-three, once-per-battle-per-mode rule; requires Titanic/Monster anchors (Angron, Khorne Lord Of Skulls class units) to exist at all.
- **Synergies**: Angron aura + mass Jakhals (65pts/10 per merged data) or Goremongers (Infiltrators) as the buffed swarm.
- **Limits**: research flags CONDITIONAL BY DESIGN — engine must grant nothing permanently from this detachment. Auras range-limited (6"/9"); each mode once per battle.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

#### Berzerker Warband (3DP → PURGE THE FOE)
- **Mechanics**: when any World Eaters unit makes a Charge move, until end of turn its melee weapons gain +1 Attacks and +2 Strength.
- **Rating**: Strong for Purge — army-wide trigger whose condition (charging) is the army's default action every turn; +1A/+2S across the entire melee roster is the largest unconditional-feeling damage lift in the book. Not rated unconditionally: the bonus exists only on charge turns.
- **Synergies**: everything that charges — Eightbound/Exalted Eightbound, Khorne Berzerkers, Angron, Maulerfiend; Scout/Deep Strike delivery sets up the turn-2 double charge.
- **Limits**: not_modeled: +1 Attacks characteristic not expressible in vocabulary; +2 Strength is target-T-dependent so no fixed wound modifier was fabricated (research explicitly left it unmodeled). Gate: bonus applies ONLY on turns the unit made a Charge move — reliable here because charging is the army's default action, but never present on a turn it doesn't charge. Engine output currently carries NO modifiers for this detachment — do not quote engine numbers as including Warband bonuses. 3DP consumes the full budget.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/world-eaters/

### Enhancements & Stratagems Worth Taking
- Interpretation, grounded in merged enhancement lists: Berzerker Warband's Helm of Brazen Ire (30pts) fits the charge-every-turn plan while Battle-lust (20pts) is the cheap fill; Goretrack Onslaught's Murderous Onslaught (5pts) is near-free on a transport list and Aggressive Deployment (20pts) accelerates the disembark alpha strike; Cult Of Blood's Butcher Lord (10pts) cheaply upgrades the anchor monster. No stratagem assessment attempted — stratagem text is outside the research corpus.

Overall army play pattern (interpretation): World Eaters is a single-plan army — cross the table faster than the opponent can attrite it, charge in mass on battle rounds 2–3, and delete enough of the enemy's scoring units that its own thin OC stops mattering. Detachment choice mostly tunes how violent that window is (Berzerker Warband maximizes it), how it arrives (Goretrack via transports, Scouts/Deep Strike natively), or adds a side economy (Khorne Daemonkin's Tithe). Lists that deviate — holding back for Priority Assets or playing a Battle-shock disruption game — fight the faction's design and consistently rate worse than leaning fully into the charge.
