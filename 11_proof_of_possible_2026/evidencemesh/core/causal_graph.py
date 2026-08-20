"""
Causal Claim Dependency Graph (DAG) Engine.
Manages topological order of claims, prerequisite resolution, contradiction propagation, and cycle detection.
"""

from typing import List, Dict, Set, Optional, Tuple
from evidencemesh.models import AtomicClaim, CausalEdge, VerificationStatus


class CausalGraph:
    """
    Directed Acyclic Graph (DAG) linking atomic claims via logical relationships:
    - prerequisite_of (Claim A must hold for Claim B to be evaluated)
    - entails (Claim A logically implies Claim B)
    - contradicts (Claim A refutes Claim B)
    - causes (Causal mechanism linkage)
    """

    def __init__(self):
        self.claims: Dict[str, AtomicClaim] = {}
        self.edges: List[CausalEdge] = []
        self.adjacency_out: Dict[str, List[CausalEdge]] = {}
        self.adjacency_in: Dict[str, List[CausalEdge]] = {}

    def add_claim(self, claim: AtomicClaim) -> None:
        self.claims[claim.claim_id] = claim
        if claim.claim_id not in self.adjacency_out:
            self.adjacency_out[claim.claim_id] = []
        if claim.claim_id not in self.adjacency_in:
            self.adjacency_in[claim.claim_id] = []

    def add_edge(self, source_id: str, target_id: str, relation_type: str = "entails", weight: float = 1.0) -> bool:
        if source_id not in self.claims or target_id not in self.claims:
            return False

        edge = CausalEdge(source_id=source_id, target_id=target_id, relation_type=relation_type, weight=weight)
        self.edges.append(edge)
        self.adjacency_out[source_id].append(edge)
        self.adjacency_in[target_id].append(edge)
        return True

    def detect_cycles(self) -> List[List[str]]:
        """
        Detects cycles in the claim graph using DFS (Tarjan style).
        Returns list of cycles found.
        """
        visited: Dict[str, int] = {cid: 0 for cid in self.claims}  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str):
            visited[node] = 1
            path.append(node)

            for edge in self.adjacency_out.get(node, []):
                # Ignore contradiction edges for DAG cycle detection
                if edge.relation_type == "contradicts":
                    continue
                neighbor = edge.target_id
                if visited.get(neighbor, 0) == 1:
                    cycle_idx = path.index(neighbor)
                    cycles.append(path[cycle_idx:] + [neighbor])
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor)

            path.pop()
            visited[node] = 2

        for node_id in self.claims:
            if visited[node_id] == 0:
                dfs(node_id)

        return cycles

    def topological_sort(self) -> List[str]:
        """
        Returns topological ordering of claims (prerequisites first).
        If cycle detected, returns default key order.
        """
        in_degree: Dict[str, int] = {cid: 0 for cid in self.claims}
        for edge in self.edges:
            if edge.relation_type in ["prerequisite_of", "causes", "entails"]:
                in_degree[edge.target_id] += 1

        queue = [cid for cid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for edge in self.adjacency_out.get(curr, []):
                if edge.relation_type in ["prerequisite_of", "causes", "entails"]:
                    in_degree[edge.target_id] -= 1
                    if in_degree[edge.target_id] == 0:
                        queue.append(edge.target_id)

        if len(order) < len(self.claims):
            # Fallback in case of cycle
            return list(self.claims.keys())
        return order

    def propagate_verification_states(self) -> None:
        """
        Propagates verified and refuted states across entailment and contradiction edges.
        """
        order = self.topological_sort()

        for cid in order:
            claim = self.claims[cid]
            # Check outgoing edges
            for edge in self.adjacency_out.get(cid, []):
                target = self.claims.get(edge.target_id)
                if not target:
                    continue

                if edge.relation_type == "contradicts":
                    if claim.status == VerificationStatus.VERIFIED and target.status == VerificationStatus.VERIFIED:
                        target.status = VerificationStatus.CONTRADICTED
                        target.confidence_score = max(0.1, target.confidence_score * 0.3)
                        target.epistemic_uncertainty = min(0.95, target.epistemic_uncertainty + 0.4)

                elif edge.relation_type == "prerequisite_of":
                    if claim.status in [VerificationStatus.REFUTED, VerificationStatus.CONTRADICTED]:
                        target.status = VerificationStatus.REFUTED
                        target.explanation = f"Prerequisite {claim.claim_id} failed verification."
                        target.confidence_score = 0.05
                        target.epistemic_uncertainty = 0.9

    def get_contradiction_count(self) -> int:
        count = 0
        for edge in self.edges:
            if edge.relation_type == "contradicts":
                s = self.claims.get(edge.source_id)
                t = self.claims.get(edge.target_id)
                if s and t:
                    if (s.status == VerificationStatus.VERIFIED and t.status in [VerificationStatus.VERIFIED, VerificationStatus.CONTRADICTED]) or \
                       (s.status == VerificationStatus.CONTRADICTED or t.status == VerificationStatus.CONTRADICTED):
                        count += 1
        return count
