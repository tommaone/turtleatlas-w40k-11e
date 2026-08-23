# Expert File: Black Templars

## Faction Identity

- **Full name**: Black Templars (BSData catalogue: "Imperium - Adeptus Astartes - Black Templars")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Black Templars`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Per the Warhammer Community faction-pack article title, Black Templars "forget Oaths of Moment, swear a Templar Vow" — i.e. the chapter replaces the standard Astartes Oath framework with a Vow system. Specific Vow mechanics are NOT documented in the research corpus [unverified]. Detachment roster note: unlike sibling chapters, no Librarius Conclave and no 1st Company Task Force appear in the merged detachment list — consistent with the chapter's no-psyker identity (no Librarian units in data/config).
- **Sub-faction keywords**: `Faction: Black Templars`

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/black-templars.json +
_space-marines-shared.json (2026-08-23, packs v1.1). 20 detachments total:
6 chapter-specific, 14 inherited from the shared Space Marines codex pack
(rated here in Black Templars context, not re-assessed).

### Army Rule
- **Templar Vows**: per the Warhammer Community article ("Black Templars forget Oaths of Moment, swear a Templar Vow today"), the chapter swaps Oath of Moment for vows chosen at army construction. The corpus does not document individual Vow effects — treat any specific vow claim as unverified.
- **Play pattern** *(interpretation)*: the chapter-specific suite is built around Crusader Squad / Sword Brethren bodies pushing forward — advance/charge reliability, transport assault, and Chaplain-fuelled melee pressure.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Vindication Task Force anchors objectives on ANCIENT units; inherited Anvil/Bastion bench exists but Bastion costs BT 3DP (vs 2DP shared). |
| Purge the Foe | Strong | Companions Of Vehemence rerolls every Advance and Charge army-wide; Godhammer delivers melee via Land Raider; Sword Brethren mortal-wound charges. |
| Reconnaissance | Moderate | Only inherited tools (Vanguard Spearhead cover, Subversion detection) — no chapter-specific recon piece. |
| Priority Assets | Moderate | Marshal's Household is Sword Brethren-only; Gladius inherited remains the generalist option. |
| Disruption | Strong | Companions Of Vehemence mobility plus Wrathful Procession Chaplain pressure; Stormlance available at 2DP as an alternative. |

### Detachment Assessments

### Chapter-Specific Detachments
<!-- ordered by DP -->

#### Marshal'S Household (1DP → PRIORITY ASSETS)
- **Mechanics**: Faith-fuelled Resolve — Sword Brethren Squads gain +1 OC; enhancements add +1 to charge rolls or Fights First; stratagems add +2 Strength vs Monsters/Vehicles, D6-per-model mortal wounds on the charge (max 6), and Desperate Escape punishment.
- **Rating**: Situational for Priority Assets
- **Synergies**: Sword Brethren Squad led by High Marshal Helbrecht or a Marshal as the army's scoring blade.
- **Limits**: OC buff restricted to Sword Brethren Squads; mortal-wound stratagem is CP-gated and capped; 1DP add-on scope.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### The Living Miracle (1DP → DISRUPTION)
- **Mechanics**: Anointed Champion — when the Emperor's Champion fights, re-roll one hit roll and one wound roll. Free Guiding Omens enhancement picks 3 of 6 abilities (incl. once-per-battle Devastating Wounds vs Characters, +2 Attacks). No stratagems.
- **Rating**: Situational for Disruption
- **Synergies**: Emperor'S Champion (or Anointed variant) duelling enemy characters.
- **Limits**: Single-model detachment — zero effect on the other ~90% of the army; ⚠️ merged objective DISRUPTION conflicts with official sources listing PURGE THE FOE.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Wrathful Procession (1DP → TAKE AND HOLD)
- **Mechanics**: Chant of Deathless Devotion — Chaplain units get a 5+ invulnerable save vs ranged attacks; enhancements add Devastating Wounds or Cleave/Precision choice to the Chaplain's melee; stratagems add 4+ FNP vs mortals, unit Precision, +1 Strength.
- **Rating**: Situational for Take and Hold
- **Synergies**: Chaplain Grimaldus holding an objective with Crusader Squad bodyguard.
- **Limits**: Chaplain-keyword-gated throughout; save is ranged-only; 1DP add-on scope.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Companions Of Vehemence (2DP → PURGE THE FOE)
- **Mechanics**: Righteous Fervour — ALL units re-roll Advance and Charge rolls. Stratagems give 6" pile-in/consolidate, reactive Surge toward enemies within 9", battle-shock punishment for chargers.
- **Rating**: Strong for Purge the Foe (and Disruption)
- **Synergies**: Any melee core — Crusader Squad blobs, Sword Brethren Squad, Assault Intercessors With Jump Packs — gets reliable charge math without spending eligibility rules.
- **Limits**: Rerolls are dice-reliability, not eligibility (cannot charge after Advance); most spike damage lives behind CP stratagems.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Godhammer Assault Force (2DP → PURGE THE FOE)
- **Mechanics**: Units get +1 to hit with melee if they disembarked from a Transport that turn; charged enemies take Battle-shock tests. Stratagems allow charging through models and disembarking from a Land Raider straight into Engagement Range.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Land Raider-delivered Terminator Assault Squad / Sword Brethren alpha strikes.
- **Limits**: Everything keys off Transport disembarkation — dead transport rule, dead detachment; ⚠️ research confidence MEDIUM; ⚠️ merged objective PURGE THE FOE conflicts with official sources listing DISRUPTION.
- **_source**: https://www.warhammer-community.com/en-gb/articles/3nvcmema/black-templars-forget-oaths-of-moment-swear-a-templar-vow-today/

#### Vindication Task Force (2DP → PRIORITY ASSETS)
- **Mechanics**: Purge and Sanctify — attacks vs ANCIENT units near objectives subtract 1 from wound rolls when attacker S exceeds target T; Crusader Squad surge moves can route toward objectives. Stratagems revive a destroyed Ancient, add AP near objectives, ignore cover/hit modifiers.
- **Rating**: Situational for Take and Hold (objective-holding build despite PRIORITY ASSETS label)
- **Synergies**: Crusade Ancient / Ancient anchoring big Crusader Squads on mid-field markers.
- **Limits**: Defensive reduction dual-conditional (ANCIENT + objective + S>T); revival stratagem once-per-battle per model; research confidence MEDIUM.
- **_source**: https://www.40k.app/factions/black-templars/detachments/vindication-task-force

### Inherited From Space Marines Codex
<!-- shorter blocks; mechanics per _space-marines-shared.json, rated in BT context -->

#### Fulguris Task Force (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Skystrike — SPEEDER units ingress in Movement phase 1 (inherited from SM codex).
- **Rating**: Situational for Reconnaissance — thin speeder roster in config; ⚠️ shared-codex delta flags official sources listing DISRUPTION.
- **_source**: inherited:_space-marines-shared.json

#### Subversion Assets (1DP → DISRUPTION) — *inherited*
- **Mechanics**: Nowhere to Hide — Scout/Phobos detection manipulation (inherited from SM codex).
- **Rating**: Situational for Disruption — Scout Squad utility only; ⚠️ shared-codex delta flags official sources listing RECONNAISSANCE.
- **_source**: inherited:_space-marines-shared.json

#### Vengeful Hosts (1DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Imperator Unleashed — FLY INFANTRY re-roll hit 1s on ingress/charge turns (inherited from SM codex).
- **Rating**: Situational for Take and Hold. ⚠️ Research confidence LOW: objective/DP sourcing unconfirmed by fetched sources.
- **_source**: inherited:_space-marines-shared.json

#### Anvil Siege Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: All ranged weapons gain HEAVY (+1 Wound stationary if already HEAVY) (inherited from SM codex).
- **Rating**: Weak for Take and Hold — static gunline theme against a melee chapter identity.
- **_source**: inherited:_space-marines-shared.json

#### Firestorm Assault Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: ASSAULT on all ranged, +1 Strength within 12" (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — works with Aggressor Squad close-range packages; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Headhunter Task Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Tank Ace vehicles: flat 6" Advance, stationary damage re-rolls (inherited from SM codex).
- **Rating**: Situational for Priority Assets — very thin vehicle roster in config (Drop Pod only), limiting value.
- **_source**: inherited:_space-marines-shared.json

#### Ironstorm Spearhead (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: One hit/wound/damage re-roll per unit per phase (inherited from SM codex).
- **Rating**: Weak for Take and Hold — single-die insurance, vehicle-themed mismatch; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Orbital Assault Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: 2-4 units gain Deep Strike + arrival-turn wound-1s rerolls (inherited from SM codex).
- **Rating**: Moderate for Take and Hold — Drop Pod delivery suits the Crusader push.
- **_source**: inherited:_space-marines-shared.json

#### Stormlance Task Force (2DP → DISRUPTION) — *inherited, discounted DP*
- **Mechanics**: Lightning Assault — all units charge after Advancing or Falling Back (inherited from SM codex; BT pay 2DP vs 3DP shared cost per merged data).
- **Rating**: Strong for Disruption — army-wide advance-and-charge at 2DP stacks cleanly with Companions Of Vehemence-style charge reliability if combined across packs is permitted; verify combination legality before planning it.
- **Limits**: Eligibility ≠ made charges; fall-back-charge unmodeled.
- **_source**: inherited:_space-marines-shared.json

#### Vanguard Spearhead (2DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Benefit of Cover vs ranged attacks from beyond 12" (inherited from SM codex).
- **Rating**: Moderate for Reconnaissance — best inherited defensive core for a footslogging Crusader army.
- **_source**: inherited:_space-marines-shared.json

#### Bastion Task Force (3DP → TAKE AND HOLD) — *inherited, premium DP*
- **Mechanics**: Battleline act after Advance/Fall Back + Auspex scan rerolls (inherited from SM codex; BT pay 3DP vs 2DP shared cost — confirmed by research note).
- **Rating**: Weak for Take and Hold — paying above shared-codex price for an off-brand Battleline flood playstyle.
- **_source**: inherited:_space-marines-shared.json

#### Armoured Speartip (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Post-disembark follow-up moves from moved Transports (inherited from SM codex).
- **Rating**: Situational for Take and Hold — overlaps Godhammer's transport-assault niche at higher DP.
- **_source**: inherited:_space-marines-shared.json

#### Ceramite Sentinels (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Terrain-based hit/wound-1s rerolls + Entrenched status (inherited from SM codex).
- **Rating**: Situational for Take and Hold — static gunline theme, off-brand.
- **_source**: inherited:_space-marines-shared.json

#### Gladius Task Force (3DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Rotating Combat Doctrines, each once per battle (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — serviceable generalist; Assault Doctrine duplicates what Companions/Stormlance do permanently.
- **_source**: inherited:_space-marines-shared.json

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* The Living Miracle's free Guiding Omens pick-3-of-6 does not count against the army enhancement limit — the only documented zero-cost enhancement in the chapter pack, making Emperor's Champion builds efficient. Marshal's Household's Blade of Detestation (D6-per-model mortal wounds on the charge, max 6) is the named burst CP tool for Sword Brethren. Companions Of Vehemence's pile-in/consolidate 6" stratagem extends engagement grinding. All CP/enhancement-gated, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Black Templars play as a single massed crusade wave: the strongest chapter-specific rules (Companions Of Vehemence advance/charge rerolls, Godhammer transport delivery, Wrathful Procession objective-holding Chaplains) all assume Crusader Squad and Sword Brethren bodies arriving together and staying in combat. The default build is Companions Of Vehemence (or Stormlance at its discounted 2DP) with a 1DP add-on for whichever elite unit needs sharpening. Structural weaknesses are Reconnaissance — no native tool exists — and the premium pricing of inherited defensive detachments (Bastion at 3DP); the Templar Vow system that defines the army rule layer is undocumented in this corpus, so list-building claims involving specific vows are unsupported here.
