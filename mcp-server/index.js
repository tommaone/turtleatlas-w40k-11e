#!/usr/bin/env node
/**
 * turtleatlas-w40k-11e MCP server
 *
 * Serves 11th Edition Warhammer 40k rules data and DPP computations.
 * Run: node index.js [--port=PORT]
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { randomUUID } from "node:crypto";
import express from "express";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const BASE_DIR = join(__dirname, "..");
const DATA_DIR = join(BASE_DIR, "data");
const MERGED_DIR = join(DATA_DIR, "merged");
const CONFIG_DIR = join(DATA_DIR, "config");
const FINDINGS_DIR = join(BASE_DIR, "findings");
const ADVISOR_FILE = join(FINDINGS_DIR, "advisor.json");
const TIERS_FILE = join(FINDINGS_DIR, "army_tiers.json");
const MISSIONS = [
  "Take and Hold",
  "Purge the Foe",
  "Reconnaissance",
  "Priority Assets",
  "Disruption",
];

class TurtleAtlasW40kServer {
  constructor() {
    // Core rules never generated (needs pymupdf + GW PDFs) — always null
    this.coreRules = null;

    // Auto-discover factions from data/merged/*.json + data/config/*/
    this.factions = this.#discoverFactions();
    this.defaultFaction = "grey-knights";

    this.server = new Server(
      {
        name: "turtleatlas-w40k-11e",
        version: "1.0.0",
      },
      { capabilities: { tools: {} } },
    );

    this.#setupToolHandlers();
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  #loadJson(path) {
    try {
      if (!existsSync(path)) return null;
      return JSON.parse(readFileSync(path, "utf8"));
    } catch (err) {
      console.error(`Failed to load ${path}: ${err.message}`);
      return null;
    }
  }

  /**
   * Auto-discover factions from data/merged/*.json and data/config/
   * Each faction gets: mergedUnits (from merged) + config (from config)
   */
  #discoverFactions() {
    const factions = {};

    // 1. Scan merged dir for unit data
    try {
      const mergedFiles = readdirSync(MERGED_DIR).filter(f => f.endsWith(".json"));
      for (const file of mergedFiles) {
        const key = file.replace(".json", "");
        const data = this.#loadJson(join(MERGED_DIR, file));
        if (!data) continue;
        factions[key] = { mergedUnits: data, config: null, detachmentModifiers: null };
      }
    } catch (err) {
      console.error(`Failed to scan merged dir: ${err.message}`);
    }

    // 2. Load config files (detachments.json heuristic ratings, supported.json) into matching factions
    try {
      const configDirs = readdirSync(CONFIG_DIR, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith("_"))
        .map(d => d.name);

      for (const dir of configDirs) {
        const detPath = join(CONFIG_DIR, dir, "detachments.json");
        const supPath = join(CONFIG_DIR, dir, "supported.json");

        if (!factions[dir]) factions[dir] = { mergedUnits: null, config: null, detachmentModifiers: null };

        // detachments.json = heuristic ratings (classification: heuristic),
        // NOT mechanical engine modifiers (which are retired 2026-08-27).
        factions[dir].detachmentModifiers = this.#loadJson(detPath);
        factions[dir].config = this.#loadJson(supPath);
      }
    } catch (err) {
      console.error(`Failed to scan config dir: ${err.message}`);
    }

    const loaded = Object.keys(factions).map(k => {
      const f = factions[k];
      return `${k}(units=${f.mergedUnits ? f.mergedUnits.units?.length || 0 : 0}, det=${f.detachmentModifiers ? Object.keys(f.detachmentModifiers.detachments || {}).length : 0})`;
    }).join(", ");
    console.error(`Discovered factions: ${loaded}`);

    return factions;
  }

  /**
   * Call the Python engine via subprocess (stdin) for any function.
   */
  #runPython(code, args) {
    const result = spawnSync("python3", ["-c", code], {
      input: JSON.stringify(args),
      encoding: "utf8",
      timeout: 15000,
      maxBuffer: 1024 * 1024,
    });

    if (result.error) {
      return { error: result.error.message };
    }
    if (result.status !== 0) {
      return { error: `Python exited ${result.status}: ${result.stderr.toString().trim()}` };
    }
    const output = result.stdout.toString().trim();
    if (!output) {
      return { error: `No output from engine. Stderr: ${result.stderr.toString().trim()}` };
    }
    try {
      return JSON.parse(output);
    } catch {
      return { error: `Failed to parse engine output: ${output.slice(0, 200)}` };
    }
  }

  /**
   * Call the Python DPP engine via subprocess (stdin).
   */
  #runDppEngine(args) {
    const code = `
import sys, json, re
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.dpp import compute_weapon_dpp, WeaponProfile, TargetProfile, HitMode, WeaponModifier
from engine.weapon_loader import _parse_attacks

a = json.loads(sys.stdin.read())

# data/merged stores A and D as display strings: "4", "D6", "2D6", "D6+1".
# The engine already has the canonical flattener (_parse_attacks: D6->3.5,
# 2D6->7.0, "3"->3.0). Reuse it rather than hand-rolling a second parser, so
# the MCP surface and the loader can never disagree about what "D6" means.
def as_number(v):
    if isinstance(v, bool):
        raise ValueError("boolean is not a number")
    if isinstance(v, (int, float)):
        return float(v)
    return _parse_attacks(str(v))

def as_bs(v):
    # BS/WS render as "3+"; Torrent weapons carry "N/A" and skip the hit roll
    # entirely (dpp.py), so 0.0 is a safe, never-used placeholder for them.
    if isinstance(v, bool):
        raise ValueError("boolean is not a number")
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"^\\s*(\\d+)", str(v or ""))
    return float(m.group(1)) if m else 0.0

raw_damage = a["damage"] if isinstance(a["damage"], str) else None

wp = WeaponProfile(
    name=a.get("weapon_name", "Custom"),
    attacks=as_number(a["attacks"]),
    bs=as_bs(a["bs"]),
    strength=a["strength"],
    ap=a["ap"],
    damage=as_number(a["damage"]),
    damage_raw=raw_damage,
    abilities=[x.strip() for x in a.get("abilities", "").split(",") if x.strip()],
)
target = TargetProfile(
    toughness=a["target_toughness"],
    save=a["target_save"],
    invuln=a.get("target_invuln"),
    wounds_per_model=a.get("wounds_per_model", 1),
    model_count=a.get("model_count", 1),
)
mode_map = {"normal": HitMode.NORMAL, "cover": HitMode.COVER, "plunging_fire": HitMode.PLUNGING_FIRE}
mode = mode_map.get(a.get("hit_mode", "normal"), HitMode.NORMAL)
points = a.get("unit_points", 1)

r = compute_weapon_dpp(wp, target, unit_points=points, hit_mode=mode)
print(json.dumps(r))
`;
    return this.#runPython(code, args);
  }

  /**
   * Call compute_unit_dpp: every weapon of a unit, one shared points cost,
   * with the overkill cap applied ONCE to the summed total.
   */
  #runUnitDppEngine(args) {
    const code = `
import sys, json, re
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.dpp import compute_unit_dpp, WeaponProfile, TargetProfile, HitMode
from engine.weapon_loader import _parse_attacks

a = json.loads(sys.stdin.read())

def as_number(v):
    if isinstance(v, bool):
        raise ValueError("boolean is not a number")
    if isinstance(v, (int, float)):
        return float(v)
    return _parse_attacks(str(v))

def as_bs(v):
    if isinstance(v, bool):
        raise ValueError("boolean is not a number")
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"^\\s*(\\d+)", str(v or ""))
    return float(m.group(1)) if m else 0.0

weapons = []
for w in a["weapons"]:
    raw_damage = w["damage"] if isinstance(w["damage"], str) else None
    weapons.append(WeaponProfile(
        name=w.get("weapon_name", "Custom"),
        attacks=as_number(w["attacks"]),
        bs=as_bs(w["bs"]),
        strength=w["strength"],
        ap=w["ap"],
        damage=as_number(w["damage"]),
        damage_raw=raw_damage,
        count=w.get("count", 1),
        abilities=[x.strip() for x in (w.get("abilities") or "").split(",") if x.strip()],
    ))

target = TargetProfile(
    toughness=a["target_toughness"],
    save=a["target_save"],
    invuln=a.get("target_invuln"),
    wounds_per_model=a.get("wounds_per_model", 1),
    model_count=a.get("model_count", 1),
)
mode_map = {"normal": HitMode.NORMAL, "cover": HitMode.COVER, "plunging_fire": HitMode.PLUNGING_FIRE}
mode = mode_map.get(a.get("hit_mode", "normal"), HitMode.NORMAL)

r = compute_unit_dpp(weapons, target, points=a.get("unit_points", 1), hit_mode=mode)
print(json.dumps(r))
`;
    return this.#runPython(code, args);
  }

  /**
   * Call the Python SURV engine via subprocess.
   */
  #runSurvEngine(args) {
    const code = `
import sys, json
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.dpp import compute_surv, UnitDefense

a = json.loads(sys.stdin.read())

defense = UnitDefense(
    toughness=a["toughness"],
    wounds_per_model=a["wounds_per_model"],
    save=a["save"],
    invuln=a.get("invuln"),
    fnp=a.get("fnp"),
    models=a.get("models", 1),
)

r = compute_surv(defense, unit_points=a.get("unit_points", 1))
print(json.dumps(r))
`;
    return this.#runPython(code, args);
  }

  /**
   * Call the Python MOB engine via subprocess.
   */
  #runMobEngine(args) {
    const code = `
import sys, json
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.dpp import compute_mob

a = json.loads(sys.stdin.read())

r = compute_mob(
    movement=a.get("movement", 6),
    fly=a.get("fly", False),
    deep_strike=a.get("deep_strike", False),
    oc=a.get("oc", 1),
    keywords=a.get("keywords", []),
    transport_capacity=a.get("transport_capacity"),
    abilities=a.get("abilities", []),
)
print(json.dumps(r))
`;
    return this.#runPython(code, args);
  }

  /**
   * Call the Python ranking engine via subprocess.
   */
  #runRankEngine(args) {
    const code = `
import sys, json
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.ranking import RankingEngine

a = json.loads(sys.stdin.read())

faction = a.get("faction", "grey-knights")
target_name = a.get("target", "MEQ")
mission_name = a.get("mission")
tier = a.get("tier", "1st")
meta_name = a.get("meta")
detachment = a.get("detachment")
detachment_choice = a.get("detachment_choice")
top_n = a.get("top_n", 10)

eng = RankingEngine(faction)
targets = eng.config.target_profiles

# Resolve target
if meta_name:
    target = targets.get("MEQ")
else:
    target = targets.get(target_name)

if not target:
    print(json.dumps({"error": f"Target profile '{target_name}' not found. Available: {list(targets.keys())}"}))
    sys.exit(0)

results = eng.compute_ranking(
    target=target,
    mission=mission_name,
    meta_name=meta_name,
    tier=tier,
    detachment=detachment,
    detachment_choice=detachment_choice,
)

output = []
for r in results[:top_n]:
    entry = {
        "name": r["name"],
        "points": r["points"],
        "dpp": r["dpp"],
        "total_damage": r["total_damage"],
        "surv_ew_ap0": r["surv"]["effective_wounds"]["ap0"],
        "surv_ew_ap2": r["surv"]["effective_wounds"]["ap2"],
        "surv_ew_ap4": r["surv"]["effective_wounds"]["ap4"],
        "mob_tier": r["mob"]["mobility_tier"],
        "mob_movement": r["mob"]["movement"],
        "mob_deep_strike": r["mob"]["deep_strike"],
        "loadout": r.get("loadout_desc", ""),
    }
    if "_mission_score" in r:
        entry["mission_score"] = r["_mission_score"]
    if "_dps_pct" in r:
        entry["dps_pct"] = r["_dps_pct"]
        entry["surv_pct"] = r["_surv_pct"]
        entry["mob_pct"] = r["_mob_pct"]
    output.append(entry)

print(json.dumps(output))
`;
    return this.#runPython(code, args);
  }

  // -------------------------------------------------------------------------
  // Tool handlers
  // -------------------------------------------------------------------------

  #setupToolHandlers(server = this.server) {
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "get_llm_contract",
          description:
            "LLM boundary contract — call BEFORE any other tool. Defines truth vs interpretation: engine_output (computed, never re-derived), heuristic (L2 ratings, traceable, AI-labeled), verbatim (L0 sources). Never strip _classification labels, never re-compute engine numbers, never paraphrase rules as authoritative, never assert combos as guarantees. Every recommendation carries context + assumption registry.",
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        {
          name: "list_factions",
          description:
            "List available factions with loaded data status.",
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        {
          name: "get_core_rules",
          description:
            "Get 11e core rules overview: cover, phases, common weapon abilities. Engine-modeled basics only — full rules require PDF parsing.",
          inputSchema: {
            type: "object",
            properties: {
              section: {
                type: "string",
                enum: ["abilities", "stratagems", "phases", "cover", "all"],
                description: "Which section to retrieve",
              },
            },
          },
        },
        {
          name: "get_ability",
          description:
            "Look up a weapon ability by name (engine-modeled only). E.g. SUSTAINED HITS, LETHAL HITS, COVER, PSYCHIC, TWIN-LINKED.",
          inputSchema: {
            type: "object",
            properties: {
              name: { type: "string", description: "Ability name" },
            },
            required: ["name"],
          },
        },
        {
          name: "get_detachment",
          description:
            "Get detachment info: verified MFM basics (dp, objective, enhancements — L0) + L2 static facts (rule paraphrase, strength rating, limitations). Mechanical engine modifiers are RETIRED (2026-08-27) — no DPP/SURV detachment buffs exist anymore.",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Detachment name (e.g. Argent Assault, Infernal Lance)",
              },
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights). Default: grey-knights",
              },
            },
            required: ["name"],
          },
        },
        {
          name: "compute_unit_dpp",
          description:
            "Compute expected damage per point for a WHOLE UNIT (all weapons combined) against one target, sharing a single points cost. Use this instead of compute_dpp when the question is about a squad or multi-weapon unit — summing several compute_dpp results yourself is exactly the arithmetic this contract forbids, and per-weapon overkill caps must not be added. The target's wound pool caps the SUMMED total once. Weapons accept datasheet strings verbatim (\"D6\", \"2D6\", \"3+\", \"N/A\").",
          inputSchema: {
            type: "object",
            properties: {
              unit_name: { type: "string", description: "Unit label" },
              weapons: {
                type: "array",
                minItems: 1,
                description:
                  "Every weapon the unit fires. One entry per weapon option; repeat an entry (or set count) for multiple of the same weapon.",
                items: {
                  type: "object",
                  properties: {
                    weapon_name: { type: "string", description: "Weapon name label" },
                    attacks: {
                      type: ["number", "string"],
                      description: "Number of attacks, or the datasheet dice expression verbatim (\"D6\", \"2D6\", 4).",
                    },
                    bs: {
                      type: ["number", "string"],
                      description: "Ballistic Skill as a number, or verbatim (\"3+\", \"N/A\").",
                    },
                    strength: { type: "number", description: "Weapon Strength" },
                    ap: { type: "number", description: "Weapon AP" },
                    damage: {
                      type: ["number", "string"],
                      description: "Damage per wound, or the dice expression verbatim (\"D6\", \"D6+1\", 2).",
                    },
                    count: {
                      type: "number",
                      description: "How many models carry this weapon (default 1).",
                    },
                    abilities: {
                      type: "string",
                      description:
                        "Comma-separated ability keywords, verbatim from get_unit. Torrent, Psychic, Sustained Hits, Lethal Hits, ANTI, Ignore Cover, Melta 2, Rapid Fire 2.",
                    },
                  },
                  required: ["attacks", "bs", "strength", "ap", "damage"],
                },
              },
              target_toughness: { type: "number", description: "Target toughness" },
              target_save: { type: "number", description: "Target save (e.g. 3 for 3+)" },
              target_invuln: {
                type: "number",
                description: "Target invulnerable save (e.g. 4 for 4+), if any",
              },
              wounds_per_model: {
                type: "number",
                minimum: 1,
                description: "Wounds per model on the target. Multiplies the pool. Defaults to 1.",
              },
              model_count: {
                type: "number",
                minimum: 1,
                description: "Models in the target unit. Multiplies the pool. Defaults to 1.",
              },
              hit_mode: {
                type: "string",
                enum: ["normal", "cover", "plunging_fire"],
                description: "normal / cover / plunging_fire",
              },
              unit_points: {
                type: "number",
                description: "Total points for the WHOLE unit (the shared denominator)",
              },
            },
            required: ["weapons", "target_toughness", "target_save"],
          },
        },
        {
          name: "compute_dpp",
          description:
            "Compute expected damage per point for a weapon profile vs a target. Supports 11e Cover (worsens BS) and Plunging Fire. MANDATORY: You MUST call this tool for all DPP values. NEVER compute, derive, estimate, or fabricate DPP numbers yourself — the engine applies the 11e wound table, Cover, Plunging Fire, abilities, and target profiles. Only this tool's output is authoritative. Violation produces unreliable results.",
          inputSchema: {
            type: "object",
            properties: {
              weapon_name: { type: "string", description: "Weapon name label" },
              attacks: {
                type: ["number", "string"],
                description: "Number of attacks, or the datasheet dice expression verbatim (e.g. 4, \"D6\", \"2D6\", \"D6+1\"). Strings are flattened by the engine's own _parse_attacks (D6 -> 3.5, 2D6 -> 7.0) so MCP and the loader can never disagree. Pass the value exactly as get_unit reports it.",
              },
              bs: {
                type: ["number", "string"],
                description: "Ballistic Skill as a number (3 for 3+) or verbatim (\"3+\", \"N/A\"). Torrent weapons report \"N/A\" and bypass the hit roll entirely; Psycannon-style weapons override BS via Psychic.",
              },
              strength: { type: "number", description: "Strength" },
              ap: {
                type: "number",
                description: "Armor Penetration (e.g. -1)",
              },
              damage: {
                type: ["number", "string"],
                description:
                  "Damage per wound, or the dice expression verbatim (e.g. 2, \"D6\", \"2D6\"). Strings are flattened via the engine's _parse_attacks and the raw expression is retained for honest damage-reroll math.",
              },
              abilities: {
                type: "string",
                description:
                  "Comma-separated abilities (e.g. 'Sustained Hits 1, Lethal Hits')",
              },
              target_toughness: { type: "number", description: "Target Toughness" },
              target_save: {
                type: "number",
                description: "Target Save (e.g. 3 for 3+)",
              },
              target_invuln: {
                type: "number",
                description: "Target Invuln save (e.g. 4 for 4++)",
              },
              wounds_per_model: {
                type: "number",
                minimum: 1,
                description:
                  "Whole number >= 1. Wounds per model on the target. Total damage is capped by wounds_per_model x model_count, so omitting this under-reports damage vs multi-wound or multi-model units. Defaults to 1. Check get_unit for the real value.",
              },
              model_count: {
                type: "number",
                minimum: 1,
                description:
                  "Whole number >= 1. Models in the target unit (squad size). Multiplies the wound pool for the damage cap. Defaults to 1.",
              },
              hit_mode: {
                type: "string",
                enum: ["normal", "cover", "plunging_fire"],
                description: "Cover or Plunging Fire mode",
              },
              unit_points: {
                type: "number",
                description: "Unit points cost for DPP",
              },
            },
            required: [
              "attacks",
              "bs",
              "strength",
              "ap",
              "damage",
              "target_toughness",
              "target_save",
            ],
          },
        },
        {
          name: "list_units",
          description: "List available units with their points costs.",
          inputSchema: {
            type: "object",
            properties: {
              search: {
                type: "string",
                description: "Optional search filter",
              },
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights). Default: grey-knights",
              },
            },
          },
        },
        {
          name: "get_unit",
          description:
            "Get full profile of a unit including weapons, stats, abilities.",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Unit name (case-insensitive partial match)",
              },
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights). Default: grey-knights",
              },
            },
            required: ["name"],
          },
        },
        {
          name: "get_stratagem",
          description:
            "Look up a core 11e stratagem by name (Command Reroll, Battle Shock, Inspired Leadership). Full stratagem text requires PDF parsing.",
          inputSchema: {
            type: "object",
            properties: {
              name: { type: "string", description: "Stratagem name" },
              detachment: {
                type: "string",
                description: "Optional detachment name to narrow search",
              },
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights). Default: grey-knights",
              },
            },
            required: ["name"],
          },
        },
        {
          name: "compute_surv",
          description:
            "Compute survivability metrics for a unit: effective wound pool at AP0/AP2/AP4, and points-per-effective-wound efficiency. MANDATORY: You MUST call this tool for all survivability values. NEVER compute, derive, or estimate effective wounds yourself. Only this tool's output is authoritative.",
          inputSchema: {
            type: "object",
            properties: {
              toughness: { type: "number", description: "Toughness characteristic" },
              wounds_per_model: { type: "number", description: "Wounds per model" },
              save: { type: "number", description: "Save characteristic (e.g. 3 for 3+)" },
              invuln: { type: "number", description: "Invulnerable save (e.g. 4 for 4++)" },
              fnp: { type: "number", description: "Feel No Pain (e.g. 6 for 6+++)" },
              models: { type: "number", description: "Number of models in unit" },
              unit_points: { type: "number", description: "Unit points cost" },
            },
            required: ["toughness", "wounds_per_model", "save", "models", "unit_points"],
          },
        },
        {
          name: "compute_mob",
          description:
            "Compute mobility and utility profile for a unit: movement, Fly, Deep Strike, OC, keywords, mobility tier. MANDATORY: You MUST call this tool for mobility values. Do not fabricate or approximate mobility metrics.",
          inputSchema: {
            type: "object",
            properties: {
              movement: { type: "number", description: "Movement in inches" },
              fly: { type: "boolean", description: "Has Fly keyword" },
              deep_strike: { type: "boolean", description: "Has Deep Strike ability" },
              oc: { type: "number", description: "Objective Control" },
              keywords: {
                type: "array",
                items: { type: "string" },
                description: "Unit keywords",
              },
              transport_capacity: { type: ["integer", "string", "null"], description: "Transport capacity in models (e.g. 12). Accepts an int, a numeric string, or a legacy BSData 'Transport' ability prose string, which is parsed. Pass null when the datasheet states no model count." },
              abilities: {
                type: "array",
                items: { type: "string" },
                description: "Relevant mobility abilities",
              },
            },
            required: ["movement", "oc"],
          },
        },
        {
          name: "rank_units",
          description:
            "Compute three-vector (DPS/SURV/MOB) ranking for all units in a faction. Supports target profile, mission weighting, pricing tier, meta profile, and detachment modifiers. MANDATORY: You MUST call this tool for all ranking output. NEVER fabricate, approximate, or re-compute DPP/SURV/MOB values yourself. The engine configures loadouts, applies detachment modifiers, and computes all three vectors. Only this tool's output is authoritative for ranking analysis. Violation: if you present numbers not from this tool's output, the analysis is unreliable.",
          inputSchema: {
            type: "object",
            properties: {
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights). Default: grey-knights",
              },
              target: {
                type: "string",
                description: "Target profile name (e.g. MEQ, TEQ, GEQ). Default: MEQ",
              },
              mission: {
                type: "string",
                description: "Mission profile name (e.g. Purge the Foe, Take and Hold)",
              },
              tier: {
                type: "string",
                enum: ["1st", "3rd"],
                description: "Pricing tier. Default: 1st",
              },
              meta: {
                type: "string",
                description: "Multi-target meta profile name (e.g. all-comers, vehicle-heavy)",
              },
              detachment: {
                type: "string",
                description: "Detachment name to apply modifiers from (e.g. Infernal Lance, Warpbane Task Force)",
              },
              detachment_choice: {
                type: "number",
                description: "Index of modifier choice (0-based). Default: 0",
              },
              top_n: {
                type: "number",
                description: "Number of results to return. Default: 10",
              },
            },
          },
        },
        {
          name: "get_findings",
          description:
            "Retrieve pre-computed DPP/SURV/MOB findings for a faction across all missions. These are pipeline-verified baseline values with known assumptions. Use as the ground truth for unit evaluation — the LLM layers detachment combos, disposition analysis, and cross-faction comparisons on top. MANDATORY: NEVER fabricate DPP, effective wounds, or mission scores. Only this tool's output is authoritative. Violation: presenting numbers not from this tool's output makes the analysis unreliable.",
          inputSchema: {
            type: "object",
            properties: {
              faction: {
                type: "string",
                description: "Faction key (e.g. grey-knights, chaos-knights)",
              },
              mission: {
                type: "string",
                enum: ["Take and Hold", "Purge the Foe", "Reconnaissance", "Priority Assets", "Disruption"],
                description: "Mission name filter. If omitted, returns all 5 missions.",
              },
              top_n: {
                type: "number",
                description: "Number of top units to return per mission (sorted by mission score). Default: 10. Use 0 for all units.",
              },
            },
            required: ["faction"],
          },
        },
        {
          name: "get_army_index",
          description:
            "Army-level meta index from findings/advisor.json: overall_index, ceiling, floor, versatility, roster_depth, best/worst disposition, points_churn, first_army_fit, and meta_ceiling. Use for 'how strong is this army' and 'what should I play first'. MANDATORY: NEVER compute or estimate an index yourself — the numbers are a rank-decay weighted mean of engine mission scores and are only authoritative from this tool. Note _classification on every row: some fields are engine output, others (first_army_fit) are expert judgement.",
          inputSchema: {
            type: "object",
            properties: {
              faction: {
                type: "string",
                description:
                  "Faction key (e.g. grey-knights). Omit to return every rated faction ranked by overall_index.",
              },
              limit: {
                type: "number",
                description:
                  "Max rows when listing all factions. Default: 30.",
              },
            },
          },
        },
        {
          name: "compare_factions",
          description:
            "Side-by-side comparison of 2-5 factions: per-mission scores from findings/army_tiers.json plus the advisor indices. Use for 'X vs Y'. MANDATORY: NEVER compute the comparison yourself — call this tool. The two sources rank differently on purpose: army_tiers is the rules-free generalist index, advisor carries rules-aware adjustment, so a gap between them is signal, not error.",
          inputSchema: {
            type: "object",
            properties: {
              factions: {
                type: "array",
                items: { type: "string" },
                description:
                  "2-5 faction keys (e.g. [\"grey-knights\",\"orks\"]).",
              },
            },
            required: ["factions"],
          },
        },
        {
          name: "get_faction_tiers",
          description:
            "Factions ranked by score for a single mission, from findings/army_tiers.json. Use for 'which armies suit Purge the Foe'. MANDATORY: NEVER fabricate a mission score — only this tool's output is authoritative. Set by_rank to false for a compact full table instead of a top-N cut.",
          inputSchema: {
            type: "object",
            properties: {
              mission: {
                type: "string",
                enum: ["Take and Hold", "Purge the Foe", "Reconnaissance", "Priority Assets", "Disruption", "overall"],
                description:
                  "Mission to rank by, or 'overall'. Omit for overall.",
              },
              top_n: {
                type: "number",
                description: "Rows to return. Default: 10.",
              },
            },
          },
        },
        {
          name: "list_findings_topics",
          description:
            "List the committed per-faction analysis reports under findings/, including one-off topic reports beyond findings.html (e.g. dark-angels/take-and-hold-trivector.html). Use to discover what written analysis exists before claiming nothing is on file. This tool lists filenames only — it does not summarise the reports, and no numeric claim may be sourced from it.",
          inputSchema: {
            type: "object",
            properties: {
              faction: {
                type: "string",
                description:
                  "Faction key to list topics for. Omit to list every faction's topics.",
              },
            },
          },
        },
      ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      switch (name) {
        case "get_llm_contract":
          return this.#handleGetLlmContract();
        case "list_factions":
          return this.#handleListFactions();
        case "get_core_rules":
          return this.#handleGetCoreRules(args);
        case "get_ability":
          return this.#handleGetAbility(args);
        case "get_detachment":
          return this.#handleGetDetachment(args);
        case "compute_dpp":
          return this.#handleComputeDpp(args);
        case "compute_unit_dpp":
          return this.#handleComputeUnitDpp(args);
        case "list_units":
          return this.#handleListUnits(args);
        case "get_unit":
          return this.#handleGetUnit(args);
        case "get_stratagem":
          return this.#handleGetStratagem(args);
        case "compute_surv":
          return this.#handleComputeSurv(args);
        case "compute_mob":
          return this.#handleComputeMob(args);
        case "rank_units":
          return this.#handleRankUnits(args);
        case "get_findings":
          return this.#handleGetFindings(args);
        case "get_army_index":
          return this.#handleGetArmyIndex(args);
        case "compare_factions":
          return this.#handleCompareFactions(args);
        case "get_faction_tiers":
          return this.#handleGetFactionTiers(args);
        case "list_findings_topics":
          return this.#handleListFindingsTopics(args);
        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${name}`,
          );
      }
    });
  }

  // -------- Core rules ----------------------------------------------------

  #handleGetCoreRules(_args) {
    // Core rules data requires PDF parsing (pymupdf) + GW PDFs — not available.
    // Return hardcoded 11e basics that are well-known.
    const section = (_args?.section || "all").toLowerCase();
    const lines = ["# 11th Edition Core Rules\n"];

    if (section === "cover" || section === "all") {
      lines.push(`## Cover (11e)\n`);
      lines.push(`- Cover worsens attacker's BS by 1 (does NOT modify saves)`);
      lines.push(`- Benefit of Cover: -1 to Hit roll`);
      lines.push(`- Plunging Fire (vertical): -1 to Hit roll (attacker) or +1 to Save (defender)`);
      lines.push(`- Ignores Cover: weapons with this ability ignore the -1 BS penalty`);
      lines.push(`- Heavy weapons ignore penalty from moving, but NOT from cover`);
    }

    if (section === "phases" || section === "all") {
      lines.push(`\n## Game Phases\n`);
      lines.push(`1. Command Phase — score objectives, battle-shock tests`);
      lines.push(`2. Movement Phase — Normal Move, Advance, Fall Back`);
      lines.push(`3. Shooting Phase — ranged attacks`);
      lines.push(`4. Charge Phase — declare and make charge moves`);
      lines.push(`5. Fight Phase — melee attacks (Fight first, then Fight last)`);
      lines.push(`6. Morale Phase — Battle-shock tests for below Starting Strength`);
    }

    if (section === "abilities" || section === "all") {
      lines.push(`\n## Common Weapon Abilities (engine-modeled)\n`);
      lines.push(`- **Sustained Hits X**: Critical hits (unmodified 6) deal X additional hits`);
      lines.push(`- **Lethal Hits**: Critical hits auto-wound (no wound roll)`);
      lines.push(`- **Devastating Wounds**: Critical wounds deal mortal wounds instead of normal damage`);
      lines.push(`- **Twin-Linked**: Re-roll wound rolls`);
      lines.push(`- **Ignores Cover**: Attack ignores cover BS penalty`);
      lines.push(`- **Torrent**: Auto-hit (no BS roll)`);
      lines.push(`- **Melta X**: Double damage within half range`);
      lines.push(`- **Lance**: +1 to wound when charging/charged/heroic intervention`);
      lines.push(`- **Anti-X Y+**: Auto-critical wound vs X keyword on Y+`);
    }

    if (section === "stratagems" || section === "all") {
      lines.push(`\n## Core Stratagems\n`);
      lines.push(`Stratagem text requires GW faction pack PDFs to parse. Use get_detachment for faction-specific stratagem names.`);
    }

    return this.#text(lines.join("\n"));
  }

  // -------- Ability lookup ------------------------------------------------

  #handleGetAbility(args) {
    const query = (args?.name || "").toUpperCase().trim();

    // Engine-modeled abilities with known effects
    const KNOWN_ABILITIES = {
      "SUSTAINED HITS": { name: "Sustained Hits", desc: "Critical hits (unmodified 6) score additional hits equal to the ability value (e.g. Sustained Hits 1 = 1 extra hit). Does NOT trigger on hit roll 1." },
      "LETHAL HITS": { name: "Lethal Hits", desc: "Critical hits (unmodified 6) auto-wound the target — no wound roll needed. Does NOT trigger on hit roll 1." },
      "DEVASTATING WOUNDS": { name: "Devastating Wounds", desc: "Critical wounds (unmodified 6 on wound roll) inflict mortal wounds equal to weapon damage instead of normal damage. Mortals bypass saves." },
      "TWIN-LINKED": { name: "Twin-Linked", desc: "Re-roll the wound roll." },
      "IGNORES COVER": { name: "Ignores Cover", desc: "The target does not benefit from Cover (BS penalty ignored)." },
      "TORRENT": { name: "Torrent", desc: "This weapon does not make hit rolls — it automatically hits." },
      "LANCE": { name: "Lance", desc: "+1 to wound roll when the bearer declared a charge, was charged, or performed a Heroic Intervention." },
      "MELTA X": { name: "Melta", desc: "If target is within half range, this weapon's Damage characteristic is doubled." },
      "HEAVY": { name: "Heavy", desc: "If the bearer moved, subtract 1 from hit rolls (does NOT apply to cover penalty)." },
      "ASSAULT": { name: "Assault", desc: "The bearer can shoot even after Advancing. -1 to hit after Advancing (unless weapon has Ignores Cover)." },
      "RAPID FIRE X": { name: "Rapid Fire X", desc: "If target is within half range, this weapon makes X additional attacks." },
      "PSYCHIC": { name: "Psychic", desc: "Weapon keyword. Attacks made with Psychic weapons ignore all hit roll modifiers (BS/WS modifiers do not apply). Psychic tests are a separate mechanic." },
      "ANTI-INFANTRY X+": { name: "Anti-Infantry X+", desc: "Attacks against INFANTRY keyword models are critical wounds on X+ (auto-wound)." },
      "ANTI-VEHICLE X+": { name: "Anti-Vehicle X+", desc: "Attacks against VEHICLE keyword models are critical wounds on X+ (auto-wound)." },
      "SUSTAINED HITS 1": { name: "Sustained Hits 1", desc: "Critical hits (unmodified 6) score 1 additional hit." },
      "SUSTAINED HITS 2": { name: "Sustained Hits 2", desc: "Critical hits (unmodified 6) score 2 additional hits." },
      "SUSTAINED HITS 3": { name: "Sustained Hits 3", desc: "Critical hits (unmodified 6) score 3 additional hits." },
    };

    const match = KNOWN_ABILITIES[query] ||
      Object.values(KNOWN_ABILITIES).find(a =>
        a.name.toUpperCase().includes(query) || query.includes(a.name.toUpperCase())
      );

    if (!match) {
      const allNames = Object.values(KNOWN_ABILITIES).map(a => a.name).join(", ");
      return this.#text(`Ability "${query}" not found in engine-modeled abilities.\n\nKnown abilities: ${allNames}\n\nNote: Full core rules text requires PDF parsing (not yet implemented). Only engine-modeled abilities are available.`);
    }

    return this.#text(`# ${match.name}\n\n${match.desc}\n\n---\n*Engine-modeled: this ability has a defined mechanical effect in DPP/SURV/MOB computation.*`);
  }

  // -------- Detachment lookup ---------------------------------------------

  #handleGetLlmContract() {
    const contract = `# LLM Boundary Contract (turtle-dojo mandate)

Call this tool FIRST, before any other tool in this server. It defines the
line between truth (engine/tool output) and interpretation (what the LLM
says about it). Violations produce fabricated or compressed beliefs that
look like facts.

## Classification labels (never strip, never omit)
- **engine_output** — engine-computed numbers (DPP/SURV/MOB, rankings).
  Authoritative for numbers. NEVER re-compute, derive, or estimate these
  yourself from raw data; the engine computes, the LLM narrates.
- **heuristic** — L2 detachment ratings (strength, disposition, rule
  paraphrase). Traceable to _source URLs. AI-labeled; not human-verified
  unless _meta.human_reviewed: true is set in the config.
- **verbatim** — L0 source data (MFM points, objective, enhancements).
  Cite as-is.

## Rules
1. Every response that interprets data self-labels: raw tool output carries
   its _classification; do not strip it, do not present heuristic ratings
   as engine facts.
2. No re-computation: never answer "how many wounds does X deal to Y" by
   doing the math yourself. Call compute_dpp / compute_surv / compute_mob.
3. No rule rewriting: never present a paraphrased rule as authoritative GW
   text. Quote verbatim (L0) or label your summary as "interpretation".
4. No ability-chaining certainty: frame combos as possibilities ("can",
   "may"), never guarantees ("will", "always").
5. No "best" without context: always give target type, range context,
   detachment modifier, and points efficiency. Frame as "favored when...",
   not "the best".
6. Every recommendation ships four parts: Context (assumptions), Answer
   (the recommendation), Why (stat/keyword basis), Limitation (when it
   fails or what counters it).`;
    return this.#text(contract);
  }

  #handleGetDetachment(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);

    const query = (args?.name || "").trim().toUpperCase();

    // Verified basics come from MFM merged detachments[] (L0).
    // Heuristic ratings come from detachments.json (L2, interpretation).
    const mergedDets = fd.mergedUnits?.detachments || [];
    const heuristic = fd.detachmentModifiers?.detachments || {};

    const slugify = (s) => (s || "").trim().toLowerCase()
      .replace(/ /g, "-").replace(/['\u2019]/g, "");
    // Query normalisation: strip spaces, hyphens AND apostrophes so
    // "Cabal Of Chaos", "cabal-of-chaos", "Mont’ka" and "CABAL" all match.
    const norm = (s) => (s || "").toUpperCase().replace(/[\s-'\u2019]/g, "");
    const nQuery = norm(query);

    const mergedByKey = {};
    for (const d of mergedDets) mergedByKey[slugify(d.name)] = d;

    // Match heuristic key first, then merged slug / merged name substring.
    const hKey = Object.keys(heuristic).find(k =>
      norm(k) === nQuery || norm(k).includes(nQuery) || nQuery.includes(norm(k))
    );
    const mergedMatch = mergedDets.find(d =>
      norm(d.name).includes(nQuery) || nQuery.includes(norm(d.name))
    );
    const mKey = Object.keys(mergedByKey).find(k =>
      norm(k) === nQuery || norm(k).includes(nQuery) || nQuery.includes(norm(k))
    );
    const merged = mergedByKey[mKey] || mergedMatch || null;

    if (!hKey && !merged) {
      const names = [...new Set([
        ...Object.keys(heuristic),
        ...mergedDets.map(d => slugify(d.name)),
      ])].sort().join(", ");
      return this.#text(
        `Detachment not found. Available (${names.split(", ").length}): ${names}`
      );
    }

    const det = heuristic[hKey] || {};
    const title = det.name || (merged && merged.name) || hKey
      || (merged && slugify(merged.name));
    let out = `# ${title}\n\n`;

    // Verified basics (MFM / engine data — L0). Community-maintained points
    // and objective, NOT rule text.
    out += `> **Verified basics (MFM data):** points, objective and enhancements `;
    out += `below are L0 community data, not engine scores.\n`;
    out += `> **Heuristic ratings (interpretation):** rule/strength/disposition `;
    out += `fields are L2 facts (rule = EN mechanical paraphrase, not verbatim GW `;
    out += `text); mechanical detachment modifiers are retired (2026-08-27) — `;
    out += `base ranking stays generalist and rules-free.\n\n`;

    const dp = (merged && merged.dp) || det.dp_cost;
    if (dp) out += `**DP Cost:** ${dp}\n`;
    if (merged && merged.objective) out += `**Objective:** ${merged.objective}\n`;
    if (merged && merged.enhancements && merged.enhancements.length) {
      const enh = merged.enhancements
        .map(e => `${e.name} (${e.points}pts)`)
        .join("; ");
      out += `**Enhancements:** ${enh}\n`;
    }

    // L2 static fact: detachment rule as EN mechanical paraphrase (never
    // verbatim GW rule text — IP). Always carries _source when present.
    const rule = det.rule || {};
    if (rule.text) {
      out += `\n**Rule (paraphrase, ${rule._lang || "en"}):** ${rule.text}\n`;
      if (rule.affects && rule.affects.length) {
        out += `**Affects:** ${rule.affects.join("; ")}\n`;
      }
      if (rule._source && rule._source.length) {
        out += `**Rule source:** ${rule._source.join("; ")}\n`;
      }
    }

    const hFields = [];
    if (det.disposition) hFields.push(`**Disposition:** ${det.disposition}`);
    if (det.strength) hFields.push(`**Strength:** ${det.strength}`);
    if (hFields.length) out += `\n${hFields.join("\n")}\n`;
    if (det.strength_notes) out += `\n**Why:** ${det.strength_notes}\n`;
    if (det.limitations && det.limitations.length) {
      out += `\n**Limitations:**\n${det.limitations.map(l => `- ${l}`).join("\n")}\n`;
    }
    if (det.source) out += `\n**Source:** ${det.source}\n`;

    return this.#text(out);
  }

  // -------- DPP engine ----------------------------------------------------

  // wounds_per_model and model_count are counts: positive whole numbers. The
// engine clamps defensively, but a clamped value and a printed value that
// disagree is a false contract line, so refuse instead.
#validatePool(args) {
    for (const field of ["wounds_per_model", "model_count"]) {
      const v = args[field];
      if (v === undefined || v === null) continue; // defaults to 1 downstream
      if (typeof v !== "number" || !Number.isFinite(v)) {
        return `${field} must be a finite number (got ${JSON.stringify(v)}).`;
      }
      if (!Number.isInteger(v) || v < 1) {
        return `${field} must be a whole number >= 1 — it counts ${
          field === "wounds_per_model" ? "wounds per model" : "models in the unit"
        } (got ${v}). Omit it to use the 1 default.`;
      }
    }
    return null;
  }

  #handleComputeDpp(args) {
    if (!args) {
      return this.#text("Missing arguments.");
    }
    // Validate required fields
    const required = ["attacks", "bs", "strength", "ap", "damage", "target_toughness", "target_save"];
    for (const field of required) {
      if (args[field] === undefined || args[field] === null) {
        return this.#text(`Missing required field: ${field}`);
      }
    }

    // The wound pool drives the damage cap AND the disclosure line. A 0,
    // negative, NaN or fractional value makes the printed "wound pool N"
    // disagree with what the engine actually applied, which is worse than
    // refusing: it is a confidently wrong contract line. Both are counts.
    const poolErr = this.#validatePool(args);
    if (poolErr) return this.#text(poolErr);

    const result = this.#runDppEngine(args);
    if (result.error) {
      return this.#text(`Engine error: ${result.error}`);
    }

    const data = result;
    // Profile line renders from `args` — the values actually handed to the
    // engine — because the engine's return echoes toughness/save but NOT
    // wounds_per_model/model_count. Reading invuln from args also fixes it
    // never being shown: it is absent from the return too.
    const wpm = args.wounds_per_model ?? 1;
    const models = args.model_count ?? 1;
    let out = `# DPP Calculation\n\n`;
    out += `**Weapon:** ${data.weapon}\n`;
    out += `**Target:** T${data.target_toughness} ${data.target_save}+`;
    if (args.target_invuln) out += ` ${args.target_invuln}++`;
    out += ` — ${wpm}W x ${models} model${models === 1 ? "" : "s"}`;
    out += ` (wound pool ${wpm * models})`;
    out += `\n**Condition:** on ${data.conditions?.hit_mode || "normal"}\n\n`;
    out += `| Metric | Value |\n|--------|-------|\n`;
    out += `| Expected Hits | ${data.expected_hits} |\n`;
    out += `| Regular Wounds | ${data.regular_wounds} |\n`;
    out += `| Mortal Wounds | ${data.mortal_wounds} |\n`;
    out += `| **Total Damage** | **${data.total_damage}** |\n`;
    out += `| **Damage Per Point** | **${data.dpp}** |\n`;

    // Attach formula metadata per the LLM boundary contract
    out += `\n---\n`;
    out += `**Formula:** DPP = expected_total_damage / unit_points\n`;
    out += `**Modeled:** Cover = +1BS (worsen), Plunging Fire = -1BS (improve), Torrent=auto-hit, Sustained Hits, Lethal Hits, Devastating Wounds, Twin-Linked, ANTI, Lance, Ignore Cover\n`;
    out += `**Not modeled:** detachment buffs, stratagems, command rerolls, cover modifiers on saves, FNP, melta range\n`;
    out += `**Wound pool cap:** total damage is capped at ${wpm} x ${models} = ${wpm * models}`;
    out +=
      wpm * models > 1
        ? ".\n"
        : " — wounds_per_model/model_count were not passed, so this is a single 1W model. Against multi-wound or multi-model targets, pass the real values or damage is understated.\n";

    return this.#text(out);
  }

  // -------- unit-level DPP (compute_unit_dpp) -----------------------------

  #handleComputeUnitDpp(args) {
    if (!args) return this.#text("Missing arguments.");
    const weapons = args.weapons;
    if (!Array.isArray(weapons) || weapons.length === 0) {
      return this.#text(
        "Missing required field: weapons (a non-empty array of weapon objects)."
      );
    }
    const weaponRequired = ["attacks", "bs", "strength", "ap", "damage"];
    for (let i = 0; i < weapons.length; i++) {
      const w = weapons[i] || {};
      for (const field of weaponRequired) {
        if (w[field] === undefined || w[field] === null) {
          return this.#text(`weapons[${i}] is missing required field: ${field}`);
        }
      }
    }
    for (const field of ["target_toughness", "target_save"]) {
      if (args[field] === undefined || args[field] === null) {
        return this.#text(`Missing required field: ${field}`);
      }
    }
    const poolErr = this.#validatePool(args);
    if (poolErr) return this.#text(poolErr);

    const result = this.#runUnitDppEngine(args);
    if (result.error) {
      return this.#text(`Engine error: ${result.error}`);
    }

    const d = result;
    const wpm = args.wounds_per_model ?? 1;
    const models = args.model_count ?? 1;

    let out = `# Unit DPP Calculation\n\n`;
    out += `**Weapons:** ${weapons.length} | **Target:** T${d.target.toughness} ${
      d.target.save
    }${d.target.invuln ? " INV " + d.target.invuln : ""} \u2014 ${wpm}W x ${models} models (wound pool ${
      wpm * models
    })\n`;
    out += `**Condition:** ${d.hit_mode}\n\n`;
    out += `| Metric | Value |\n|--------|-------|\n`;
    out += `| Unit Points | ${d.unit_points} |\n`;
    out += `| Target Wound Pool | ${d.unit_wounds} |\n`;
    out += `| Damage Before Cap | ${d.uncapped_total_damage} |\n`;
    out += `| **Total Damage (capped)** | **${d.total_damage}** |\n`;
    out += `| **Damage Per Point** | **${d.total_dpp}** |\n`;
    out += `| Overkill Cap Applied | ${d.overkill_capped ? "yes" : "no"} |\n\n`;

    out += `## Per-weapon\n\n`;
    out += `| Weapon | Hits | Reg Wounds | Damage (pre-cap) |\n`;
    out += `|--------|------|------------|------------------|\n`;
    for (const w of d.weapons || []) {
      out += `| ${w.weapon} | ${w.expected_hits} | ${w.regular_wounds} | ${w.total_damage} |\n`;
    }
    out += `\nThe per-weapon column sums to **Damage Before Cap**. The cap is applied once, to the summed total \u2014 a target cannot be dealt more wounds than it has.\n`;

    out += `\n---\n`;
    out += `**Formula:** total_damage = min(sum(per-weapon expected damage), wounds_per_model x model_count); total_dpp = total_damage / unit_points\n`;
    out += `**Modeled:** Cover, Plunging Fire, Torrent, Psychic, Sustained Hits, Lethal Hits, ANTI, Lance, Ignore Cover, Blast, Rapid Fire, Melta, Heavy\n`;
    out += `**Not modeled:** detachment buffs, stratagems, command rerolls, cover on saves, FNP\n`;
    out += `**Wound pool cap:** ${wpm} x ${models} = ${wpm * models}`;
    out +=
      wpm * models > 1
        ? ".\n"
        : " \u2014 wounds_per_model/model_count were not passed, so this is a single 1W model. Pass the real values or damage is understated.\n";

    return this.#text(out);
  }

  // -------- SURV engine ---------------------------------------------------

  #handleComputeSurv(args) {
    if (!args) return this.#text("Missing arguments.");
    const required = ["toughness", "wounds_per_model", "save", "models", "unit_points"];
    for (const f of required) {
      if (args[f] === undefined || args[f] === null)
        return this.#text(`Missing required field: ${f}`);
    }

    const r = this.#runSurvEngine(args);
    if (r.error) return this.#text(`Engine error: ${r.error}`);

    let out = `# Survivability\n\n`;
    out += `**Profile:** T${r.toughness} ${r.wounds_per_model}W ${r.save}`;
    if (r.invuln) out += ` ${r.invuln}`;
    if (r.fnp) out += ` ${r.fnp}`;
    out += ` (${r.models} models, ${r.total_wounds} total wounds)\n\n`;
    out += `| AP Level | Effective Wounds |\n|----------|------------------|\n`;
    out += `| AP 0     | ${r.effective_wounds.ap0} |\n`;
    out += `| AP -2    | ${r.effective_wounds.ap2} |\n`;
    out += `| AP -4    | ${r.effective_wounds.ap4} |\n\n`;
    out += `**Points per effective wound (AP0):** ${r.pts_per_eff_w_ap0}\n\n`;
    out += `---\n`;
    out += `**Formula:** eff_wounds = total_w / (1 - save_prob) × FNP_factor\n`;
    out += `**Interpretation:** Effective wounds = raw damage needed to kill the unit at each AP level.\n`;
    out += `**Not modeled:** to-wound roll (varies by attacker), cover modifiers on target, detachment buffs.\n`;

    return this.#text(out);
  }

  // -------- MOB engine ----------------------------------------------------

  #handleComputeMob(args) {
    if (!args) return this.#text("Missing arguments.");
    if (args.movement === undefined || args.oc === undefined)
      return this.#text("Missing required fields: movement, oc");

    const r = this.#runMobEngine(args);
    if (r.error) return this.#text(`Engine error: ${r.error}`);

    let out = `# Mobility & Utility\n\n`;
    out += `| Metric | Value |\n|--------|-------|\n`;
    out += `| Movement | ${r.movement} |\n`;
    out += `| Fly | ${r.fly} |\n`;
    out += `| Deep Strike | ${r.deep_strike} |\n`;
    out += `| Gate of Infinity | ${r.gate_of_infinity} |\n`;
    out += `| Objective Control | ${r.objective_control} |\n`;
    out += `| Mobility Tier | ${r.mobility_tier} |\n`;
    out += `| Infantry | ${r.is_infantry} |\n`;
    out += `| Vehicle | ${r.is_vehicle} |\n`;
    out += `| Terminator | ${r.is_terminator} |\n`;
    out += `| Character | ${r.is_character} |\n`;
    if (r.transport_capacity) out += `| Transport | ${r.transport_capacity} |\n`;
    out += `\n**Keywords:** ${(r.keywords || []).join(", ") || "none"}\n`;

    return this.#text(out);
  }

  // -------- Faction data helper -------------------------------------------

  #getFactionData(factionKey) {
    const key = (factionKey || this.defaultFaction).toLowerCase();
    const data = this.factions[key];
    if (!data) {
      const available = Object.keys(this.factions).join(", ");
      return { error: `Faction "${key}" not found. Available: ${available}` };
    }
    if (!data.mergedUnits) {
      return { error: `Merged unit data not loaded for "${key}".` };
    }
    return data;
  }

  // -------- List factions -------------------------------------------------

  #handleListFactions() {
    const lines = ["# Available Factions\n"];
    for (const [key, data] of Object.entries(this.factions)) {
      const unitCount = data.mergedUnits?.units?.length || 0;
      const detCount = data.detachmentModifiers ? Object.keys(data.detachmentModifiers.detachments || {}).length : 0;
      const configStatus = data.config ? "yes" : "no";
      lines.push(
        `- **${key}**: ${unitCount} units, ${detCount} detachments (config=${configStatus})`,
      );
    }
    return this.#text(lines.join("\n"));
  }

  // -------- List units ----------------------------------------------------

  #handleListUnits(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);
    const search = (args?.search || "").toLowerCase();
    let out = `# Units (${fd.mergedUnits.units.length} total)\n\n`;
    out += `| Name | Points (from) | Role |\n|------|---------------|------|\n`;
    for (const u of fd.mergedUnits.units) {
      if (search && !u.name.toLowerCase().includes(search)) continue;
      // Smallest entry in the ladder. For a 1-model unit that IS the price; for
      // a multi-model squad it is the smallest model's cost, which is why the
      // column says "from". get_unit serves the full ladder.
      const pricing = u.pricing?.[0]?.costs?.[0]?.points || "-";
      out += `| ${u.name} | ${pricing} | ${u.role || ""} |\n`;
    }
    return this.#text(out);
  }

  // -------- Get unit ------------------------------------------------------

  #handleGetUnit(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);

    // Fail closed. This used to fall through to `includes("")`, which is true
    // for every unit — so `{}` or a wrong parameter name returned the first
    // roster entry as a confident, well-formatted answer. For an agent that
    // trusts tool output, a plausible wrong unit is the worst failure mode in
    // the stack.
    const raw = (args?.name ?? "").toString().trim();
    if (!raw) {
      let hint = `Missing required parameter: name.`;
      if (args?.unit) {
        hint += `\nYou passed "unit" — the parameter is "name".`;
      }
      return this.#text(
        `${hint}\nAn empty name would otherwise match the first unit in the roster. ` +
          `Use list_units (faction: "${args?.faction || "?"}") to see valid names.`,
      );
    }

    const query = raw.toLowerCase();
    const units = fd.mergedUnits.units;
    const exact = units.find((u) => u.name.toLowerCase() === query);
    const matches = exact
      ? [exact]
      : units.filter((u) => u.name.toLowerCase().includes(query));

    if (matches.length === 0) {
      return this.#text(
        `No unit in "${args?.faction || "?"}" matches "${raw}".\n` +
          `Use list_units to see valid names.`,
      );
    }
    if (matches.length > 1) {
      // Partial match is ambiguous. Say so rather than picking one and letting
      // the caller believe it asked for that unit.
      return this.#text(
        `"${raw}" matches ${matches.length} units in "${args?.faction || "?"}". ` +
          `Re-query with the full name:\n` +
          matches
            .slice(0, 12)
            .map((u) => `- ${u.name}`)
            .join("\n"),
      );
    }
    const unit = matches[0];

    const prof = unit.profile || {};
    // pricing[0].costs is a LADDER: costs[0] is the smallest model count, not
    // the squad. Quoting it alone understated a 5-model Paladin Squad as the
    // 4-model price (170, not 215).
    const ladder = (unit.pricing?.[0]?.costs || []).filter(
      (c) => c && c.points !== undefined,
    );
    const base = ladder[0];
    const headline = base
      ? `${base.points} pts @ ${base.models} model${base.models === 1 ? "" : "s"}`
      : "?";
    let out = `# ${unit.name} (${headline})\n\n`;
    if (ladder.length > 1) {
      out += `**Points ladder:** ${ladder
        .map((c) => `${c.points} @ ${c.models}`)
        .join(", ")}\n\n`;
    }
    out += `**Role:** ${unit.role || "N/A"}\n\n`;
    if (prof.keywords) {
      out += `**Keywords:** ${
        Array.isArray(prof.keywords) ? prof.keywords.join(", ") : prof.keywords
      }\n\n`;
    }
    if (prof.stats) {
      const s = prof.stats;
      // merged stores the save as `Sv`, not `SV` — the old `s.SV` read missed
      // every time and printed SV=? for every unit in the game. InSv (the
      // defensive stat DPP questions turn on) was never rendered at all.
      const sv = s.Sv ?? s.SV ?? "?";
      out += `**Stats:** M=${s.M || "?"} T=${s.T || "?"} SV=${sv} W=${s.W || "?"} LD=${s.LD || "?"} OC=${s.OC || "?"}`;
      if (s.InSv) out += ` INV=${s.InSv}`;
      out += `\n\n`;
    }

    if (prof.weapons?.length) {
      out += `## Weapons\n\n`;
      out += `| Name | A | BS | S | AP | D | Abilities |\n`;
      out += `|------|---|---|---|---|---|-----------|\n`;
      for (const w of prof.weapons) {
        const s = w.profiles?.[0]?.stats || {};
        out += `| ${w.name} | ${s.A || "-"} | ${s.BS || s.WS || "-"} | ${s.S || "-"} | ${s.AP || "-"} | ${s.D || "-"} | ${s.Keywords || ""} |\n`;
      }
    }
    if (prof.abilities?.length) {
      out += `\n## Abilities\n\n`;
      for (const a of prof.abilities) {
        // merged/ stores abilities as {name, <derived field>}; any description
        // was verbatim rule text and is dropped at merge time, so only the
        // machine-readable name is served. Previously `- ${a}` stringified these
        // to "[object Object]".
        out += `- ${typeof a === "string" ? a : a?.name || "?"}\n`;
      }
    }
    return this.#text(out);
  }

  // -------- Rank units ----------------------------------------------------

  #handleRankUnits(args) {
    if (!args) return this.#text("Missing arguments.");

    const result = this.#runRankEngine(args);
    if (result.error) {
      return this.#text(`Ranking error: ${result.error}`);
    }

    const data = result;
    if (!Array.isArray(data)) {
      if (data.error) return this.#text(`Ranking error: ${data.error}`);
      return this.#text(`Unexpected result: ${JSON.stringify(data)}`);
    }

    if (data.length === 0) {
      return this.#text("No ranking results returned.");
    }

    const faction = args.faction || "grey-knights";
    const target = args.target || "MEQ";
    const mission = args.mission || "none";
    const tier = args.tier || "1st";
    const det = args.detachment || "";

    let out = `# Unit Ranking — ${faction} vs ${target}`;
    if (mission !== "none") out += ` (Mission: ${mission})`;
    if (det) out += ` [Detachment: ${det}]`;
    out += `\nTier: ${tier}\n\n`;

    // Table header
    let hasMissionScore = false;
    for (const r of data) {
      if (r.mission_score !== undefined) { hasMissionScore = true; break; }
    }

    if (hasMissionScore) {
      out += `| # | Unit | Pts | DPP | Dmg | Surv(AP0) | Mob | Score |\n`;
      out += `|---|------|-----|-----|-----|-----------|-----|-------|\n`;
      for (let i = 0; i < data.length; i++) {
        const r = data[i];
        out += `| ${i + 1} | ${r.name} | ${r.points} | ${r.dpp.toFixed(4)} | ${r.total_damage.toFixed(2)} | ${r.surv_ew_ap0} | ${r.mob_tier} | ${r.mission_score?.toFixed(0) || "-"} |\n`;
      }
    } else {
      out += `| # | Unit | Pts | DPP | Dmg | Surv(AP0) | Mob Tier |\n`;
      out += `|---|------|-----|-----|-----|-----------|----------|\n`;
      for (let i = 0; i < data.length; i++) {
        const r = data[i];
        out += `| ${i + 1} | ${r.name} | ${r.points} | ${r.dpp.toFixed(4)} | ${r.total_damage.toFixed(2)} | ${r.surv_ew_ap0} | ${r.mob_tier} |\n`;
      }
    }

    out += `\n---\n`;
    out += `**Context:** target=${target}, mission=${mission || "none"}, tier=${tier}, detachment=${det || "none"}\n`;
    out += `**Formula:** DPP = total_damage / points. SURV = effective wound pool at AP0/AP2/AP4. MOB = mobility tier (static/slow/standard/cavalry/fast/very_fast/skyborne).\n`;
    out += `**Limitation:** Does not model stratagems, command rerolls, or conditional buffs beyond selected detachment modifier.\n`;

    return this.#text(out);
  }

  // -------- Get findings (pre-computed pipeline output) -------------------

  #handleGetFindings(args) {
    const faction = (args?.faction || "").toLowerCase().trim();
    if (!faction) {
      return this.#text("Missing required parameter: faction");
    }

    // Path traversal guard
    if (!/^[a-z0-9-]+$/.test(faction)) {
      return this.#text(`Invalid faction key "${faction}".`);
    }

    // Read the JSON sidecar, not the report. This used to regex a
    // `const DATA = {...}` blob out of findings.html, which coupled a data
    // tool to the presentation's markup and broke on any restyle. gen_findings_html.py
    // writes the same payload to findings/<fid>/data.json.
    const dataPath = join(FINDINGS_DIR, faction, "data.json");
    if (!existsSync(dataPath)) {
      let available = [];
      try {
        const dirs = readdirSync(FINDINGS_DIR, { withFileTypes: true })
          .filter(d => d.isDirectory() && !d.name.startsWith("_"));
        for (const d of dirs) {
          if (existsSync(join(FINDINGS_DIR, d.name, "data.json"))) {
            available.push(d.name);
          }
        }
      } catch { /* ignore */ }

      if (available.length === 0) {
        return this.#text(
          `No findings sidecars found (findings/*/data.json). Regenerate with:\n` +
            `  python3 scripts/gen_findings_html.py --all`,
        );
      }
      return this.#text(
        `No findings for faction "${faction}".\n\n` +
          `Factions with findings: ${available.join(", ")}\n\n` +
          `If "${faction}" has a findings.html but no data.json, the sidecar is from an older generator run — regenerate with:\n` +
          `  python3 scripts/gen_findings_html.py --all`,
      );
    }

    let data;
    try {
      data = JSON.parse(readFileSync(dataPath, "utf-8"));
    } catch {
      return this.#text(`Failed to parse findings data for "${faction}" — data.json is not valid JSON.`);
    }

    if (!data || !data.meta) {
      return this.#text(`Findings sidecar for "${faction}" is malformed (no meta key).`);
    }

    // Default to first meta (competitive) unless specified
    const metaSlug = args?.meta || Object.keys(data.meta)[0];
    const metaData = data.meta[metaSlug];
    if (!metaData) {
      return this.#text(`Meta "${metaSlug}" not found. Available: ${Object.keys(data.meta).join(", ")}`);
    }

    const allMissions = Object.keys(metaData);
    const missionFilter = args?.mission;
    const missions = missionFilter
      ? allMissions.filter(m => m.toLowerCase() === missionFilter.toLowerCase())
      : allMissions;

    if (missionFilter && missions.length === 0) {
      return this.#text(
        `Mission "${missionFilter}" not found.\nAvailable: ${allMissions.join(", ")}`
      );
    }

    const topN = (args?.top_n !== undefined && args?.top_n !== null)
      ? Math.floor(args.top_n)
      : 10;

    let out = `# Findings: ${faction} (${metaSlug})\n\n`;
    out += `*Source: findings/${faction}/data.json - pre-computed with penalties (FLYCOST, OC0, etc.).*\n\n`;

    for (const mission of missions) {
      const units = metaData[mission];
      if (!Array.isArray(units) || units.length === 0) {
        out += `## ${mission}\n\nNo units found.\n\n`;
        continue;
      }

      const shown = topN > 0 ? units.slice(0, topN) : units;

      out += `## ${mission} (${units.length} units${topN > 0 && units.length > topN ? `, showing top ${topN}` : ""})\n\n`;
      out += `| # | Unit | Pts | Score | DPP | DPP% | SURV | OBJ% | MOB% | Tags |\n`;
      out += `|---|------|-----|-------|-----|------|------|------|------|------|\n`;

      for (let i = 0; i < shown.length; i++) {
        const u = shown[i];
        const tags = [];
        if (u.ds) tags.push("DS");
        if (u.fly) tags.push("FLY");
        if (u.inv) tags.push(`INV${u.inv}`);
        if (u.fnp) tags.push(`FNP${u.fnp}`);
        if (u.oc === 0) tags.push("OC0");
        if (u.cost_eff !== null && u.cost_eff !== undefined) tags.push(`COST${u.cost_eff}`);

        out += `| ${i + 1} | ${u.name} | ${u.pts} | ${u.score} | ${u.dpp} | ${u.dpp_pct}% | ${u.surv_turns}t | ${u.obj_pct}% | ${u.mob_pct}% | ${tags.join(" ")} |\n`;
      }
      out += `\n`;
    }

    out += `---\n`;
    out += `**Formula:** Score = DPP${allMissions.length > 0 ? '×' : ''} + SURV + OBJ + MOB weighted by mission.\n`;
    out += `**Penalties applied:** FLYCOST (aircraft OC0), cost efficiency, objective penalty for OC0 units.\n`;
    out += `**Not modeled:** detachment buffs, stratagems, command rerolls.\n`;

    return this.#text(out);
  }

  // -------- Army-level indices (findings/advisor.json, army_tiers.json) ---

  #advisorByFid() {
    const a = this.#loadJson(ADVISOR_FILE);
    if (!a || !Array.isArray(a.factions)) return null;
    return new Map(a.factions.map((f) => [f.fid, f]));
  }

  #handleGetArmyIndex(args) {
    const advisor = this.#loadJson(ADVISOR_FILE);
    if (!advisor || !Array.isArray(advisor.factions) || advisor.factions.length === 0) {
      return this.#text(
        `advisor.json not found or empty at ${ADVISOR_FILE}. Regenerate with:\n` +
          `  python3 scripts/army_advisor.py --guide`,
      );
    }

    const rows = [...advisor.factions].sort(
      (a, b) => (b.overall_index ?? 0) - (a.overall_index ?? 0),
    );
    const wanted = (args?.faction || "").toLowerCase().trim();

    let out;
    if (wanted) {
      const row = rows.find((f) => f.fid === wanted);
      if (!row) {
        return this.#text(
          `No advisor entry for "${wanted}". Rated factions: ${rows
            .map((f) => f.fid)
            .join(", ")}`,
        );
      }
      out = `# Army Index: ${row.name}\n\n`;
      out += `| Field | Value |\n|-------|-------|\n`;
      out += `| Overall index | ${row.overall_index} |\n`;
      out += `| Ceiling | ${row.ceiling} |\n`;
      out += `| Floor | ${row.floor} |\n`;
      out += `| Versatility | ${row.versatility} |\n`;
      out += `| Roster depth | ${row.roster_depth} |\n`;
      out += `| Best disposition | ${row.best_disposition} |\n`;
      out += `| Worst disposition | ${row.worst_disposition} |\n`;
      out += `| Points churn | ${row.points_churn} |\n`;
      out += `| First-army fit | ${row.first_army_fit}${
        row.first_army_fit_why ? ` — ${row.first_army_fit_why}` : ""
      }\n`;
      out += `| Meta ceiling | ${
        row.meta_ceiling ?? "not computed"
      }${row.meta_ceiling_best_detachment ? ` (${row.meta_ceiling_best_detachment})` : ""} |\n`;
    } else {
      const limit = args?.limit ? Math.floor(args.limit) : 30;
      out = `# Army Index — all rated factions\n\n`;
      out += `Ranked by overall_index. ${rows.length} factions rated.\n\n`;
      out += `| # | Faction | Index | Ceiling | Floor | Vers | Depth | First army |\n`;
      out += `|---|---------|-------|---------|-------|------|-------|-------------|\n`;
      rows.slice(0, limit).forEach((f, i) => {
        out += `| ${i + 1} | ${f.name} | ${f.overall_index} | ${f.ceiling} | ${f.floor} | ${f.versatility} | ${f.roster_depth} | ${f.first_army_fit} |\n`;
      });
    }

    // Contract block. The row mixes engine output with expert judgement, so
    // the split has to travel with the numbers or an LLM reads first_army_fit
    // as an engine fact.
    out += `\n---\n`;
    out += `**Generated:** ${advisor.generated} (from findings/advisor.json)\n`;
    out += `**Formula:** overall_index = ${advisor._formula?.overall_index ?? "unrecorded"}\n`;
    out += `**unit_score:** ${advisor._formula?.unit_score ?? "unrecorded"}\n`;
    out += `**Not modeled:**\n`;
    for (const n of advisor._formula?.not_modeled ?? []) out += `- ${n}\n`;

    return this.#text(out);
  }

  #handleCompareFactions(args) {
    const list = Array.isArray(args?.factions) ? args.factions : [];
    if (list.length < 2) {
      return this.#text(`Provide 2-5 factions in "factions" to compare.`);
    }
    if (list.length > 5) {
      return this.#text(`Too many factions (${list.length}). Compare 2-5 at a time.`);
    }
    const fids = list.map((f) => String(f).toLowerCase().trim());
    for (const f of fids) {
      if (!/^[a-z0-9-]+$/.test(f)) return this.#text(`Invalid faction key "${f}".`);
    }

    const tiers = this.#loadJson(TIERS_FILE);
    const advisor = this.#advisorByFid();
    if (!tiers) {
      return this.#text(
        `army_tiers.json not found at ${TIERS_FILE}. Regenerate with:\n` +
          `  python3 scripts/gen_findings_html.py --all`,
      );
    }

    const cols = MISSIONS.concat(["overall"]);
    let out = `# Comparison\n\n`;
    out += `**army_tiers.json — rules-free generalist index**\n\n`;
    out += `| Faction | ${cols.join(" | ")} |\n`;
    out += `|---------|${cols.map(() => "-------").join("|")}|\n`;
    for (const fid of fids) {
      const t = tiers[fid];
      // fid is rendered alongside the display name so a caller can chain this
      // result straight into get_findings/get_army_index without re-guessing
      // the slug.
      if (!t) {
        out += `| ${fid} |`;
        out += `${cols.map(() => "_not rated_").join(" | ")} |\n`;
        continue;
      }
      const cells = cols.map((m) =>
        m === "overall" ? t.overall : (t.missions?.[m] ?? "—"),
      );
      out += `| ${t.name ?? fid} \`${fid}\` (${t.n_units} units) | ${cells.join(" | ")} |\n`;
    }

    const rated = fids.map((f) => advisor?.get(f)).filter(Boolean);
    if (rated.length > 0) {
      out += `\n**advisor.json — rules-aware**\n\n`;
      out += `| Faction | Index | Ceiling | Floor | Vers | Meta ceiling | First army |\n`;
      out += `|---------|-------|---------|-------|------|--------------|-------------|\n`;
      for (const r of rated) {
        out += `| ${r.name} \`${r.fid}\` | ${r.overall_index} | ${r.ceiling} | ${r.floor} | ${r.versatility} | ${r.meta_ceiling ?? "not computed"} | ${r.first_army_fit} |\n`;
      }
    } else {
      out += `\n_Advisor: no rated entry for any of these factions._\n`;
    }

    out += `\n---\n`;
    out += `The two tables rank differently on purpose. army_tiers is rules-free and generalist; advisor applies the rules-aware rating from resources/experts. A faction that climbs between them is being lifted by army rules, not statlines.\n`;
    out += `**Not modeled:** see get_army_index for advisor.json's full not-modeled list.\n`;
    return this.#text(out);
  }

  #handleGetFactionTiers(args) {
    const tiers = this.#loadJson(TIERS_FILE);
    if (!tiers) {
      return this.#text(
        `army_tiers.json not found at ${TIERS_FILE}. Regenerate with:\n` +
          `  python3 scripts/gen_findings_html.py --all`,
      );
    }

    const mission = args?.mission || "overall";
    const valid = MISSIONS.concat(["overall"]);
    if (!valid.includes(mission)) {
      return this.#text(
        `Unknown mission "${mission}". Valid: ${valid.join(", ")}`,
      );
    }

    const topN = args?.top_n !== undefined ? Math.floor(args.top_n) : 10;
    const pick = (t) =>
      mission === "overall" ? t.overall : (t.missions?.[mission] ?? null);

    const rows = Object.entries(tiers)
      .map(([fid, t]) => ({ fid, t, v: pick(t) }))
      .filter((r) => r.v !== null && r.v !== undefined)
      .sort((a, b) => b.v - a.v);

    let out = `# Faction tiers by ${mission}\n\n`;
    out += `${rows.length} factions scored.\n\n`;
    out += `| # | Faction | ${mission} | Units |\n`;
    out += `|---|---------|${"-".repeat(mission.length + 2)}|-------|\n`;
    const shown = topN > 0 ? rows.slice(0, topN) : rows;
    shown.forEach((r, i) => {
      out += `| ${i + 1} | ${r.t.name ?? r.fid} | ${r.v} | ${r.t.n_units ?? "—"} |\n`;
    });

    out += `\n---\n`;
    out += `**Source:** findings/army_tiers.json (engine mission scores).\n`;
    out += `**Formula:** mission score = DPP/SURV/OBJ/MOB composite weighted per mission.\n`;
    out += `**Not modeled:** detachment buffs, stratagems, command rerolls, rules-aware adjustment. Use get_army_index for the rules-aware view.\n`;
    return this.#text(out);
  }

  #handleListFindingsTopics(args) {
    const wanted = (args?.faction || "").toLowerCase().trim();
    if (wanted && !/^[a-z0-9-]+$/.test(wanted)) {
      return this.#text(`Invalid faction key "${wanted}".`);
    }
    if (!existsSync(FINDINGS_DIR)) {
      return this.#text(`findings/ not found at ${FINDINGS_DIR}.`);
    }

    let dirs;
    try {
      dirs = readdirSync(FINDINGS_DIR, { withFileTypes: true })
        .filter((d) => d.isDirectory() && !d.name.startsWith("_"))
        .map((d) => d.name)
        .sort();
    } catch {
      return this.#text(`Could not read ${FINDINGS_DIR}.`);
    }
    if (wanted) dirs = dirs.filter((d) => d === wanted);

    let out = `# Findings reports\n\n`;
    if (dirs.length === 0) {
      return this.#text(
        wanted
          ? `No findings directory for "${wanted}".`
          : `No findings directories found.`,
      );
    }

    let total = 0;
    for (const d of dirs) {
      let topics = [];
      try {
        topics = readdirSync(join(FINDINGS_DIR, d))
          .filter((f) => f.endsWith(".html"))
          .sort();
      } catch {
        continue;
      }
      if (topics.length === 0) continue;
      total += topics.length;
      const extra = topics.filter((t) => t !== "findings.html");
      out += `**${d}** — ${topics.join(", ")}`;
      if (extra.length > 0) out += ` _(extra: ${extra.join(", ")})_`;
      out += `\n`;
    }

    out += `\n${total} reports across ${dirs.length} factions.\n`;
    out += `---\n`;
    out += `Filenames only. This tool summarises nothing — no numeric claim may be sourced from it. Use get_findings for the per-unit competition table, get_army_index for the meta indices.\n`;
    return this.#text(out);
  }

  // -------- Stratagem lookup ----------------------------------------------

  #handleGetStratagem(args) {
    const query = (args?.name || "").toUpperCase().trim();

    // Core stratagems — hardcoded 11e basics
    const CORE_STRATAGEMS = [
      { name: "BATTLE SHOCK STRATAGEM", cp: 1, desc: "Used when a unit below Starting Strength fails Battle-shock test. Unit passes instead." },
      { name: "COMMAND REROLL", cp: 1, desc: "Re-roll a single Hit roll, Wound roll, Damage roll, Saving throw, Advance roll, Charge roll, or Hazardous test." },
      { name: "INSPIRED LEADERSHIP", cp: 1, desc: "Used in your Command phase. One VEHICLE or MONSTER unit within 6\" of a Leader is Battleshock immune until your next Command phase." },
    ];

    const results = [];

    for (const s of CORE_STRATAGEMS) {
      if (s.name.toUpperCase().includes(query) || query.includes(s.name.toUpperCase())) {
        results.push({ source: "Core (11e)", ...s });
      }
    }

    if (results.length === 0) {
      return this.#text(`Stratagem "${query}" not found.\n\nCore stratagems available: Command Reroll, Battle Shock Stratagem, Inspired Leadership.\n\nNote: Full stratagem text requires GW faction pack PDFs (not yet parsed). For faction-specific stratagems, see the L2 rule/strength facts via get_detachment.`);
    }

    let out = "";
    for (const s of results) {
      out += `## ${s.name} [${s.source}]\n`;
      out += `CP: ${s.cp}\n`;
      out += `${s.desc}\n\n`;
    }
    return this.#text(out);
  }

  // -------------------------------------------------------------------------
  // Transport helpers
  // -------------------------------------------------------------------------

  #text(text) {
    return { content: [{ type: "text", text }] };
  }

  // -------------------------------------------------------------------------
  // Server runners
  // -------------------------------------------------------------------------

  async runStdio() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("turtleatlas-w40k-11e MCP server running on stdio");
  }

  async runHttp(port) {
    const app = express();
    app.use(express.json());

    app.get("/health", (_req, res) =>
      res.json({ status: "healthy", service: "turtleatlas-w40k-11e" }),
    );

    const transports = {};

    app.post("/mcp", async (req, res) => {
      const sessionId = req.headers["mcp-session-id"];
      let transport;

      if (sessionId && transports[sessionId]) {
        transport = transports[sessionId];
      } else if (!sessionId && isInitializeRequest(req.body)) {
        const t = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (id) => {
            transports[id] = t;
          },
        });
        t.onclose = () => {
          const sid = t.sessionId;
          if (sid) delete transports[sid];
        };
        transport = t;

        const httpServer = new Server(
          { name: "turtleatlas-w40k-11e", version: "1.0.0" },
          { capabilities: { tools: {} } },
        );
        this.#setupToolHandlers(httpServer);
        await httpServer.connect(transport);
        await transport.handleRequest(req, res, req.body);
        return;
      } else {
        res.status(400).json({
          jsonrpc: "2.0",
          error: { code: -32000, message: "Bad Request" },
          id: null,
        });
        return;
      }

      await transport.handleRequest(req, res, req.body);
    });

    app.listen(port, "0.0.0.0", () =>
      console.error(`turtleatlas-w40k-11e MCP server on http://0.0.0.0:${port}/mcp`),
    );
  }

  async run() {
    const portArg = process.argv.find((a) => a.startsWith("--port="));
    const port = portArg
      ? parseInt(portArg.split("=")[1], 10)
      : process.env.MCP_PORT
        ? parseInt(process.env.MCP_PORT, 10)
        : null;
    if (port) await this.runHttp(port);
    else await this.runStdio();
  }
}

// ---------------------------------------------------------------------------
// Entry
// ---------------------------------------------------------------------------

const instance = new TurtleAtlasW40kServer();
instance.run().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
