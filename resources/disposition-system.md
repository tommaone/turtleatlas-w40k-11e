# Detachment Disposition System

The Detachment Disposition system is a faction-agnostic framework that determines
how your army's detachments align to different mission types.

---

## What is a Disposition?

Each detachment enables exactly **one** disposition. A disposition describes the
strategic profile of a detachment — what it's designed to do on the battlefield.
There are 5 dispositions in total.

A detachment's disposition is defined in its faction pack JSON. When building an
army, you select a mission, then your detachments' dispositions determine whether
you get a mission alignment bonus.

---

## The 5 Dispositions

| Disposition | Focus | DPP Optimisation |
|-------------|-------|------------------|
| **Purge the Foe** | Kill-focused — rewards high DPS, trading efficiency, threat range | DPS (damage output) |
| **Take and Hold** | Objective-focused — rewards durability, OC, mobility for board control | Survival & board presence |
| **Reconnaissance** | Mobility and positioning — rewards speed, infiltration, deep strike | Mobility & deployment |
| **Priority Assets** | Balanced with assassination focus — rewards efficient trading and character kills | Mixed (DPS + survival) |
| **Disruption** | Deny and control — rewards battleshock, area denial, movement blocking | Board control & denial |

Each disposition has a JSON profile in `data/dispositions.json` with DPS/SURV/MOB
weighting factors used by the engine for mission-aligned ranking.

---

## DP Budget

Detachment Points (DP) are a resource that limits how many detachments you can take,
based on game size:

| Game Size | Points | Max DP | Typical Detachments |
|-----------|--------|--------|-------------------|
| Combat Patrol | 500pts | 1 | 1 |
| Incursion | 1000pts | 2 | 1–2 |
| Strike Force | 2000pts | 3 | 2–3 |
| Onslaught | 3000pts | 4 | 2–4 |

Each detachment has a DP cost (1–3), defined in its faction pack JSON
(e.g. `data/grey-knights-faction-pack.json`). The total DP across all detachments
in your army cannot exceed the game size's max DP.

---

## Mission Alignment

When you select a mission, your army must include **at least one detachment**
whose disposition matches the chosen mission.

- If at least one detachment matches → your army is **aligned** and receives the
  mission bonus
- If no detachment matches → your army is **unaligned** and receives no mission
  bonus

Mission alignment data is in `data/dispositions.json` under `mission_alignment`.

---

## Why It Matters for DPP

Disposition tells the engine what to optimise for:

| Disposition | Primary Stat | Secondary Stats |
|-------------|-------------|-----------------|
| Purge the Foe | DPP (damage) | Threat range |
| Take and Hold | SURV (durability) | OC, MOB |
| Reconnaissance | MOB (mobility) | Deployment options |
| Priority Assets | DPP + SURV | Character kill efficiency |
| Disruption | Control profile | Battleshock, area denial |

When the ranking engine has no explicit mission flag, it defaults to **Purge the Foe**
per the current competitive meta (see `resources/meta-bias.md`).

---

## Current Meta Bias (July 2026)

Only **Purge the Foe** and **Take and Hold** are competitively viable as of July 2026
per Mordian Glory community consensus. The other three dispositions (Reconnaissance,
Priority Assets, Disruption) are effectively dead until GW revises the GT Mission Pack.

See `resources/meta-bias.md` for the full bias analysis and expiry conditions.

---

## Machine-Readable Data

- **`data/dispositions.json`** — disposition definitions, DP budgets, mission
  alignment, meta bias flags
- **Faction pack JSONs** (e.g. `data/grey-knights-faction-pack.json`) — per-detachment
  dispositions and DP costs
- **`resources/meta-bias.md`** — human-readable meta bias analysis
