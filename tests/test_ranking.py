from paymind.ranking.engine import RankInput, rank_options
from paymind.settings import RankingSettings


def test_ranking_orders_highest_score_first():
    rows = [
        RankInput("A", 0.7, 0.9, 0.01, 15.0, 1),
        RankInput("B", 0.2, 0.8, 0.04, 120.0, 2),
    ]
    ranked = rank_options(rows, RankingSettings())
    assert ranked[0].option_id == "A"
    assert ranked[0].rank == 1
