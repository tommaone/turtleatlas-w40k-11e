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
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const BASE_DIR = join(__dirname, "..");
const DATA_DIR = join(BASE_DIR, "data");

class TurtleAtlasW40kServer {
  constructor() {
    // Load data at startup (best-effort)
    this.coreRules = this.#loadJson("core-rules-11e.json");

    // Per-faction data
    this.factions = {
      "grey-knights": {
        factionPack: this.#loadJson("grey-knights-faction-pack.json"),
        mergedUnits: this.#loadJson("merged/grey-knights.json"),
      },
      "chaos-knights": {
        factionPack: this.#loadJson("chaos-knights-faction-pack.json"),
        mergedUnits: this.#loadJson("merged/chaos-knights.json"),
      },
    };
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

  #loadJson(filename) {
    try {
      const path = join(DATA_DIR, filename);
      if (!existsSync(path)) return null;
      return JSON.parse(readFileSync(path, "utf8"));
    } catch (err) {
      console.error(`Failed to load ${filename}: ${err.message}`);
      return null;
    }
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
            "Get 11e core rules overview: abilities, phases, stratagems, cover.",
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
            "Look up a core ability by name (case-insensitive). E.g. SUSTAINED HITS, LETHAL HITS, COVER, PLUNGING FIRE.",
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
            "Get detachment rules, enhancements, and stratagems for a named detachment.",
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
            "Compute expected damage per point for a weapon profile vs a target. Supports 11e Cover (worsens BS) and Plunging Fire.",
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
            "Look up a core or detachment stratagem by name.",
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
            "Compute survivability metrics for a unit: effective wound pool at AP0/AP2/AP4, and points-per-effective-wound efficiency.",
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
            "Compute mobility and utility profile for a unit: movement, Fly, Deep Strike, OC, keywords, mobility tier.",
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
        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${name}`,
          );
      }
    });
  }

  // -------- Core rules ----------------------------------------------------

  #handleGetCoreRules(args) {
    const lines = [];
    const section = (args?.section || "all").toLowerCase();

    if (!this.coreRules) {
      return this.#text("Core rules data not loaded. Run parser first.");
    }

    if (section === "abilities" || section === "all") {
      lines.push(`# Core Abilities (${this.coreRules.abilities.length} total)`);
      for (const a of this.coreRules.abilities) {
        lines.push(`\n## ${a.name} [${a.ref}]`);
        if (a.form) lines.push(`Form: ${a.form}`);
        lines.push(a.description);
      }
    }

    if (section === "stratagems" || section === "all") {
      lines.push(
        `\n# Core Stratagems (${this.coreRules.stratagems.length} total)`,
      );
      for (const s of this.coreRules.stratagems) {
        lines.push(`\n## ${s.name} [${s.ref}]`);
        if (s.cp_cost) lines.push(`CP: ${s.cp_cost}`);
      }
    }

    if (section === "phases" || section === "all") {
      lines.push(`\n# Phases`);
      for (const [key, val] of Object.entries(this.coreRules.phases || {})) {
        lines.push(`\n## ${key.replace(/_/g, " ").toUpperCase()} (${val.ref})`);
        for (const step of val.steps || []) {
          lines.push(`- [${step.ref}] ${step.name}`);
        }
      }
    }

    if (section === "cover" || section === "all") {
      const cr = this.coreRules.cover_rules || {};
      lines.push(`\n# Cover Rules (11th Edition)`);
      lines.push(
        `\n## How Cover Works\nIn 11e, Cover does NOT modify saves. Instead, it worsens the attacker's BS by 1.`,
      );
      if (cr.benefit_of_cover)
        lines.push(`\n**Benefit of Cover:** ${cr.benefit_of_cover}`);
      if (cr.cover_modifier)
        lines.push(`\n**Modifier:** ${cr.cover_modifier}`);
      if (cr.plunging_fire)
        lines.push(`\n**Plunging Fire:** ${cr.plunging_fire}`);
      if (cr.ignores_cover)
        lines.push(`\n**Ignores Cover:** ${cr.ignores_cover}`);
    }

    return this.#text(lines.join("\n"));
  }

  // -------- Ability lookup ------------------------------------------------

  #handleGetAbility(args) {
    if (!this.coreRules) {
      return this.#text("Rules not loaded.");
    }
    const query = (args?.name || "").toUpperCase().trim();
    const idx = this.coreRules.abilities_index || {};
    const match =
      idx[query] ||
      Object.values(idx).find(
        (a) => a.name.includes(query) || query.includes(a.name),
      );
    if (!match) {
      const allNames = this.coreRules.abilities.map((a) => a.name).join(", ");
      return this.#text(`Ability not found. Available: ${allNames}`);
    }
    let out = `# ${match.name} [${match.ref}]\n\n`;
    if (match.form) out += `Form: ${match.form}\n\n`;
    out += match.description;
    return this.#text(out);
  }

  // -------- Detachment lookup ---------------------------------------------

  #handleGetDetachment(args) {
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);
    if (!fd.factionPack) {
      return this.#text("Faction Pack data not loaded.");
    }
    const query = (args?.name || "").toUpperCase().trim();
    const det = fd.factionPack.detachments.find(
      (d) =>
        d.name.toUpperCase().includes(query) ||
        query.includes(d.name.toUpperCase()),
    );
    if (!det) {
      const names = fd.factionPack.detachments.map((d) => d.name).join(", ");
      return this.#text(`Detachment not found. Available: ${names}`);
    }
    let out = `# ${det.name} (DP: ${det.dp_cost})\n\n`;
    out += `## Rules\n`;
    for (const r of det.rules) {
      out += `\n### ${r.name}\n${r.description}\n`;
    }
    out += `\n## Enhancements\n`;
    for (const e of det.enhancements) {
      out += `\n### ${e.name}${e.cp_cost ? ` (${e.cp_cost}CP)` : ""}\n${e.description}\n`;
    }
    out += `\n## Stratagems\n`;
    for (const s of det.stratagems) {
      out += `\n### ${s.name} (${s.cp_cost || "?"}CP)\n`;
      if (s.when) out += `WHEN: ${s.when}\n`;
      if (s.target) out += `TARGET: ${s.target}\n`;
      if (s.effect) out += `EFFECT: ${s.effect}\n`;
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
      const unitsLoaded = data.mergedUnits ? "yes" : "no";
      const fpLoaded = data.factionPack ? "yes" : "no";
      lines.push(
        `- **${key}**: units=${unitsLoaded}, factionPack=${fpLoaded}`,
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

  // -------- Stratagem lookup ----------------------------------------------

  #handleGetStratagem(args) {
    const query = (args?.name || "").toUpperCase().trim();
    const detName = (args?.detachment || "").toUpperCase().trim();
    const fd = this.#getFactionData(args?.faction);
    if (fd.error) return this.#text(fd.error);
    const results = [];

    // Core stratagems
    if (this.coreRules?.stratagems) {
      for (const s of this.coreRules.stratagems) {
        if (
          s.name.toUpperCase().includes(query) ||
          query.includes(s.name.toUpperCase())
        ) {
          results.push({ source: "Core", ...s });
        }
      }
    }

    // Detachment stratagems
    if (fd.factionPack?.detachments) {
      for (const d of fd.factionPack.detachments) {
        if (
          detName &&
          !d.name.toUpperCase().includes(detName) &&
          !detName.includes(d.name.toUpperCase())
        )
          continue;
        for (const s of d.stratagems) {
          if (
            s.name.toUpperCase().includes(query) ||
            query.includes(s.name.toUpperCase())
          ) {
            results.push({ source: d.name, ...s });
          }
        }
      }
    }

    if (results.length === 0) {
      return this.#text(`Stratagem not found matching "${query}".`);
    }

    let out = "";
    for (const s of results) {
      out += `## ${s.name} [${s.source}]\n`;
      if (s.cp_cost) out += `CP: ${s.cp_cost}\n`;
      if (s.ref) out += `Ref: ${s.ref}\n`;
      if (s.when) out += `WHEN: ${s.when}\n`;
      if (s.target) out += `TARGET: ${s.target}\n`;
      if (s.effect) out += `EFFECT: ${s.effect}\n`;
      out += "\n";
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
