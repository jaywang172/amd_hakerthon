from mi300x_launch_doctor.benchmark.results import sample_benchmark
from mi300x_launch_doctor.report.markdown import audit_context_section, deployment_blockers, generate_markdown_report
from mi300x_launch_doctor.schemas import RepoInventory, RiskItem, ScoreResult


def _risk(file: str, category: str = "cuda_api") -> RiskItem:
    return RiskItem(
        severity="medium",
        category=category,
        file=file,
        line=1,
        evidence="torch.cuda.is_available()",
        why_it_matters="test",
        recommendation="test",
        rule_id="python.torch_cuda",
    )


def test_report_separates_audit_context_from_deployment_blockers():
    risks = [_risk("modules/devices.py"), _risk("docs/guide.md"), _risk("vllm/platforms/rocm.py")]

    blockers = deployment_blockers(risks)
    context = audit_context_section(risks)

    assert [risk.file for risk in blockers] == ["modules/devices.py"]
    assert "Documentation" in context
    assert "ROCm compatibility implementation" in context


def test_report_includes_stress_limit_metadata():
    inventory = RepoInventory(
        repo_name="stress",
        source="fixture",
        root_path="/tmp/stress",
        scan_scope="Runtime deployment scan",
        files_scanned=3000,
        files_discovered=3500,
        files_omitted_by_limit=500,
        scan_limit_applied=True,
        important_files=["requirements.txt"],
        languages=["Python"],
        frameworks=["PyTorch"],
    )
    score = ScoreResult(score=88, label="Ready for AMD deployment")
    report = generate_markdown_report(inventory, [], score, sample_benchmark(), ["scan_result.json"]).content

    assert "Files discovered in scope: 3500" in report
    assert "Files omitted by stress limit: 500" in report
