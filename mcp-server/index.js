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

    // 2. Load config files (detachment_modifiers.json, supported.json) into matching factions
    try {
      const configDirs = readdirSync(CONFIG_DIR, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith("_"))
        .map(d => d.name);

      for (const dir of configDirs) {
        const detPath = join(CONFIG_DIR, dir, "detachment_modifiers.json");
        const supPath = join(CONFIG_DIR, dir, "supported.json");

        if (!factions[dir]) factions[dir] = { mergedUnits: null, config: null, detachmentModifiers: null };

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
import sys, json
sys.path.insert(0, ${JSON.stringify(BASE_DIR)})
from engine.dpp import compute_weapon_dpp, WeaponProfile, TargetProfile, HitMode, WeaponModifier

a = json.loads(sys.stdin.read())

wp = WeaponProfile(
    name=a.get("weapon_name", "Custom"),
    attacks=a["attacks"],
    bs=a["bs"],
    strength=a["strength"],
    ap=a["ap"],
    damage=a["damage"],
    abilities=[x.strip() for x in a.get("abilities", "").split(",") if x.strip()],
)
target = TargetProfile(
    toughness=a["target_toughness"],
    save=a["target_save"],
    invuln=a.get("target_invuln"),
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
            "Get detachment engine-modeled modifiers (DPP/SURV buffs) for a named detachment. Reads from config files.",
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
          name: "compute_dpp",
          description:
            "Compute expected damage per point for a weapon profile vs a target. Supports 11e Cover (worsens BS) and Plunging Fire. MANDATORY: You MUST call this tool for all DPP values. NEVER compute, derive, estimate, or fabricate DPP numbers yourself — the engine applies the 11e wound table, Cover, Plunging Fire, abilities, and target profiles. Only this tool's output is authoritative. Violation produces unreliable results.",
          inputSchema: {
            type: "object",
            properties: {
              weapon_name: { type: "string", description: "Weapon name label" },
              attacks: {
                type: "number",
                description: "Number of attacks",
              },
              bs: {
                type: "number",
                description: "Ballistic Skill (e.g. 3 for 3+)",
              },
              strength: { type: "number", description: "Strength" },
              ap: {
                type: "number",
                description: "Armor Penetration (e.g. -1)",
              },
              damage: { type: "number", description: "Damage per wound" },
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
              transport_capacity: { type: "string", description: "Transport capacity (e.g. '6 INFANTRY')" },
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
      ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      switch (name) {
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

  #handleGetDetachment(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);
    if (!fd.detachmentModifiers) {
      return this.#text(`No detachment config data for "${args?.faction || this.defaultFaction}".`);
    }
    const query = (args?.name || "").toUpperCase().trim();
    const detachments = fd.detachmentModifiers.detachments || {};

    // Find matching detachment
    const detKey = Object.keys(detachments).find(k =>
      k.toUpperCase().includes(query) || query.includes(k.toUpperCase())
    );
    if (!detKey) {
      const names = Object.keys(detachments).join(", ");
      return this.#text(`Detachment not found. Available: ${names}`);
    }

    const det = detachments[detKey];
    let out = `# ${detKey}\n\n`;
    out += `**DP Cost:** ${det.dp_cost || "?"}\n`;
    if (det._source) out += `**Source:** ${det._source}\n`;
    if (det._engine_note) out += `\n> ${det._engine_note}\n`;

    out += `\n## Engine-Modeled Modifiers\n`;
    const choices = det.choices || [];
    if (choices.length === 0) {
      out += `No engine-modeled modifiers (rules too complex for DPP computation).\n`;
    } else {
      for (const c of choices) {
        out += `\n### ${c.name}\n`;
        if (c.description) out += `${c.description}\n`;
        if (c.condition) out += `Condition: ${c.condition}\n`;
        out += `Affects: ${c.affects || "?"}\n`;
        // Show numeric modifiers
        const mods = [];
        if (c.reroll_hits) mods.push(`Re-roll hits: ${c.reroll_hits}`);
        if (c.reroll_wounds) mods.push(`Re-roll wounds: ${c.reroll_wounds}`);
        if (c.hit_modifier) mods.push(`Hit modifier: ${c.hit_modifier > 0 ? "+" : ""}${c.hit_modifier}`);
        if (c.plus1_to_wound) mods.push("+1 to wound");
        if (c.sustained_hits_extra) mods.push(`Extra Sustained Hits: +${c.sustained_hits_extra}`);
        if (c.lethal_hits) mods.push("Lethal Hits");
        if (c.movement_bonus) mods.push(`Movement: +${c.movement_bonus}"`);
        if (c.invulnerable_save) mods.push(`Invulnerable: ${c.invulnerable_save}+`);
        if (c.feel_no_pain) mods.push(`FNP: ${c.feel_no_pain}+`);
        if (mods.length > 0) out += `Modifiers: ${mods.join(", ")}\n`;
        if (c.unit_filter) out += `Applies to: ${c.unit_filter.join(", ")}\n`;
        if (c._engine_note) out += `> ${c._engine_note}\n`;
        out += `\n`;
      }
    }

    return this.#text(out);
  }

  // -------- DPP engine ----------------------------------------------------

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

    const result = this.#runDppEngine(args);
    if (result.error) {
      return this.#text(`Engine error: ${result.error}`);
    }

    const data = result;
    let out = `# DPP Calculation\n\n`;
    out += `**Weapon:** ${data.weapon}\n`;
    out += `**Target:** T${data.target_toughness} ${data.target_save}+`;
    out += data.target_invuln ? ` ${data.target_invuln}++` : "";
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
    out += `| Name | Points | Role |\n|------|--------|------|\n`;
    for (const u of fd.mergedUnits.units) {
      if (search && !u.name.toLowerCase().includes(search)) continue;
      const pricing = u.pricing?.[0]?.costs?.[0]?.points || "-";
      out += `| ${u.name} | ${pricing} | ${u.role || ""} |\n`;
    }
    return this.#text(out);
  }

  // -------- Get unit ------------------------------------------------------

  #handleGetUnit(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);
    const query = (args?.name || "").toLowerCase();
    const unit = fd.mergedUnits.units.find((u) =>
      u.name.toLowerCase().includes(query),
    );
    if (!unit) {
      return this.#text(`Unit not found matching "${query}".`);
    }
    const prof = unit.profile || {};
    const pricing = unit.pricing?.[0]?.costs?.[0]?.points || "?";
    let out = `# ${unit.name} (${pricing} pts)\n\n`;
    out += `**Role:** ${unit.role || "N/A"}\n\n`;
    if (prof.keywords) {
      out += `**Keywords:** ${
        Array.isArray(prof.keywords) ? prof.keywords.join(", ") : prof.keywords
      }\n\n`;
    }
    if (prof.stats) {
      const s = prof.stats;
      out += `**Stats:** M=${s.M || "?"} T=${s.T || "?"} SV=${s.SV || "?"} W=${s.W || "?"} LD=${s.LD || "?"} OC=${s.OC || "?"}\n\n`;
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
        out += `- ${a}\n`;
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
      return this.#text(`Stratagem "${query}" not found.\n\nCore stratagems available: Command Reroll, Battle Shock Stratagem, Inspired Leadership.\n\nNote: Full stratagem text requires GW faction pack PDFs (not yet parsed). For faction-specific stratagems, see the detachment modifiers via get_detachment.`);
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
