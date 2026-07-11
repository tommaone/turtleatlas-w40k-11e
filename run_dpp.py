"""
Generic DPP ranking runner — works for any configured faction.

Usage:
    python3 run_dpp.py --faction chaos-knights
    python3 run_dpp.py --faction grey-knights --meta competitive --mission "Purge the Foe"
    python3 run_dpp.py --faction chaos-daemons --detachment "INFERNAL LANCE"
    python3 run_dpp.py --faction chaos-knights --detachment "ICONOCLAST FIEFDOM:0,HELHUNT LANCE:0"
    python3 run_dpp.py --list-factions
"""

import sys
import json
from pathlib import Path
from engine.ranking import RankingEngine


def list_factions():
    config_dir = Path(__file__).resolve().parent / "data" / "config"
    for d in sorted(config_dir.iterdir()):
        if d.is_dir():
            supported = d / "supported.json"
            if supported.exists():
                data = json.loads(supported.read_text())
                name = data.get("name", d.name)
                key = data.get("key", d.name)
                print(f"  {key:20s}  {name}")


def run(args: list[str] = None):
    import argparse

    parser = argparse.ArgumentParser(description="Run DPP ranking for a faction")
    parser.add_argument("--faction", type=str, default=None,
                        help="Faction key (e.g. chaos-knights, grey-knights)")
    parser.add_argument("--meta", type=str, default="competitive",
                        help="Meta profile name (default: competitive)")
    parser.add_argument("--mission", type=str, default=None,
                        help="Mission profile name (e.g. 'Purge the Foe')")
    parser.add_argument("--target", type=str, default=None,
                        help="Target profile name (overrides meta, e.g. Knight, MEQ)")
    parser.add_argument("--detachment", type=str, default=None,
                        help="Detachment modifier. Single: 'INFERNAL LANCE'. "
                             "Multi (comma-sep): 'ICONOCLAST FIEFDOM:0,HELHUNT LANCE:0'")
    parser.add_argument("--detachment-choice", type=int, default=0,
                        help="Which detachment modifier to apply (default: 0). "
                             "Ignored if --detachment uses multi-format with :choice.")
    parser.add_argument("--list-factions", action="store_true",
                        help="List available factions and exit")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of top results to show (default: 10)")

    parsed, _ = parser.parse_known_args(args)

    if parsed.list_factions:
        print("Available factions:")
        list_factions()
        return

    faction = parsed.faction
    if not faction:
        # Interactive mode: show factions, pick one
        print("Available factions:")
        list_factions()
        print()
        faction = input("Enter faction key: ").strip()

    engine = RankingEngine(faction)

    # Parse detachment argument — supports single or multi-detachment
    detachments_list: list[tuple[str, int]] | None = None
    single_detachment: str | None = None
    single_choice: int = 0

    if parsed.detachment:
        if "," in parsed.detachment:
            # Multi-detachment format: "NAME:idx,NAME:idx"
            detachments_list = []
            for part in parsed.detachment.split(","):
                part = part.strip()
                if ":" in part:
                    name, idx_str = part.rsplit(":", 1)
                    detachments_list.append((name.strip(), int(idx_str)))
                else:
                    detachments_list.append((part, 0))
        elif ":" in parsed.detachment:
            # Single detachment with explicit choice: "NAME:idx"
            name, idx_str = parsed.detachment.rsplit(":", 1)
            single_detachment = name.strip()
            single_choice = int(idx_str)
        else:
            single_detachment = parsed.detachment
            single_choice = parsed.detachment_choice

    # Build title
    if detachments_list:
        title = f"{faction} ranking | multi: {' + '.join(d[0] for d in detachments_list)}"
    elif single_detachment:
        title = f"{faction} ranking | {single_detachment} (choice {single_choice})"
    else:
        title = f"{faction} ranking"

    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

    # Common kwargs for compute_ranking
    rank_kwargs = dict(
        mission=parsed.mission,
        melta_active=False,
        heavy_stationary=False,
    )

    if detachments_list:
        rank_kwargs["detachments"] = detachments_list
    elif single_detachment:
        rank_kwargs["detachment"] = single_detachment
        rank_kwargs["detachment_choice"] = single_choice

    if parsed.target:
        target = engine.config.target_profiles.get(parsed.target)
        if not target:
            print(f"Unknown target: {parsed.target}")
            sys.exit(1)
        results = engine.compute_ranking(target=target, **rank_kwargs)
        engine.print_ranking(results[:parsed.top], target_name=parsed.target,
                             mission_name=parsed.mission)
    else:
        results = engine.compute_ranking(meta_name=parsed.meta, **rank_kwargs)
        engine.print_ranking(results[:parsed.top], meta_name=parsed.meta,
                             mission_name=parsed.mission)

    print(f"\n  Done. DPP range: {results[-1]['dpp']:.4f} – {results[0]['dpp']:.4f}")
    print()


if __name__ == "__main__":
    run()
