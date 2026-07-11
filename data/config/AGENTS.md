# data/config/ — Detachment Modifier Configs

Per-faction detachment modifier JSON files consumed by the DPP engine and MCP server.

## Structure

```
data/config/
├── _base.json              # Shared target/mission profiles (DPP profiles)
├── chaos-knights/
│   └── detachment_modifiers.json
├── chaos-daemons/
│   └── detachment_modifiers.json
└── grey-knights/
    └── detachment_modifiers.json
```

## Detachment Modifier Integrity — Hard Rules

**Do NOT fabricate detachment rules.** Every entry in `detachment_modifiers.json` must be verifiable from a real source. If you don't know the rule, you don't write a modifier.

### Verification chain (mandatory)

1. **Find the actual rule description** from one of:
   - Official Warhammer Community faction focus articles
   - Goonhammer/Tabletop Battles faction pack reviews (they have review copies)
   - 40k.app official rules database
   - GW's own faction pack PDFs on warhammer-community.com

2. **Translate the mechanic to a modifier**, not the name. A detachment called "Synergized Assault" does NOT imply rerolls — read what it actually does.

3. **If the mechanic can't be expressed** as a simple numeric/boolean modifier (hit_modifier, sustained_hits_extra, reroll_hits, plus1_to_wound, lethal_hits, movement_bonus, invulnerable_save, feel_no_pain, stealth, advance_and_charge, etc.), then:
   - Set `_engine_note` explaining why it can't be modelled
   - Set NO numeric modifiers (do NOT approximate, do NOT guess)
   - Example: Helhunt Lance "Masters of the Pack" (aura self-affection) — no DPP modifier, just a note

4. **Every entry gets a `_source` field** pointing to the verified source article/URL.

5. **Cross-check all three vectors.** If the detachment rule affects something the engine can't model (battleshock, CP reduction, aura interactions, detection range), say so explicitly in `_engine_note` rather than faking a modifier on a different vector.

### Violation handling

If Shredder review finds a detachment modifier without a `_source` or with an `_engine_note` that reads like a guess:
- ❌ The modifier is removed immediately
- ❌ The config is marked as "unverified — stripped"
- ❌ No replacement until a real source is found
- ❌ The agent who created it must explain which source was used and how the mechanic was translated

The Helhunt Lance incident (fabricated Synergized Assault as reroll 1s hit+wound) is the precedent: **one fabricated rule means every rule from that agent is suspect.** The only fix is source-level verification.

### `_source` annotation format

```json
{
  "name": "Masters of the Pack",
  "_source": "https://www.tabletopbattles.com/detachment-focus-helhunt-lance",
  "_engine_note": "Aura self-affection — depends on specific auras carried by the Knight. Cannot be modelled as a universal DPP modifier.",
  "affects": "dpp",
  ...
}
```

## Current Factions

| Faction | Detachments | Status |
|---------|-------------|--------|
| Grey Knights | 9 | Verified from 40k.app |
| Chaos Knights | 8 | Verified from 40k.app |
| Chaos Daemons | 9 | Verified from 40k.app (4-god breakdown) |
