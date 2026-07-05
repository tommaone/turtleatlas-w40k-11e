"""
Chaos Knights DPP engine — all 7 runs for Knight profile + competitive meta.
"""
from engine.ranking import RankingEngine
import json

engine = RankingEngine("chaos-knights")

print("=" * 80)
print("RUN 1: Knight target profile — Purge the Foe (with print_ranking)")
print("=" * 80)

results = engine.compute_ranking(target=engine.config.target_profiles["Knight"], mission="Purge the Foe")
engine.print_ranking(results, target_name="Knight", mission_name="Purge the Foe")

print()
print("=" * 80)
print("RUN 2: competitive meta — Purge the Foe (with print_ranking)")
print("=" * 80)

results = engine.compute_ranking(meta_name="competitive", mission="Purge the Foe")
engine.print_ranking(results, meta_name="competitive", mission_name="Purge the Foe")

print()
print("=" * 80)
print("RUN 3: competitive meta — Purge the Foe + Bastions of Tyranny (Tyrant: +1 to hit)")
print("=" * 80)

results = engine.compute_ranking(meta_name="competitive", mission="Purge the Foe",
                                  detachment="BASTIONS OF TYRANNY", detachment_choice=0)
engine.print_ranking(results, meta_name="competitive", mission_name="Purge the Foe (Bastions modifier)")

print()
print("=" * 80)
print("RUN 4: Knight target — Purge the Foe + Bastions of Tyranny (Tyrant: +1 to hit)")
print("=" * 80)

results = engine.compute_ranking(target=engine.config.target_profiles["Knight"], mission="Purge the Foe",
                                  detachment="BASTIONS OF TYRANNY", detachment_choice=0)
engine.print_ranking(results, target_name="Knight", mission_name="Purge the Foe (Bastions modifier)")

print()
print("=" * 80)
print("RUN 5: all-comers meta — Purge the Foe")
print("=" * 80)

results = engine.compute_ranking(meta_name="all-comers", mission="Purge the Foe")
engine.print_ranking(results, meta_name="all-comers", mission_name="Purge the Foe")

print()
print("=" * 80)
print("RUN 6: raw DPP vs Knight target (no mission weighting, sorted by DPP descending)")
print("=" * 80)

results = engine.compute_ranking(target=engine.config.target_profiles["Knight"])
for r in sorted(results, key=lambda r: r['dpp'], reverse=True):
    print(f"{r['name']:<40s} {r['points']:>4d}pts  DPP={r['dpp']:.4f}  DMG={r['total_damage']:.2f}  SURV_AP0={r['surv']['effective_wounds']['ap0']:.1f}")

print()
print("=" * 80)
print("RUN 7: verifying engine import (already done above)")
print("=" * 80)
print("Import OK (all runs completed successfully)")
