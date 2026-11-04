import json
import re
from pathlib import Path

import pytest
import yaml

from housing_lima.cli import main
from housing_lima.validate import validate_run

ROOT = Path(__file__).resolve().parents[1]


def out_json(capsys):
    return json.loads(capsys.readouterr().out)


def test_new_run_ok_and_error_codes(tmp_path, capsys):
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({"price_min": 250000, "price_max": 400000, "currency": "PEN", "min_area_m2": 60,
                                   "min_bedrooms": 2, "districts": ["Surco", "Barranco"], "down_payment_pct": 20,
                                   "extras_text": "con cochera"}), encoding="utf-8")
    assert main(["new-run", "--answers", str(answers), "--runs-root", str(tmp_path / "runs")]) == 0
    res = out_json(capsys)
    assert res["inputs"]["districts"] == ["Santiago de Surco", "Barranco"]
    assert res["inputs"]["extras"]["parking_min"] == 1

    data = json.loads(answers.read_text(encoding="utf-8"))
    answers.write_text(json.dumps({**data, "down_payment_pct": 70}), encoding="utf-8")
    assert main(["new-run", "--answers", str(answers), "--runs-root", str(tmp_path / "runs2")]) == 2
    assert out_json(capsys)["code"] == "down_payment_out_of_range"


def test_end_to_end_fixture_dry_run(tmp_path, capsys):
    assert main(["fixture-run", "--runs-root", str(tmp_path)]) == 0
    res = out_json(capsys)
    run_dir = Path(res["run_dir"])
    assert res["ok"] and validate_run(run_dir, "all") == []
    for name in ("inputs.json", "listings.csv", "market_summary.json", "housing_params.json",
                 "opportunity_costs.json", "analysis_results.csv", "analysis_summary.json", "analysis_report.md"):
        assert (run_dir / name).exists(), name
    assert main(["summary", "--run", str(run_dir)]) == 0
    summary = out_json(capsys)
    assert summary["synthetic"] is True and summary["source_mode"] == "csv"
    assert all(set(d["verdicts"]) == {"5", "10", "15", "20", "30"} for d in summary["districts"])
    assert "dashboard" in summary["dashboard"]
    assert (run_dir / "validacion.txt").exists() and (tmp_path / "validacion.txt").exists()
    assert "RESULTADO: OK" in (tmp_path / "validacion.txt").read_text(encoding="utf-8")
    assert main(["figures", "--run", str(run_dir), "--out", str(tmp_path / "figuras")]) == 0
    figs = out_json(capsys)["figures"]
    assert len(figs) == 1 + 2 * len(summary["districts"]) and all(Path(f).exists() for f in figs)


def frontmatter(path: Path) -> dict:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m.group(1))




SKILLS = ["buy-vs-rent", "peru-listings-search", "peru-safe-investments", "rent-vs-buy-model", "streamlit-dashboard"]


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_files(skill):
    path = ROOT / ".claude" / "skills" / skill / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == skill
    assert len(fm["description"]) > 60
    assert len(path.read_text(encoding="utf-8").splitlines()) < 500
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"]) and len(fm["name"]) <= 64
    for ref in re.findall(r"\]\(([\w./-]+\.(?:md|csv))\)", path.read_text(encoding="utf-8")):
        assert (path.parent / ref).exists(), ref
    assert "CLAUDE_PLUGIN_ROOT" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("agent,skill", [("market-data", "peru-listings-search"),
                                         ("opportunity-cost", "peru-safe-investments"),
                                         ("financial-analysis", "rent-vs-buy-model"),
                                         ("streamlit-builder", "streamlit-dashboard")])
def test_agent_files(agent, skill):
    fm = frontmatter(ROOT / ".claude" / "agents" / f"{agent}.md")
    assert fm["name"] == agent and fm["description"] and fm["tools"]
    assert fm["skills"] == skill
    assert (ROOT / ".claude" / "skills" / skill / "SKILL.md").exists()


def test_research_agents_have_web_tools_and_analysis_does_not():
    assert "WebSearch" in frontmatter(ROOT / ".claude" / "agents" / "market-data.md")["tools"]
    assert "WebSearch" in frontmatter(ROOT / ".claude" / "agents" / "opportunity-cost.md")["tools"]
    assert "Web" not in frontmatter(ROOT / ".claude" / "agents" / "financial-analysis.md")["tools"]
