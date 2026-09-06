# Choosing Your Army — strength, versatility, fit

*Generated 2026-09-06 from engine outputs (rank-decay roster index, MFM v1.4) + expert first-army-fit ratings. Full method + caveats in findings/advisor.json.*

> This narrows the field — it tells you where each faction's strength sits today and what the army demands from you as a player. It cannot tell you the future meta.

## How to read this (plain words — judgement layer, not engine fact)

The engine measures how strong each faction's models are on paper
(statlines and points). It cannot measure rules packages, skill floor,
or how punishing an army is to play — those are the expert calls below,
each carrying a source trail in the faction's expert file.

- **Strength** — where the faction ranks today on model quality.
  Changes with balance updates; a strong army can get nerfed.
- **Versatility** — does it fight well on every mission type, or only
  one? Versatile armies forgive list-building mistakes.
- **First-army fit** — expert-rated Great / Good / Demanding / Bad,
  authored in resources/experts/<faction>.md. This is a skill-floor
  judgement, NOT engine fact. Engine "statline bulk" (median wounds
  across the whole roster, vehicles included) is listed in
  findings/advisor.json as reference only — it is NOT a first-army
  signal: World Eaters read "Durable" off a vehicle-inflated median
  while their 2W melee core punishes every positioning error.
- **GW attention** — factions whose points changed a lot recently keep
  changing. Playing one means accepting that your points and rules
  will move under you.


## If this is your first army

> Start with a faction expert-rated **Great** (or **Good** with versatility above the bottom quarter). Statline bulk (big wound pools) is an engine fact, NOT a skill-floor signal — World Eaters read 'Durable' off a vehicle-inflated wound median while their 2W melee core punishes every positioning error.

> Factions not listed have no expert first-army-fit rating yet: their engine strength is shown below, but the guide cannot certify them as forgiving.

- **Dark Angels** — deep durable bench (Deathwing terminator core), straightforward mid-range shooting, and six 1DP detachments forgive list-building; the classic forgiving first army.
- **Necrons** — Reanimation Protocols literally undo mistakes; warrior bricks plus durable monsters forgive positioning errors.
- **T'au Empire** — castle-and-shoot with durable suits; minimal melee exposure if you keep range.
- **Adeptus Custodes** — W3-4 baseline with a near-universal 4+ invuln and tiny model count; positioning is forgiving.
- **Death Guard** — T5 infantry, contagion aura, and -1D make mistakes survivable; damage arrives from statlines, not combos.

## Strongest long-term signal
- **Aeldari** — strength 69.0, plays all missions (Unrated first-army fit)
- **Blood Angels** — strength 68.6, plays all missions (Demanding first-army fit)
- **Chaos Daemons** — strength 68.4, plays all missions (Demanding first-army fit)

## Specialist picks (strong in one mission)

- **Space Marines** — shines in Priority Assets (Unrated first-army fit)
- **Dark Angels** — shines in Priority Assets (Great first-army fit)
- **Black Templars** — shines in Priority Assets (Unrated first-army fit)

## Active GW tuning (expect repricing)

- **Orks** — 245 MFM changelog entries
- **Astra Militarum** — 108 MFM changelog entries
- **Dark Angels** — 94 MFM changelog entries
- **Space Wolves** — 91 MFM changelog entries
- **Space Marines** — 82 MFM changelog entries
- **Aeldari** — 76 MFM changelog entries
- **Black Templars** — 74 MFM changelog entries

## Underrated right now

- **Necrons** — overall 62.7, versatile 86.0
- **Drukhari** — overall 62.3, versatile 90.3
- **Thousand Sons** — overall 62.1, versatile 87.3
- **World Eaters** — overall 62.0, versatile 88.5
- **Emperor's Children** — overall 61.1, versatile 90.9
- **T'au Empire** — overall 60.3, versatile 87.1

## Honest limitations

- meta_ceiling is engine-computed only for factions with VERIFIED detachment data (grey-knights, chaos-knights, chaos-daemons, dark-angels, space-marines); null = generalist index is the ceiling proxy (auto-generated MFM stubs are not detachment rules)
- statline quality persists across balance patches; rules packages do not
- points churn counts changelog mentions since edition start - a proxy for GW attention, not a prediction; Astartes flavours share one codex so their churn is partially double-counted
- win-rate correlation is partial: community results include rules packaging this index deliberately excludes
- first-army-fit is an expert judgement (user-domain + rule-text sourced per faction in resources/experts) — re-audit when the meta or play preferences shift
