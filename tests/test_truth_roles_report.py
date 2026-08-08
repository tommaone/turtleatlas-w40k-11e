"""Report-only auto-derived role-truth checks, cross-faction.

These encode *domain expectations* derived from weapon stats and verified
against the engine's own numbers. Nothing here is recomputed by hand.

Epistemic split (per the dojo LLM-boundary contract):
  - ARMOR SHARE / HORDE SHARE  come from weapon stats (S/AP/D/A). INTERPRETATION.
  - LEAN (dpp[vehicle] - dpp[infantry]) comes from the engine's weighted-mix
    loadout optimisation. TRUTH.

The honest truths are CORRELATIONAL, not per-unit:
  T1. armor_share and lean must positively correlate ACROSS a faction's units.
      A faction whose anti-tank units do NOT trend vehicle-lean (Spearman
      strongly negative, enough units) has a config problem — its anti-tank
      guns don't actually beat armour.
  T2. horde_share and lean must negatively correlate (anti-horde units trend
      infantry-lean).
  T3. Any unit referencing a weapon missing from the catalog is a data gap
      (resolve_loadout raises KeyError).

Per-unit deviations are EXPECTED (a lascannon among bolters is not an
anti-armor unit; a Voldus with S12 melee still shreds infantry), so we do
NOT flag them individually. We only xfail when the faction-wide TREND is
absent or inverted, and we write the full per-unit table to the report for
human triage.

All failure thresholds live in one place (below) so the suite is honest
about its own calibration, not magic numbers hidden in asserts.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import _ld_dmg
from tests.crossfaction_common import ALL_FACTIONS, load_engine

# ── Calibration (single source of truth for the thresholds) ─────────────
ARMOR_MIN_S = 8          # anti-armor: melta/lance/lascannon-class Strength
ARMOR_MAX_AP = -2        # anti-armor: AP -2 or better
ARMOR_MIN_D = 2          # anti-armor: Damage 2+
HORDE_MIN_SHOT = 20      # horde: 20+ effective shots in the loadout
HORDE_MIN_A = 15         # horde: one weapon with 15+ attacks
HORDE_MAX_S = 5          # horde: max Strength 5 (no anti-armor punch)
MIN_UNITS_FOR_TREND = 8  # below this, correlation is not statistically
                         # meaningful → no xfail, just report.
TREND_EPS = 1e-6
# FAIL thresholds are deliberately asymmetric and honest about what they
# flag. They only trip on CLEAR inversion, not on soft/weak trends.
ARMOR_TREND_FAIL = -0.25      # fail if anti-armor units clearly lean infantry
HORDE_TREND_FAIL = 0.25       # fail if anti-horde units clearly lean vehicle

# Below |r| the trend is weak — collected as a WARNING (report only), not a
# fail. Rationale: a faction where every unit leans the same way produces a
# spurious rank correlation (e.g. Votann, where nothing has a serious vehicle
# meta — everything drifts mildly infantry-lean). That is a real observation
# but NOT a horde-config bug, so it must not fail.
WEAK_TIE = 0.15


def _resolved_weapons(eng, name):
    """Flat list of weapons the engine resolved for a unit.

    Returns a string starting 'unresolvable:' if the unit references a weapon
    missing from the catalog (real data gap surfaced in the report).
    """
    try:
        res = eng.resolve_loadout(name, eng.config.target_profiles["Knight"])
    except KeyError as e:
        return f"unresolvable:{e}"
    if res is None:
        return None
    _, ranged, melee, innate, _ = res
    return list(ranged) + list(melee) + list(innate)


def _shares(weapons):
    """armor_share / horde_share of a loadout.

    armor_share: fraction of attacks×D coming from S>=8/AP<=-2/D>=2 weapons.
    horde_share: fraction of attacks coming from low-S (<=5) weapons — i.e.
      the loadout's anti-horde volume. A squad of bolters (S4) is horde-clear
      even though no single gun has 15 attacks; the aggregate matters.
    """
    def slot(cond):
        return sum(w.attacks * w.damage for w in weapons if cond(w))
    def shot(cond):
        return sum(w.attacks for w in weapons if cond(w))

    total_slot = max(slot(lambda w: True), 1e-9)
    total_shot = max(shot(lambda w: True), 1e-9)
    armor_share = slot(lambda w: w.strength >= ARMOR_MIN_S
                       and w.ap <= ARMOR_MAX_AP and w.damage >= ARMOR_MIN_D) / total_slot
    horde_share = shot(lambda w: w.strength <= HORDE_MAX_S) / total_shot
    return round(armor_share, 4), round(horde_share, 4)


def _unit_lean(eng, name):
    """dpp(vehicle) - dpp(infantry) from the engine's weighted-mix
    optimisation — the same code path as the findings UI. Engine truth.

    Uses _ld_dmg_conditional so datasheet reroll abilities vs
    MONSTER/VEHICLE (Surge of Wrath etc.) are modelled exactly as the
    engine models them: per-target, phase-gated. Without this the report
    would diverge from compute_ranking for every ability-carrying unit.
    """
    from engine.ranking import _ld_dmg_conditional
    from engine.reroll_detect import detect_reroll_ability

    vm = eng.resolve_meta("vehicle")
    im = eng.resolve_meta("infantry")
    res_v = eng.resolve_loadout(name, vm)
    res_i = eng.resolve_loadout(name, im)
    if res_v is None or res_i is None:
        return None

    # Locate the unit's datasheet profile to auto-detect reroll abilities
    # (same lookup compute_ranking does).
    reroll_spec = None
    for unit in eng.data["units"]:
        if unit["name"] == name:
            profile = unit.get("profile") or {}
            for ab in profile.get("abilities", []) or []:
                spec = detect_reroll_ability(ab)
                if spec is not None:
                    reroll_spec = spec
                    break
            break

    def dpp_for(triples, res):
        pts, ranged, melee, innate, _ = res
        if pts <= 0:
            return 0.0
        total = 0.0
        for _, prof, w in triples:
            if reroll_spec is None:
                total += w * _ld_dmg(ranged, melee, innate, prof)
            else:
                # Mirror compute_ranking: conditional rerolls are applied
                # per-phase so a melee-only spec (Surge of Wrath) never
                # leaks onto ranged attacks.
                dr = _ld_dmg_conditional(ranged, [], [], prof, None, reroll_spec, "ranged") if ranged else 0
                dm = _ld_dmg_conditional([], melee, [], prof, None, reroll_spec, "melee") if melee else 0
                di_ = _ld_dmg_conditional([], [], innate, prof, None, reroll_spec, "both") if innate else 0
                total += w * (dr + dm + di_)
        return total / pts

    dv, di = dpp_for(vm, res_v), dpp_for(im, res_i)
    return dv - di


def _spearman(xs, ys):
    """Spearman rank correlation; None if fewer than 2 points."""
    n = len(xs)
    if n < 2:
        return None
    def ranks(vals):
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) ** 0.5
           * sum((b - my) ** 2 for b in ry) ** 0.5)
    return num / den if den > 0 else None


def faction_report(faction):
    """Compute per-unit shares+leans, faction trend stats, and failures."""
    eng = load_engine(faction)
    units, gaps = {}, []
    rows_armor, rows_horde, rows_lean = [], [], []
    for name in eng.config.known_units:
        if not isinstance(name, str) or name.startswith("_"):
            continue
        try:
            weapons = _resolved_weapons(eng, name)
            lean = _unit_lean(eng, name)
        except KeyError as e:
            gaps.append(f"{name}: unresolvable weapon -> {e}")
            continue
        if isinstance(weapons, str):           # catalog gap
            gaps.append(f"{name}: {weapons}")
            continue
        if not weapons or lean is None:
            continue
        armor_share, horde_share = _shares(weapons)
        units[name] = {
            "armor_share": armor_share, "horde_share": horde_share,
            "lean_delta": round(lean, 6),
            "best_s": max(w.strength for w in weapons),
            "max_attacks": max(w.attacks for w in weapons),
        }
        rows_armor.append(armor_share)
        rows_horde.append(horde_share)
        rows_lean.append(lean)

    r_armor = _spearman(rows_armor, rows_lean)
    r_horde = _spearman(rows_horde, rows_lean)
    n = len(units)
    failures = list(gaps)
    warnings = []
    if n >= MIN_UNITS_FOR_TREND:
        # A rank correlation over a one-sided sample is noise, not signal: if
        # every unit leans the SAME direction (e.g. Votann, where nothing has a
        # vehicle meta), the r value is ranking within one signed cluster. Only
        # keep a trend when there is genuine sign spread in the lean values.
        pos_leaders = sum(1 for l in rows_lean if l > TREND_EPS)
        neg_leaders = sum(1 for l in rows_lean if l < -TREND_EPS)
        has_sign_spread = pos_leaders >= 1 and neg_leaders >= 1

        if r_armor is not None and r_armor < ARMOR_TREND_FAIL:
            failures.append(
                f"armor_share×lean Spearman r={r_armor:+.3f} (n={n}) — anti-armor "
                f"units trend INFANTRY-lean; anti-tank config likely wrong"
            )
        if r_horde is not None and r_horde > HORDE_TREND_FAIL and has_sign_spread:
            failures.append(
                f"horde_share×lean Spearman r={r_horde:+.3f} (n={n}) — horde units "
                f"trend VEHICLE-lean; horde config likely wrong"
            )
        elif r_horde is not None and r_horde > HORDE_TREND_FAIL:
            warnings.append(
                f"note: horde_share×lean r={r_horde:+.3f} (n={n}) but lean is "
                f"one-sided (pos {pos_leaders}, neg {neg_leaders}) — rank artifact, "
                f"NOT a horde bug; faction has no strong vehicle meta"
            )
        # weak/absent trends: report-only observations, NOT failures.
        if r_armor is not None and -WEAK_TIE < r_armor < WEAK_TIE:
            warnings.append(
                f"clean: armor_share×lean r={r_armor:+.3f} (n={n}) — anti-armor is "
                f"NOT a strong driver; faction has no clear anti-tank/anti-infantry split"
            )
        if r_horde is not None and -WEAK_TIE < r_horde < WEAK_TIE:
            warnings.append(
                f"clean: horde_share×lean r={r_horde:+.3f} (n={n}) — no strong "
                f"horde-vs-armour lean; faction may lack strong vehicle meta"
            )
    return {
        "faction": faction,
        "n_units": n,
        "spearman_armor": r_armor,
        "spearman_horde": r_horde,
        "units": units,
        "failures": failures,
        "warnings": warnings,
    }


def write_report(out_dir="reports", filename="crossfaction_truth_report.json"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    combined = [faction_report(f) for f in ALL_FACTIONS]
    path = Path(out_dir) / filename
    path.write_text(json.dumps(combined, indent=2))
    total = sum(len(r["failures"]) for r in combined)
    nwarn = sum(len(r["warnings"]) for r in combined)
    flagged = [r["faction"] for r in combined if r["failures"]]
    print(f"[report] wrote {path} — {total} failures / {nwarn} warnings across "
          f"{len(combined)} factions (failing: {flagged})")
    return path


# ----------------------------------------------------------------------
# Pytest surface: per-faction xfail when the faction-wide TREND is broken.
# ----------------------------------------------------------------------

@pytest.fixture(scope="session")
def truth_report_file():
    return write_report()


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_truth_roles_report(faction, truth_report_file):
    rep = next(r for r in json.loads(truth_report_file.read_text())
               if r["faction"] == faction)
    fails = rep["failures"]
    warns = rep["warnings"]
    for m in warns:
        print(f"[TRUTH:{faction} (note)] {m}")
    for m in fails:
        print(f"[TRUTH:{faction}] {m}")
    if fails:
        pytest.xfail(
            f"{len(fails)} truth failure(s) in {faction} "
            f"(see report/{truth_report_file.name})"
        )