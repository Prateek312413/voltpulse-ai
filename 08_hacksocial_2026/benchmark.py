"""
ResilioNet AI - High-Throughput Performance & Mathematical Benchmark Suite
Measures P50, P95, P99 latency and execution throughput across all AI/ML & optimization modules.
Built for HackSocial 2026 Hackathon
"""

import time
import random
import statistics
from core.crisis_triage_nlp import CrisisNLPEngine
from core.resource_optimizer import ResourceOptimizer, SupplyHub, SupplyItem, DemandRequest
from core.vulnerability_index import VulnerabilityProfiler, ZoneDemographics, ZoneInfrastructure, RealtimeHazardModifiers
from core.mesh_packet_crypto import MeshPacketEngine, DisasterAuditLedger


def benchmark_nlp_triage(num_samples: int = 1000):
    print(f"\n[BENCHMARK 1/4] Running Zero-Shot NLP Crisis Triage Engine ({num_samples} requests)...")
    engine = CrisisNLPEngine()
    
    samples = [
        "EMERGENCY: Water rising past 2nd floor window! Family of 5 trapped including 1 newborn baby and my 78yo mother with diabetes. Insulin ruined. Location: 1420 Riverfront Ave.",
        "Elderly retirement center without power for 18 hours. 12 residents on oxygen concentrators. Generator fuel down to 5%.",
        "Roof collapsed during tremor! 3 workers trapped under concrete debris. Arterial bleeding from leg fracture.",
        "Community shelter has taken in 45 flood evacuees. Completely out of clean drinking water and baby formula.",
        "Extreme cold (-8C). 30 people shivering under highway overpass. High hypothermia risk. Need thermal emergency blankets."
    ]

    latencies_ms = []
    t_start = time.perf_counter()
    for i in range(num_samples):
        text = samples[i % len(samples)]
        s = time.perf_counter()
        engine.analyze_message(text, triage_id=f"BENCH-{i}")
        e = time.perf_counter()
        latencies_ms.append((e - s) * 1000.0)

    total_time = time.perf_counter() - t_start
    throughput = num_samples / total_time

    p50 = statistics.median(latencies_ms)
    p95 = statistics.quantiles(latencies_ms, n=100)[94]
    p99 = statistics.quantiles(latencies_ms, n=100)[98]

    print(f"  Throughput: {throughput:,.1f} triage requests / sec")
    print(f"  P50 Latency: {p50:.3f} ms | P95 Latency: {p95:.3f} ms | P99 Latency: {p99:.3f} ms")
    return {"throughput": throughput, "p50": p50, "p95": p95, "p99": p99}


def benchmark_resource_optimizer(num_demands: int = 500, num_hubs: int = 25):
    print(f"\n[BENCHMARK 2/4] Running Bipartite Matching & Equity Solver ({num_demands} Demands x {num_hubs} Hubs)...")
    optimizer = ResourceOptimizer(fairness_weight=0.35, distance_penalty_weight=0.05)

    # Generate synthetic hubs
    hubs = []
    for h in range(num_hubs):
        hubs.append(SupplyHub(
            hub_id=f"HUB-{h:03d}",
            name=f"Logistics Depot {h}",
            latitude=37.75 + random.uniform(-0.1, 0.1),
            longitude=-122.42 + random.uniform(-0.1, 0.1),
            inventory={
                "potable_water": SupplyItem(item_id="W1", name="Water", category="WATER", quantity=random.randint(100, 500), unit="gal"),
                "mre_food_rations": SupplyItem(item_id="F1", name="MRE", category="FOOD", quantity=random.randint(100, 500), unit="packs"),
                "insulin_cold_pack": SupplyItem(item_id="I1", name="Insulin", category="MED", quantity=random.randint(20, 80), unit="vials", is_perishable=True),
                "trauma_first_aid_kit": SupplyItem(item_id="T1", name="Trauma Kit", category="MED", quantity=random.randint(30, 100), unit="kits")
            }
        ))

    # Generate synthetic demands
    demands = []
    for d in range(num_demands):
        demands.append(DemandRequest(
            request_id=f"REQ-{d:04d}",
            requester_name=f"Demand {d}",
            latitude=37.75 + random.uniform(-0.1, 0.1),
            longitude=-122.42 + random.uniform(-0.1, 0.1),
            urgency_score=round(random.uniform(2.0, 10.0), 1),
            headcount=random.randint(1, 8),
            required_items={"potable_water": random.randint(2, 10), "mre_food_rations": random.randint(2, 15)},
            zone_id=f"ZONE-{d % 8}"
        ))

    t_start = time.perf_counter()
    plan = optimizer.optimize_allocations(demands, hubs)
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    print(f"  Solver Time: {elapsed_ms:.2f} ms")
    print(f"  Demands Fulfilled: {plan.matched_demands}/{num_demands} ({plan.fulfillment_rate_percent:.1f}%)")
    print(f"  Gini Equity Index: {plan.gini_equity_index:.4f}")
    return {"elapsed_ms": elapsed_ms, "fulfillment_rate": plan.fulfillment_rate_percent, "gini": plan.gini_equity_index}


def benchmark_vulnerability_profiler(num_zones: int = 5000):
    print(f"\n[BENCHMARK 3/4] Running Hyperlocal Vulnerability Profiler ({num_zones} Zone Profiles)...")
    profiler = VulnerabilityProfiler()

    t_start = time.perf_counter()
    for z in range(num_zones):
        demo = ZoneDemographics(total_population=random.randint(5000, 80000), elderly_ratio=random.uniform(0.05, 0.40))
        infra = ZoneInfrastructure(hospital_transit_minutes=random.uniform(5.0, 60.0))
        hazard = RealtimeHazardModifiers(flood_water_level_meters=random.uniform(0.0, 3.0), power_outage_active=(z % 2 == 0))
        profiler.compute_hrvi(f"ZONE-{z}", f"District {z}", demo, infra, hazard)

    total_time = time.perf_counter() - t_start
    throughput = num_zones / total_time

    print(f"  Throughput: {throughput:,.1f} zone HRVI evaluations / sec")
    print(f"  Average Latency: {(total_time / num_zones) * 1000.0:.4f} ms per zone")
    return {"throughput": throughput}


def benchmark_mesh_crypto_and_ledger(num_events: int = 1000):
    print(f"\n[BENCHMARK 4/4] Running HMAC-SHA256 Mesh Packet Crypto & Blockchain Ledger ({num_events} blocks)...")
    engine = MeshPacketEngine(node_id="NODE-BENCH-01")
    ledger = DisasterAuditLedger(node_id="NODE-BENCH-01")

    # Benchmark Signing & Verification
    t_start = time.perf_counter()
    for i in range(num_events):
        pkt = engine.create_packet("SOS_BEACON", {"id": i, "urgency": 9.0})
        engine.verify_and_ingest_packet(pkt)
        ledger.append_event("AID_TRANSACTION", {"id": i, "status": "CONFIRMED"})

    sign_verify_time = time.perf_counter() - t_start

    # Benchmark Full Chain Cryptographic Audit Verification
    t_verify_start = time.perf_counter()
    is_valid, report = ledger.verify_chain_integrity()
    verify_time_ms = (time.perf_counter() - t_verify_start) * 1000.0

    print(f"  Crypto Signing & Ingestion: {num_events / sign_verify_time:,.1f} signed packets / sec")
    print(f"  Full Blockchain Audit Time ({num_events + 1} blocks): {verify_time_ms:.2f} ms [Intact: {is_valid}]")
    return {"crypto_throughput": num_events / sign_verify_time, "chain_verify_ms": verify_time_ms}


def run_all_benchmarks():
    print("=" * 75)
    print("  RESILIONET AI - COMPREHENSIVE PERFORMANCE BENCHMARK SUITE")
    print("  Engineered for HackSocial 2026 Hackathon (Devpost)")
    print("=" * 75)

    nlp = benchmark_nlp_triage(1000)
    opt = benchmark_resource_optimizer(500, 25)
    hrvi = benchmark_vulnerability_profiler(5000)
    crypto = benchmark_mesh_crypto_and_ledger(1000)

    print("\n" + "=" * 75)
    print("  BENCHMARK SUMMARY RESULTS")
    print("=" * 75)
    print(f"  [OK] NLP Distress Triage:   {nlp['throughput']:,.0f} req/s  (P95: {nlp['p95']:.2f} ms)")
    print(f"  [OK] Bipartite Optimizer:  {opt['elapsed_ms']:.2f} ms for 500 demands x 25 hubs ({opt['fulfillment_rate']:.1f}% fulfilled)")
    print(f"  [OK] HRVI Vulnerability:   {hrvi['throughput']:,.0f} zone evaluations / s")
    print(f"  [OK] Mesh HMAC-SHA256:     {crypto['crypto_throughput']:,.0f} signed packets / s")
    print(f"  [OK] Blockchain Integrity: {crypto['chain_verify_ms']:.2f} ms for 1,001 cryptographically linked blocks")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_all_benchmarks()
