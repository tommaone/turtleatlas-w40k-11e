# Curated-sheet regression report

Diffs current configs against `5d21b52` (last verified curated state).
Each entry needs source verification before fixing — presence here
flags *change*, not proven damage. Golden-pipeline candidates.

**106 flagged entries.**

## Settled: orks + world-eaters (2026-08-24)

All 18 flagged entries for these factions source-verified against
wahapedia.ru/wh40k11ed (fetched 2026-08-24). Corpora:
`workspace/golden_loadouts/orks-golden.json`,
`workspace/golden_loadouts/world-eaters-golden.json`. Pins:
`tests/test_golden_orks.py`, `tests/test_golden_world_eaters.py`.

**FIXED (real regressions):**
- orks Mek — phantom Kustom mega-blasta removed; catalogue-exact
  `Kustom mega-slugga` spelling (old name KeyError-skipped silently).
- orks Big Mek In Mega Armour — Grot Oiler slot removed: unresolvable
  non-weapon choice skipped EVERY combo, scoring the model as bare
  power klaw.
- orks Dakkajet — base is TWO twin supa-shootas; was under-equipped
  with one. Now 2 fixed + 1 additional slot.
- orks Deff Dread — one pick-1 arm slot → four independent arm slots
  (2 shootas + 2 klaws, each replaceable).
- orks Painboy — audit sweep wrote a literal `"` into `'Urty syringe`;
  lookup silently failed and the weapon vanished from scoring.
- world-eaters Bloodthirster — 'Axe and flail'/'Axe and lash' bundles
  retyped ranged→melee (BSData holds melee-only profiles).
- world-eaters Chaos Predators — 'Combi bolter' / '2 heavy bolters'
  did not resolve: every slot combo skipped, sponson/pintle firepower
  silently lost. Catalogue-exact names + count:2 sponsons now.
- world-eaters Defiler — max_count:1 on Electroscourge was missing
  (CSM got it in ec7b60c); engine could pick the illegal 2x scourge.

**KEPT + documented (verified correct):** Warboss (3 paired builds),
Battlewagon (legal-max restructure fixed an old illegality),
Burna-Bommer, Gargantuan Squiggoth, Wazbom Blastajet (force-field
exclusivity limitation noted), Painboss, Forgefiend, Helbrute,
Khorne Lord Of Skulls.

Engine-wide lesson (now encoded in golden tests): an unresolvable
choice inside `_resolve_slots_build` skips its whole combo silently —
single-choice slots holding non-weapon wargear poison every combo and
fall back to bare fixed loadouts.

---

## Verdicts — space-marines + grey-knights (settled 2026-08-24)

Sources: wahapedia.ru 11ed Faction Pack v1.1 datasheets (per-unit URLs in
`workspace/golden_loadouts/<faction>.json`) cross-checked against local BSData
catalogue selection-entry-group constraints. Corpus entries carry `_source`.

### grey-knights

| Unit | Verdict | Why |
|------|---------|-----|
| Venerable Dreadnought | already-correct (structure) + FIXED (melee loss) | Datasheet: assault cannon (+swaps) + storm bolter→heavy flamer + combat weapon ALWAYS equipped. Two mandatory slots match BSData groups; but combined 'X and Dreadnought combat weapon' entries resolve ranged-only, dropping the melee weapon → added fixed DCW. Validator now flags it EXTRA WEAPON (advisory, deliberate): BSData hides the DCW inside the upgrade entries. |
| Grand Master In Nemesis Dreadknight | already-correct | Restored in ec7b60c from gk-csm-pilot.json golden corpus; wahapedia re-verified. |
| Nemesis Dreadknight | already-correct | Same as GMNDK ('Ranged Weapons' slot was split into Ranged 1/2 per golden pilot). |
| Grey Knights Thunderhawk Gunship | FIXED | Equipped = 2 lascannons + 4 twin heavy bolters + hull (BSData min/max=2/4). Config had collapsed to 1+1. The 5d21b52 state (4x twin HB but 2x hellstrike 'Missile battery' slots) was stale 10e data — cluster bombs are base, ONE battery replaces them. |
| Stormhawk Interceptor | already-correct | Las-talon/Skyhammer are pick-1 slot options in BSData, not fixed weapons; config matches groups. |
| Stormtalon Gunship | already-correct | Skyhammer is a slot choice (BSData single group); 'lost fixed' flag was the audit correcting stale data. |

### space-marines

| Unit | Verdict | Why |
|------|---------|-----|
| Ancient | already-correct | One pick-1 group {bolt rifle & CCW \| power weapon}, bolt pistol fixed (wahapedia + BSData agree). 5d21b52 separate ranged/melee slots were over-permissive — the audit fix was legitimate. |
| Ancient in Terminator Armor | FIXED | Base = storm bolter + power fist; fist swaps one-of; twin lightning claws OR thunder hammer + terminator storm shield replace BOTH base weapons. Audit collapse left illegal claws+storm-bolter pairing with no options. Restored as 3 builds. |
| Chaplain With Jump Pack | already-correct | Current choices match BSData group exactly (10 options incl. power fist melee swap). |
| Astraeus | FIXED (multiplicity) | Sponson pairs resolved as a single gun ('Two …' names resolve to one profile); switched to count:2 on resolvable names. Slots otherwise match BSData. |
| Brutalis Dreadnought | already-correct | Bolt rifles are bundled in the combined fists entry per BSData, not separate fixed weapons; both pick-1 groups match. |
| Dreadnought | already-correct | Arm × heavy all-pairings-legal via 2 slots covers the old 6-build enumeration. |
| Gladiator Lancer | FIXED (multiplicity + spurious fixed) | Sponsons now count:2 pairs; removed fixed storm bolter not present in BSData wargear links. |
| Invictor Tactical Warsuit | FIXED (typing) | Invictor Fist is melee, was typed ranged (fist damage counted as shooting). |
| Predator Annihilator / Destructor | FIXED (multiplicity) | '2 lascannons'/'2 heavy bolters' choice names didn't resolve → sponsons silently dropped; now Lascannon/Heavy Bolter with count:2. |
| Redemptor Dreadnought | already-correct | 3 pick-1 slots + fist/pod fixed match BSData exactly. |
| Stormhawk Interceptor | already-correct | Matches BSData groups (same sheet as GK variant). |
| Stormraven Gunship | FIXED | Hurricane Bolters are an ADDITIVE option (may equip 2) and stormstrike missiles are a PAIR — restored 2x stormstrike + 2x hurricane bolters fixed; swap slots keep base picks. 5d21b52 had 1x hurricane and no stormstrike at all. |
| Thunderhawk Gunship | FIXED | Same FW datasheet structure as GK: 2 lascannons + 4 twin heavy bolters (BSData min/max), not 1+1 nor the stale 10e loadout. |

Golden structure pins: `tests/test_golden_space_marines_loadouts.py`,
`tests/test_golden_grey_knights_loadouts.py` (structure/count only).

Validator advisory delta vs HEAD: SM 47→39 issues (net −8); GK 1→2
(+1 = the deliberate Venerable DCW fixed weapon described above;
pre-existing 'cluster bombs NOT IN DATA' remains on both Thunderhawks —
merged catalog lacks that profile entry, engine resolves it fine).

---

- `adepta-sororitas`/characters.json **Canoness**: lost slot choices: ['Melee weapon 1']
- `adepta-sororitas`/characters.json **Palatine**: lost slot choices: ['Ranged weapon 1']
- `adepta-sororitas`/weapon_options.json **Castigator**: lost slot choices: ['Ranged weapon 1']
- `adepta-sororitas`/weapon_options.json **Exorcist**: lost fixed weapons: ['Heavy Bolter', 'Hunter-Killer Missile']
- `adepta-sororitas`/weapon_options.json **Immolator**: lost fixed weapons: ['Heavy Bolter', 'Hunter-Killer Missile']
- `adeptus-custodes`/characters.json **Shield-Captain In Allarus Terminator Armour**: lost fixed weapons: ['Balistus grenade launcher']
- `adeptus-custodes`/characters.json **Shield-Captain On Dawneagle Jetbike**: lost fixed weapons: ['Interceptor lance']
- `adeptus-mechanicus`/characters.json **Sydonian Skatros**: lost fixed weapons: ['Mechanicus pistol', 'Sydonian Feet']
- `adeptus-mechanicus`/weapon_options.json **Archaeopter Stratoraptor**: lost fixed weapons: ['Cognis heavy stubber', 'Heavy phosphor blaster', 'Twin cognis lascannon']
- `adeptus-mechanicus`/weapon_options.json **Skorpius Disintegrator**: lost fixed weapons: ['Disruptor missile launcher']
- `aeldari`/weapon_options.json **Wraithknight**: lost slot choices: ['Primary Arm']
- `black-templars`/characters.json **Marshal**: lost slot choices: ['Ranged weapon 1']
- `black-templars`/weapon_options.json **Repulsor Executioner**: lost fixed weapons: ['Repulsor Executioner Defensive Array']
- `blood-angels`/characters.json **Death Company Captain With Jump Pack**: lost slot choices: ['Ranged weapon 1', 'Melee weapon 1']
- `blood-angels`/weapon_options.json **Baal Predator**: lost fixed weapons: ['Armoured Tracks', 'Armoured Tracks', 'Baal Flamestorm Cannon', 'Heavy Bolter', 'Heavy Bolter', 'Heavy Bolter', 'Heavy Bolter', 'Twin Assault Cannon']; builds collapsed 2 -> 1
- `blood-angels`/weapon_options.json **Death Company Dreadnought**: lost fixed weapons: ['Blood Talons']
- `chaos-space-marines`/characters.json **Chaos Lord**: lost slot choices: ['Ranged weapon 1', 'Melee weapon 1', 'Melee weapon 2']
- `chaos-space-marines`/characters.json **Chaos Lord With Jump Pack**: lost slot choices: ['Ranged weapon 1']
- `chaos-space-marines`/weapon_options.json **Forgefiend**: lost fixed weapons: ['Armoured limbs', 'Armoured limbs', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Forgefiend jaws', 'Forgefiend jaws', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon']; builds collapsed 4 -> 1
- `chaos-space-marines`/weapon_options.json **Khorne Lord Of Skulls**: lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2', 'Melee weapon 1']
- `dark-angels`/weapon_options.json **Land Speeder Vengeance**: lost fixed weapons: ['Assault cannon', 'Close Combat Weapon', 'Heavy bolter', 'Plasma storm battery - standard', 'Plasma storm battery - supercharge']
- `dark-angels`/weapon_options.json **Nephilim Jetfighter**: lost fixed weapons: ['Avenger mega bolter', 'Blacksword missiles', 'Nephilim lascannons', 'Twin heavy bolter']
- `dark-angels`/weapon_options.json **Ravenwing Darkshroud**: lost fixed weapons: ['Assault cannon', 'Close Combat Weapon', 'Heavy bolter']
- `death-guard`/weapon_options.json **Chaos Predator Annihilator**: lost slot choices: ['Ranged weapon 1']
- `death-guard`/weapon_options.json **Chaos Predator Destructor**: lost slot choices: ['Ranged weapon 1']
- `death-guard`/weapon_options.json **Defiler**: lost slot choices: ['Ranged weapon 1']
- `death-guard`/weapon_options.json **Foetid Bloat-Drone**: lost fixed weapons: ['Fleshmower', 'Plaguespitter']
- `death-guard`/weapon_options.json **Helbrute**: lost slot choices: ['Ranged weapon 1', 'Melee weapon 1']
- `emperors-children`/characters.json **Keeper Of Secrets**: lost fixed weapons: ['Phantasmagoria - focused witchfire', 'Snapping claws', 'Witstealer sword']
- `emperors-children`/characters.json **Lord Exultant**: lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2', 'Melee weapon 1', 'Melee weapon 2']
- `emperors-children`/weapon_options.json **Chaos Land Raider**: lost fixed weapons: ['Soulshatter lascannon', 'Twin heavy bolter']
- `emperors-children`/weapon_options.json **Chaos Rhino**: lost fixed weapons: ['Havoc launcher']
- `emperors-children`/weapon_options.json **Defiler**: lost slot choices: ['Ranged weapon 1']
- `grey-knights`/characters.json **Venerable Dreadnought**: lost fixed weapons: ['Dreadnought combat weapon']; lost slot choices: ['Assault cannon swap', 'Storm bolter swap']
- `grey-knights`/weapon_options.json **Grand Master In Nemesis Dreadknight**: lost fixed weapons: ['Dreadfists', 'Gatling psilencer', 'Gatling psilencer', 'Heavy incinerator', 'Heavy incinerator', 'Heavy incinerator', 'Heavy incinerator', 'Heavy psycannon', 'Heavy psycannon', 'Heavy psycannon', 'Heavy psycannon', 'Nemesis daemon greathammer', 'Nemesis daemon greathammer', 'Nemesis greatsword', 'Nemesis greatsword', 'Nemesis greatsword', 'Nemesis mace', 'Sublimator', 'Sublimator']; builds collapsed 7 -> 1
- `grey-knights`/weapon_options.json **Grey Knights Thunderhawk Gunship**: lost fixed weapons: ['Armoured hull']; lost slot choices: ['Turbo-laser destructor', 'Missile battery 1', 'Missile battery 2']
- `grey-knights`/weapon_options.json **Nemesis Dreadknight**: lost slot choices: ['Ranged Weapons']
- `grey-knights`/weapon_options.json **Stormhawk Interceptor**: lost fixed weapons: ['Las-talon', 'Skyhammer missile launcher']
- `grey-knights`/weapon_options.json **Stormtalon Gunship**: lost fixed weapons: ['Skyhammer missile launcher']
- `imperial-agents`/characters.json **Inquisitor**: lost slot choices: ['Melee weapon 1']
- `imperial-agents`/weapon_options.json **Inquisitorial Chimera**: lost slot choices: ['Main weapon', 'Pintle mount', 'Extra weapon']
- `leagues-of-votann`/characters.json **Einhyr Champion**: lost slot choices: ['Melee weapon 1']
- `leagues-of-votann`/characters.json **Kâhl**: lost slot choices: ['Ranged weapon 1', 'Melee weapon 1']
- `leagues-of-votann`/weapon_options.json **Hekaton Land Fortress**: lost fixed weapons: ['Cyclic ion cannon', 'Cyclic ion cannon', 'Cyclic ion cannon', 'Heavy magna-rail cannon', 'Heavy magna-rail cannon', 'Heavy magna-rail cannon', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'Hekaton warhead', 'SP heavy conversion beamer', 'SP heavy conversion beamer', 'SP heavy conversion beamer', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin bolt cannon', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer', 'Twin ion beamer']; builds collapsed 9 -> 1
- `necrons`/characters.json **Catacomb Command Barge**: lost slot choices: ['Melee weapon 1']
- `necrons`/characters.json **Lokhust Lord**: lost fixed weapons: ["Lord's blade", 'Staff of light', 'Staff of light']
- `necrons`/characters.json **Overlord**: lost fixed weapons: ["Overlord's blade", 'Staff of light', 'Staff of light', 'Tachyon arrow', 'Voidscythe']
- `necrons`/weapon_options.json **Annihilation Barge**: lost fixed weapons: ['Gauss cannon', 'Tesla cannon']; builds collapsed 2 -> 1
- `necrons`/weapon_options.json **Monolith**: lost fixed weapons: ['Four death rays', 'Four gauss flux arcs']
- `necrons`/weapon_options.json **Seraptek Heavy Construct**: lost fixed weapons: ['Synaptic obliterator', 'Titanic forelimbs - strike', 'Titanic forelimbs - strike', 'Titanic forelimbs - sweep', 'Titanic forelimbs - sweep', 'Transdimensional projector', 'Two singularity generators']; builds collapsed 2 -> 1
- `necrons`/weapon_options.json **Triarch Stalker**: lost fixed weapons: ['Heavy gauss cannon array', 'Particle shredder']; builds collapsed 3 -> 1; lost slot choices: ['Ranged weapon 1']
- `orks`/characters.json **Big Mek In Mega Armour**: lost slot choices: ['Ranged weapon 1']
- `orks`/characters.json **Mek**: lost fixed weapons: ['Kustom mega-slugga']
- `orks`/characters.json **Painboss**: lost fixed weapons: ['Beast Snagga klaw']
- `orks`/characters.json **Painboy**: lost fixed weapons: ['’Urty syringe']
- `orks`/characters.json **Warboss**: lost fixed weapons: ['Twin slugga']; lost slot choices: ['Melee weapon 1', 'Melee weapon 2']
- `orks`/weapon_options.json **Battlewagon**: lost fixed weapons: ['Deff rolla', 'Kannon - frag', 'Kannon - shell', 'Killkannon', 'Tracks and wheels', 'Zzap gun']
- `orks`/weapon_options.json **Burna-Bommer**: lost fixed weapons: ['Skorcha missile rack']
- `orks`/weapon_options.json **Dakkajet**: lost fixed weapons: ['Twin supa-shoota']
- `orks`/weapon_options.json **Deff Dread**: lost fixed weapons: ['Big shoota', 'Dread klaw', 'Kustom mega-blasta', 'Rokkit launcha', 'Skorcha']
- `orks`/weapon_options.json **Gargantuan Squiggoth**: lost fixed weapons: ['Huge tusks - strike', 'Huge tusks - sweep', 'Kannon - frag', 'Kannon - shell', 'Supa-kannon']
- `orks`/weapon_options.json **Wazbom Blastajet**: lost fixed weapons: ['Twin supa-shoota', 'Twin tellyport mega-blasta', 'Twin wazbom mega-kannon']
- `space-marines`/characters.json **Ancient**: lost slot choices: ['Melee weapon 1']
- `space-marines`/characters.json **Ancient in Terminator Armor**: lost fixed weapons: ['Thunder Hammer']; builds collapsed 2 -> 1; lost slot choices: ['Melee weapon 1']
- `space-marines`/characters.json **Chaplain With Jump Pack**: lost slot choices: ['Ranged weapon 1']
- `space-marines`/weapon_options.json **Astraeus**: lost slot choices: ['Ranged weapon 1']
- `space-marines`/weapon_options.json **Brutalis Dreadnought**: lost fixed weapons: ['Brutalis Bolt Rifles', 'Brutalis Fists', 'Brutalis Talons']; builds collapsed 2 -> 1; lost slot choices: ['Ranged weapon 1', 'Ranged weapon 1']
- `space-marines`/weapon_options.json **Dreadnought**: lost fixed weapons: ['Assault Cannon', 'Dreadnought Combat Weapon', 'Dreadnought Combat Weapon', 'Dreadnought Combat Weapon', 'Dreadnought Combat Weapon', 'Dreadnought Combat Weapon', 'Dreadnought Combat Weapon', 'Heavy Flamer', 'Heavy Plasma Cannon', 'Missile Launcher', 'Multi-melta', 'Storm bolter', 'Storm bolter', 'Storm bolter', 'Storm bolter', 'Storm bolter', 'Storm bolter', 'Twin lascannon']; builds collapsed 6 -> 1
- `space-marines`/weapon_options.json **Gladiator Lancer**: lost fixed weapons: ['Armoured Hull', 'Icarus Rocket Pod', 'Ironhail Heavy Stubber', 'Lancer Laser Destroyer']
- `space-marines`/weapon_options.json **Invictor Tactical Warsuit**: lost fixed weapons: ['Heavy Bolter', 'Invictor Fist', 'Twin Ironhail Heavy Stubber']
- `space-marines`/weapon_options.json **Predator Annihilator**: lost fixed weapons: ['Armoured Tracks', 'Predator Twin Lascannon']
- `space-marines`/weapon_options.json **Predator Destructor**: lost fixed weapons: ['Armoured Tracks', 'Predator Autocannon']
- `space-marines`/weapon_options.json **Redemptor Dreadnought**: lost fixed weapons: ['Heavy Flamer', 'Heavy Onslaught Gatling Cannon', 'Macro Plasma Incinerator']; builds collapsed 3 -> 1; lost slot choices: ['Ranged weapon 1', 'Ranged weapon 1', 'Ranged weapon 1']
- `space-marines`/weapon_options.json **Stormhawk Interceptor**: lost fixed weapons: ['Armoured Hull']; lost slot choices: ['Ranged weapon 1']
- `space-marines`/weapon_options.json **Stormraven Gunship**: lost fixed weapons: ['Hurricane Bolter']
- `space-marines`/weapon_options.json **Thunderhawk Gunship**: lost slot choices: ['Turbo-laser destructor', 'Missile battery 1', 'Missile battery 2']
- `space-wolves`/characters.json **Wolf Guard Battle Leader**: lost slot choices: ['Melee weapon 1']
- `space-wolves`/weapon_options.json **Venerable Dreadnought**: lost fixed weapons: ['Fenrisian great axe']
- `tau-empire`/characters.json **Kroot Lone-Spear**: lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Ax-1-0 Tiger Shark**: lost fixed weapons: ['Burst cannon', 'Seeker missile']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Devilfish**: lost fixed weapons: ['Seeker missile', 'Smart missile system', 'Twin pulse carbine']
- `tau-empire`/weapon_options.json **Ghostkeel Battlesuit**: lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2']
- `tau-empire`/weapon_options.json **Hammerhead Gunship**: lost fixed weapons: ['Accelerator burst cannon', 'Seeker missile', 'Smart missile system', 'Twin pulse carbine']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Manta**: lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Razorshark Strike Fighter**: lost fixed weapons: ['Accelerator burst cannon', 'Missile pod']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Riptide Battlesuit**: lost fixed weapons: ['Missile pod', 'Twin fusion blaster', 'Twin plasma rifle', 'Twin smart missile system']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Sky Ray Gunship**: lost fixed weapons: ['Accelerator burst cannon', 'Seeker missile rack', 'Smart missile system', 'Twin pulse carbine']
- `tau-empire`/weapon_options.json **Stormsurge**: lost fixed weapons: ["Twin T'au flamer", 'Twin airbursting fragmentation projector', 'Twin burst cannon']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Sun Shark Bomber**: lost fixed weapons: ['Missile pod', 'Twin missile pod']; lost slot choices: ['Ranged weapon 1']
- `tau-empire`/weapon_options.json **Tiger Shark**: lost fixed weapons: ['Burst cannon', 'Seeker missile', 'Skyspear missile rack', 'Swiftstrike burst cannon', 'Swiftstrike railgun']; lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2']
- `thousand-sons`/weapon_options.json **Chaos Predator Annihilator**: lost slot choices: ['Ranged weapon 1']
- `thousand-sons`/weapon_options.json **Chaos Predator Destructor**: lost slot choices: ['Ranged weapon 1']
- `thousand-sons`/weapon_options.json **Defiler**: lost slot choices: ['Ranged weapon 1']
- `thousand-sons`/weapon_options.json **Forgefiend**: lost fixed weapons: ['Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Forgefiend claws', 'Forgefiend claws', 'Forgefiend jaws', 'Forgefiend jaws', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon']; builds collapsed 4 -> 1
- `thousand-sons`/weapon_options.json **Helbrute**: lost slot choices: ['Ranged weapon 1']
- `tyranids`/characters.json **Hive Tyrant**: lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2', 'Melee weapon 1', 'Melee weapon 2']
- `tyranids`/characters.json **Tervigon**: lost fixed weapons: ['Stinger salvoes']
- `tyranids`/weapon_options.json **Harpy**: lost fixed weapons: ['Stinger salvoes', 'Stinger salvoes', 'Twin heavy venom cannon', 'Twin stranglethorn cannon']; builds collapsed 2 -> 1
- `tyranids`/weapon_options.json **Tyrannofex**: lost fixed weapons: ['Acid spray', 'Fleshborer hive', 'Powerful limbs', 'Powerful limbs', 'Powerful limbs', 'Rupture cannon', 'Stinger salvoes', 'Stinger salvoes', 'Stinger salvoes']; builds collapsed 3 -> 1
- `world-eaters`/characters.json **Bloodthirster**: lost slot choices: ['Melee weapon 1']
- `world-eaters`/weapon_options.json **Chaos Predator Annihilator**: lost slot choices: ['Ranged weapon 1']
- `world-eaters`/weapon_options.json **Chaos Predator Destructor**: lost slot choices: ['Ranged weapon 1']
- `world-eaters`/weapon_options.json **Defiler**: lost slot choices: ['Ranged weapon 1']
- `world-eaters`/weapon_options.json **Forgefiend**: lost fixed weapons: ['Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Ectoplasma cannon', 'Forgefiend claws', 'Forgefiend claws', 'Forgefiend jaws', 'Forgefiend jaws', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon', 'Hades autocannon']; builds collapsed 4 -> 1
- `world-eaters`/weapon_options.json **Helbrute**: lost slot choices: ['Ranged weapon 1']
- `world-eaters`/weapon_options.json **Khorne Lord Of Skulls**: lost slot choices: ['Ranged weapon 1', 'Ranged weapon 2', 'Melee weapon 1']
