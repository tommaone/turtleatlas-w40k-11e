"""Guard: squad builds must not over-arm specials beyond the BSData datasheet cap.

For every squad in every faction, each non-default ranged weapon in a build
is matched to the corresponding BSData model-variant selection entry, and its
`count` must not exceed the variant's `max selections` constraint
(scope=parent, shared — i.e., per-squad hard cap, no scaling).

The converter (convert_squad_builds.py) historically emitted "2x <special>"
for every special mode regardless of the actual datasheet cap. This guard
catches that class of regression: if a build carries more specials than the
datasheet allows, the test fails with the exact build + weapon + cap.

BSData is the source of truth for special-weapon allowances (the datasheet
rule, expressed as a per-variant max-selections constraint). The constraint
semantics here: scope=parent + shared=true + no modifierGroups = flat
per-squad cap. Scaling caps (1 per N models) would carry modifierGroups
with a repeating-condition; those are NOT modelled by this guard yet —
extend if a scaling-cap regression appears.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BSDATA_DIR = REPO / "bsdata"
CONFIG_DIR = REPO / "data" / "config"

# our faction id -> BSData catalogue file name
BSFILE = {
    "chaos-space-marines": "Chaos - Chaos Space Marines",
    "thousand-sons": "Chaos - Thousand Sons",
    "emperors-children": "Chaos - Emperor's Children",
    "death-guard": "Chaos - Death Guard",
    "world-eaters": "Chaos - World Eaters",
    "grey-knights": "Imperium - Grey Knights",
    "space-marines": "Imperium - Space Marines",
    "aeldari": "Aeldari", "orks": "Orks", "necrons": "Necrons",
    "tau-empire": "Tau", "tyranids": "Tyranids",
    "genestealer-cults": "Genestealer Cults",
    "adepta-sororitas": "Imperium - Adepta Sororitas",
    "adeptus-custodes": "Imperium - Adeptus Custodes",
    "adeptus-mechanicus": "Imperium - Adeptus Mechanicus",
    "astra-militarum": "Imperium - Astra Militarum",
    "blood-angels": "Imperium - Blood Angels",
    "dark-angels": "Imperium - Dark Angels",
    "black-templars": "Imperium - Black Templars",
    "deathwatch": "Imperium - Deathwatch",
    "space-wolves": "Imperium - Space Wolves",
    "drukhari": "Drukhari", "chaos-daemons": "Chaos - Chaos Daemons",
    "leagues-of-votann": "Leagues of Votann",
    "imperial-knights": "Imperium - Imperial Knights",
    "chaos-knights": "Chaos - Chaos Knights",
}


def _cat_of(fid):
    p = BSDATA_DIR / f"{BSFILE[fid]}.json"
    if not p.exists():
        return None
    return json.load(open(p)).get("catalogue")


def _find_se(cat, name):
    for se in cat.get("sharedSelectionEntries", []) + cat.get("selectionEntries", []):
        if se.get("name") == name:
            return se
    return None


def _variant_max(sel):
    """{variant_name: max_selections} from selectionEntryGroups (model variants)."""
    out = {}
    for seg in sel.get("selectionEntryGroups", []):
        for e in seg.get("selectionEntries", []):
            mx = None
            for c in e.get("constraints", []):
                if c.get("type") == "max" and c.get("field") == "selections":
                    mx = c.get("value")
            out[e.get("name")] = mx
    return out


def _default_weapon(cfg):
    from collections import Counter
    base = None
    for b in cfg["builds"]:
        if b.get("name") in ("Melee", "Default", "default", "Base"):
            base = b
            break
    if base is None and cfg["builds"]:
        base = cfg["builds"][0]
    if not base:
        return None
    rc = Counter()
    for m in base.get("models", []):
        r = m.get("ranged")
        if isinstance(r, list):
            for w in r:
                rc[w] += m.get("count", 1)
        elif r:
            rc[r] += m.get("count", 1)
    return rc.most_common(1)[0][0] if rc else None


def _all_overarmed():
    findings = []
    for sq_path in sorted(CONFIG_DIR.glob("*/squads.json")):
        fid = sq_path.parent.name
        if fid not in BSFILE:
            continue
        cat = _cat_of(fid)
        if not cat:
            continue
        sq = json.load(open(sq_path))
        for unit, cfg in sq.items():
            if not isinstance(cfg, dict) or unit.startswith("_") or "builds" not in cfg:
                continue
            se = _find_se(cat, unit)
            if se is None:
                continue
            vmax = _variant_max(se)
            if not vmax:
                continue
            dflt = _default_weapon(cfg)
            for b in cfg["builds"]:
                from collections import Counter
                rc = Counter()
                for m in b.get("models", []):
                    r = m.get("ranged")
                    if isinstance(r, list):
                        for w in r:
                            rc[w] += m.get("count", 1)
                    elif r:
                        rc[r] += m.get("count", 1)
                for w, c in rc.items():
                    if w == dflt:
                        continue
                    match = None
                    wl = w.lower().split(" - ")[0].strip()
                    for vname, mx in vmax.items():
                        vn = vname.lower()
                        if wl in vn or vn in wl:
                            if "w/" in vn or wl in vn:
                                match = (vname, mx)
                                break
                    if match is None:
                        continue
                    vname, mx = match
                    if mx is not None and c > mx:
                        findings.append(
                            f"{fid}/{unit} build={b.get('name')!r}: "
                            f"{w} x{c} exceeds BSData max={mx} ({vname!r})"
                        )
    return findings


def test_no_overarmed_specials():
    """No build may carry more of a special weapon than the BSData datasheet cap."""
    findings = _all_overarmed()
    if findings:
        pytest.fail(
            f"{len(findings)} over-armed builds (special count exceeds BSData max):\n"
            + "\n".join("  " + f for f in findings)
            + "\n\nFix: reduce the special-model count to the BSData max and "
            "redistribute the freed model to the default loadout. See commit "
            "fixing Rubric Marines /Skirtarii/Kommandos for the recipe."
        )