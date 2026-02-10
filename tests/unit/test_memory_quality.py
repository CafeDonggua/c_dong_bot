from dongdong_bot.agent.memory_quality import evaluate_memory_quality


def test_memory_quality_metrics():
    query = "喜歡 手沖 咖啡"
    results = [
        "我喜歡手沖咖啡",
        "最近喜歡淺焙咖啡",
        "我喜歡手沖咖啡",
    ]
    report = evaluate_memory_quality(
        query,
        results,
        accuracy_threshold=0.6,
        relevance_threshold=0.4,
        duplicate_rate_max=0.5,
    )

    metrics = {metric.metric_name: metric for metric in report.metrics}
    assert metrics["accuracy"].value >= 0.6
    assert metrics["relevance"].value >= 0.4
    assert metrics["duplicate_rate"].value <= 0.5
    assert report.passed is True
