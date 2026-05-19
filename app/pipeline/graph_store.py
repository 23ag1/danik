from app.pipeline.graph import FraudGraph

_graph = FraudGraph()


def get_fraud_graph() -> FraudGraph:
    return _graph


def reset_fraud_graph() -> None:
    global _graph
    _graph = FraudGraph()
