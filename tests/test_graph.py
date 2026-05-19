from app.pipeline.graph import FraudGraph


def test_new_author_zero_score():
    graph = FraudGraph()
    assert graph.score_author("author-a") == 0.0


def test_register_increases_score_on_repeat():
    graph = FraudGraph()
    graph.register("author-a", ["кредит"], 0.8)
    first = graph.score_author("author-a")
    graph.register("author-a", ["займ"], 0.9)
    second = graph.score_author("author-a")
    assert second >= first


def test_connected_authors_share_flags():
    graph = FraudGraph()
    graph.register("author-a", ["кредит", "срочно"], 0.7)
    graph.register("author-b", ["кредит", "займ"], 0.6)
    assert graph.score_author("author-b") > 0.0
    assert graph._graph.has_edge("author-a", "author-b")
