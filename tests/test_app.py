import app


def test_ui_bad_input_returns_clear_error_without_raising():
    score_md, risks, report, dockerfile, requirements, script, downloads = app.analyze("not-a-url", None, None)

    assert "Analysis Error" in score_md
    assert "Unsupported source" in score_md
    assert risks == []
    assert "No deployment artifacts were generated" in report
    assert dockerfile == ""
    assert requirements == ""
    assert script == ""
    assert downloads == []


def test_ui_url_with_whitespace_returns_clear_error_without_raising():
    score_md, risks, report, dockerfile, requirements, script, downloads = app.analyze(
        "https://github.com/octocat/Hello World", None, None
    )

    assert "Analysis Error" in score_md
    assert "URL contains whitespace" in score_md
    assert risks == []
    assert "No deployment artifacts were generated" in report
    assert dockerfile == ""
    assert requirements == ""
    assert script == ""
    assert downloads == []


def test_ui_shows_top_10_deployment_blockers_only():
    score_md, risks, *_ = app.analyze("fixtures/cuda_risk_repo", None, None)

    assert "Showing top 10 deployment blockers" in score_md
    assert len(risks) == 10
    assert risks[0][0] == "high"


def test_ui_real_benchmark_json_changes_status(tmp_path):
    benchmark = tmp_path / "benchmark.json"
    benchmark.write_text(
        '{"benchmark_mode":"real","model":"Qwen/Qwen2.5-0.5B-Instruct","backend":"vLLM ROCm","gpu":"AMD Instinct MI300X","load_success":true,"avg_latency_ms":742,"p50_latency_ms":690,"p95_latency_ms":1103,"tokens_per_second":68.4,"memory_used_gb":18.2}',
        encoding="utf-8",
    )

    score_md, _, report, *_ = app.analyze("fixtures/mostly_ready_repo", None, str(benchmark))

    assert "Benchmark Status: **Real Run**" in score_md
    assert "Benchmark Status: **Real Run**" in report
    assert "Sample benchmark format" not in report
