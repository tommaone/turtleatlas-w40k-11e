# data/config/ — Faction Configs

Per-faction configuration consumed by the DPP engine and MCP server.

## Structure

```
data/config/
├── _base.json              # Shared target/mission profiles (DPP profiles)
├── chaos-knights/
│   └── supported.json      # Faction metadata: army rules, meta profiles, dispositions
├── chaos-daemons/
│   └── supported.json
└── grey-knights/
    └── supported.json
```

## Mechanical Detachment Modifiers — RETIRED (2026-08-27)

Mechanical detachment scoring via `detachment_modifiers.json` is **retired**.

**Why:** most detachment buffs cannot be expressed as numeric DPP/SURV/MOB modifiers, and the auto-generated `detachment_modifiers.json` files carried fabricated rules — the "recommended loadout by detachment" output was fake engine output.

**Current behaviour:**
- The DPP engine does NOT load or apply mechanical detachment modifiers. `detachment == generalist` for every faction.
- Detachment strength is now a **heuristic** (expert-rated `detachments.json`: `dp_cost`, `disposition`, `strength`, `best_for`, `source`), never engine-computed.
- `findings` detachment view and MCP detachment ratings read this heuristic data.
- Generalist baseline must stay byte-identical — do not re-introduce detachment scoring as engine output.

**Rules moving forward:**
1. **No fake engine output.** Detachments are not scored numerically by the engine. Ever.
2. **Heuristic data only.** Detachment strengths/likes live in `detachments.json` as expert ratings with `_source`.
3. **If a mechanic truly models** as a conditional modifier, you may add it to engine logic — but only with a verified `_source`, applied to ALL factions symmetrically, and it must NOT change the generalist baseline.
4. `list_detachments_with_modifiers()` is a retired API returning `[]`.

## Cross-Faction Unit Restrictions — Space Marine Chapters

**Each Space Marine chapter can ONLY use its own chapter-specific characters and units.**

Chapters share generic SM datasheets (Rhinos, Land Raiders, Intercessors, Devastators, etc.) but each chapter has its own unique characters that CANNOT be used by other chapters.

### Restricted units by chapter

| Chapter | Characters NOT usable by other chapters |
|---------|----------------------------------------|
| Ultramarines | Roboute Guilliman, Chief Librarian Tigurius, Captain Titus, Cato Sicarius, Marneus Calgar, Uriel Ventris, Victrix Honour Guard |
| Blood Angels | Commander Dante, Chief Librarian Mephiston, Astorath, Lemartes, The Sanguinor, Death Company characters, Sanguinary Guard |
| Dark Angels | Azrael, Asmodai, Belial, Ezekiel, Lazarus, Sammael, Lion El'Jonson, Deathwing/Ravenwing characters |
| Space Wolves | Logan Grimnar, Bjorn The Fell-Handed, Ragnar Blackmane, Njal Stormcaller, Ulrik The Slayer, Arjac Rockfist, Wolf Guard characters |
| Black Templars | High Marshal Helbrecht, Emperor's Champion, Chaplain Grimaldus, Castellan, Marshal, Sword Brethren |
| Imperial Fists | Pedro Kantor, Darnath Lysander |
| Iron Hands | Iron Father Feirros, Caanok Var |
| Raven Guard | Kayvaan Shrike, Aethon Shaan |
| White Scars | Kor'Sarro Khan, Suboden Khan |
| Salamanders | Vulkan He'Stan, Adrax Agatone |
| Deathwatch | Watch Master, Watch Captain Artemis, Kill Teams |

### What CAN be shared

Generic SM datasheets that ALL chapters can use:
- Vehicles: Rhinos, Land Raiders, Razorbacks, Predators, Gladiators, Repulsors
- Dreadnoughts: Redemptor, Brutalis, Ballistus, standard Dreadnoughts
- Battleline: Intercessors, Assault Intercessors, Heavy Intercessors, Tactical Squads
- Supports: Devastators, Sternguard, Vanguard Veterans, Assault Terminators
- Characters: Captains, Lieutenants, Chaplains, Librarians, Techmarines, Apothecaries (generic versions)

### Rule of thumb

If a unit name includes a chapter-specific keyword (e.g., "Blood Angels Captain", "Deathwing Knights", "Wolf Guard Terminators"), it's restricted to that chapter ONLY. If it's a generic name (e.g., "Captain", "Intercessor Squad", "Land Raider"), it's usable by all chapters.

**When building a chapter config, do NOT include characters from other chapters.** This was the Dark Angels incident (2026-07-23): Ultramarines characters were incorrectly added to DA config.

---

## Current Factions

| Faction | Detachments | Status |
|---------|-------------|--------|
| Grey Knights | 9 | Verified from 40k.app |
| Chaos Knights | 8 | Verified from 40k.app |
| Chaos Daemons | 9 | Verified from 40k.app (4-god breakdown) |
