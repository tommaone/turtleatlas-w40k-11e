# Expert: Adeptus Custodes

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide Adeptus Custodes-specific ground truth so Shredder can identify WRONG data.
> Scope: Faction Identity + Army Rules & Detachments Expert Assessment. Unit-by-unit cheat sheets not yet written.

## Faction Identity

- **Full name**: Adeptus Custodes
- **Faction keyword**: `Faction: Adeptus Custodes` (all units also `Imperium`); Sisters of Silence units carry the separate `ANATHEMA PSYKANA` keyword
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Martial Ka'tah — melee stance system on frontline Custodes models, with stances that interact with Sustained Hits / Lethal Hits style abilities. Several detachments key off Ka'tah attacks, TERMINATOR armour, WALKER type or the mixed Custodes + ANATHEMA PSYKANA pairing.
- **Keywords every unit should carry**: `Imperium`, `Faction: Adeptus Custodes`; Sisters of Silence units carry `ANATHEMA PSYKANA`
- **Sub-faction keywords**: Shield Hosts exist as flavour, not selectable sub-factions; detachment tags (`ARMOURY`, `LIONS`) gate detachment pairing.

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/adeptus-custodes.json (2026-08-23, packs v1.1).

### Army Rule
- **Martial Ka'tah**: Frontline Custodes models fight with selectable melee stances; some stances grant Sustained/Lethal-style critical-hit interactions that detachments like Shield Host amplify.
- **Play pattern**: *(interpretation)* Custodes is a low-model-count elite army: each unit must be individually durable and multi-role. Detachment choice mostly decides which narrow condition set (lone operation, vehicle damage states, deep-strike timing) the elite core operates under — the faction has few broad always-on buffs.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Three detachments map here and the engine's holders (Custodian Wardens, Custodian Guard variants, Sagittarum Custodians) are durable high-OC bodies needing little rule support to sit on objectives. |
| Purge the Foe | Moderate | Shield Host melee amplification is real but melee-only and Ka'tah-scoped; Vertus Praetors and Allarus Custodians provide the punch. |
| Reconnaissance | Situational | Fast frames exist (Agamatus Custodians, Venatari Custodians rank top of recon in engine) but only Null Maiden Vigil and Silent Hunters map here and both are niche. |
| Priority Assets | Moderate | Auric Champions mark-target buff and Tharanatoi ingress charge rerolls fit objective pushes but both are heavily gated. |
| Disruption | Situational | Lions Of The Emperor rewards isolation and Null Maiden Vigil pressures psykers — both meta-dependent. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Might Of The Moritoi (1DP → TAKE AND HOLD)
- **Mechanics**: All friendly Custodes WALKER units get +2" Move and +1 to Advance and Charge rolls. Carries an ARMOURY tag restricting pairing.
- **Rating**: Situational for Take and Hold
- **Synergies:** Dreadnought frames (Contemptor-Galatus/Achillus-class, Telemon-class walkers) closing faster on objectives.
- **Limits**: WALKER units only — the infantry core gets nothing; advance/charge roll bonus is not expressible as a flat movement bonus; ARMOURY tag limits pairing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Silent Hunters (1DP → RECONNAISSANCE)
- **Mechanics**: ANATHEMA PSYKANA units can Advance and still start an action; each Shooting phase one such unit can designate a visible enemy within 12" as 'nulled', giving it +3" detection range.
- **Rating**: Situational for Reconnaissance
- **Synergies:** Sisters of Silence squads screening and marking for the Custodes shooting behind them.
- **Limits**: Entirely ANATHEMA PSYKANA-scoped — pure-Custodes lists get nothing; detection/nulled mechanic has no vocabulary equivalent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Tharanatoi Hammerblow (1DP → PRIORITY ASSETS)
- **Mechanics**: TERMINATOR-armoured Custodes units that made an ingress (teleport/reserve arrival) move this turn re-roll Charge rolls. LIONS tag restricts pairing.
- **Rating**: Situational for Priority Assets
- **Synergies:** Allarus Custodians and Terminator-character bombs arriving from reserve into priority targets.
- **Limits**: Charge rerolls only on the arrival turn; TERMINATOR units only; reliability tool, not output — no hit/wound/damage effect at all.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Auric Champions (2DP → PRIORITY ASSETS)
- **Mechanics**: Each of your Command phases pick one enemy unit; until your next Command phase all attacks from models in CHARACTER-led Custodes units get +1 to Wound vs that unit only. Bonus ends if the marked CHARACTER-led unit loses its character.
- **Rating**: Situational for Priority Assets
- **Synergies:** Character-led strike units (Shield-Captain-led Guard/Wardens/Allarus) focusing down one key target per turn.
- **Limits**: Single enemy unit per turn; CHARACTER-led units only; bonus dies if the leading character is destroyed (e.g. by Precision); EMPTIED PER POLICY in modifiers — never modeled always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Lions Of The Emperor (2DP → DISRUPTION)
- **Mechanics**: All attacks by models in non-VEHICLE Custodes units gain +1 to Hit and +1 to Wound, but only while no other friendly units are within 6" of that unit.
- **Rating**: Situational for Disruption
- **Synergies:** Deliberately spread-out lone operators — solo Wardens/Venatari harassing flanks while the main body stays away.
- **Limits**: State-gated on isolation — vanishes the moment units cluster, directly anti-synergistic with aura support play; vehicles excluded; hardest rule in the codex to keep active against a mobile opponent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Null Maiden Vigil (2DP → RECONNAISSANCE)
- **Mechanics**: Enemy PSYKER units and enemy units below Starting Strength within 12" of your ANATHEMA PSYKANA models take Battle-shock tests in the opponent's Command phase (−1 to the test if below Half-strength). Also grants PROSECUTORS the BATTLELINE keyword.
- **Rating**: Situational for Reconnaissance
- **Synergies:** Sisters of Silence screens vs psyker-heavy metas; extra Prosecutors improve mission-legal body count.
- **Limits**: Debuff-only — no offensive stat anywhere; value depends entirely on opponent list composition (psyker density); Battle-shock tests are dice-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Shield Host (2DP → PURGE THE FOE)
- **Mechanics**: At the start of each battle round choose for Martial Ka'tah models' melee attacks: unmodified Hit rolls of 5+ score Critical Hits (feeding Sustained/Lethal stances), OR melee weapons gain +1 AP. Choice re-made every battle round.
- **Rating**: Strong for Purge the Foe
- **Synergies:** The whole frontline melee core — Custodian Guard, Allarus Custodians, Vertus Praetors — sequencing crit stance rounds into Sustained/Lethal Ka'tah stances and AP rounds into tough targets.
- **Limits**: Melee-only; Ka'tah models only; crit-on-5+ option converts to output only via stance abilities; per-round choice means neither half is ever always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Solar Spearhead (2DP → TAKE AND HOLD)
- **Mechanics**: VEHICLES at full Starting Strength get +2 OC; below full strength they re-roll Hit rolls of 1; Below Half-strength also re-roll Wound rolls of 1. WALKER units additionally get +2" Move and +1 to Advance and Charge rolls. ARMOURY tag restricts pairing.
- **Rating**: Situational for Take and Hold
- **Synergies:** Caladius Grav-tank / Coronus grav-carrier vehicle wings holding mid-board objectives; walker dreadnoughts gaining mobility.
- **Limits**: Every benefit gated on unit type AND damage state (+2 OC requires full strength, not AIRCRAFT, not Battle-shocked); vehicle-focused rule in a predominantly infantry faction; ARMOURY tag.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

#### Talons Of The Emperor (3DP → TAKE AND HOLD)
- **Mechanics**: ANATHEMA PSYKANA units project an aura: Custodes units within 6" get Feel No Pain 5+ vs Psychic Attacks and mortal wounds. Conversely Sisters within 6" of Custodes units get +1 to Hit on their attacks.
- **Rating**: Situational for Take and Hold
- **Synergies:** Mixed formations where Witchseeker/Prosecutor squads escort Guard blocks — mutual buff zone.
- **Limits**: Both halves require mixed-army positioning within 6"; FnP covers Psychic Attacks and mortal wounds only; 3DP cost for positioning-dependent protection; pure-Custodes lists pay for a rule they barely trigger.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-custodes/

### Enhancements & Stratagems Worth Taking
*(interpretation — enhancement effect text is NOT yet captured in the research corpus; names verified against data/merged only. Verify effects against the faction pack before citing mechanics.)*
- **Shield Host** carries four enhancements (Auric Mantle, Castellan's Mark, From the Hall of Armouries, Panoptispex) on the faction's highest-output combat detachment *for melee* — likely picks by placement alone.
- Solar Spearhead's Veteran of the Kataphraktoi and Augury Uplink sit on the vehicle detachment whose rule is already damage-state-gated; effects unverified — do not assert stacking synergy.
- No stratagem effects were captured in the research corpus for this faction — do not assert any stratagem mechanics as fact.

### Overall Play Pattern
*(interpretation)* Custodes wins on the quality of its datasheets more than on its detachment rules — almost every detachment buff is scoped to a unit type, damage state, positioning condition, or single marked target. The competitive default is therefore the shell with the fewest gates (Shield Host for melee output) layered over durable objective-holding infantry, with the specialist detachments (Lions' lone-operator aggression, Solar Spearhead vehicle wings, Talons' mixed shield-wall) reserved for deliberate builds. The faction's structural weakness is tempo and board coverage from low model count; none of the detachment rules meaningfully fix that, so mission play depends on the elite units' native durability and OC.

Assumptions:
- opponent unknown (all-comers)
- no cover factored beyond what detachment rules state
- Ka'tah stance selection assumed optimal per round (upper-bound usage of Shield Host)
- no CP economy modeling for stratagems
