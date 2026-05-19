import networkx as nx


class FraudGraph:
    """Граф авторов: рёбра при пересечении rule_flags, score — связность и история риска."""

    def __init__(self) -> None:
        self._graph = nx.Graph()

    def score_author(self, author_hash: str) -> float:
        if author_hash not in self._graph:
            return 0.0
        node = self._graph.nodes[author_hash]
        neighbor_risks = [
            self._graph.nodes[n].get("max_risk", 0.0)
            for n in self._graph.neighbors(author_hash)
        ]
        neighbor_avg = sum(neighbor_risks) / len(neighbor_risks) if neighbor_risks else 0.0
        degree = self._graph.degree(author_hash)
        repeat = max(0, node.get("events", 1) - 1)
        return min(
            1.0,
            node.get("max_risk", 0.0) * 0.35
            + neighbor_avg * 0.35
            + min(degree, 5) * 0.04
            + repeat * 0.08,
        )

    def register(self, author_hash: str, rule_flags: list[str], risk_score: float) -> float:
        if author_hash not in self._graph:
            self._graph.add_node(author_hash, events=0, max_risk=0.0, flags=set())
        node = self._graph.nodes[author_hash]
        node["events"] = node.get("events", 0) + 1
        node["max_risk"] = max(node.get("max_risk", 0.0), risk_score)
        node["flags"] = set(node.get("flags", set())) | set(rule_flags)

        for other in list(self._graph.nodes):
            if other == author_hash:
                continue
            if node["flags"] & self._graph.nodes[other].get("flags", set()):
                self._graph.add_edge(author_hash, other)

        return self.score_author(author_hash)
