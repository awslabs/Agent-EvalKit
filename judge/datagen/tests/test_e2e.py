"""End to end with MockClient: 2 concepts -> rubrics -> synthesized traces -> annotation."""
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import read_jsonl

from judge_data.annotate.prompt import META_KEYS
from judge_data.rubric_build.assemble import LIBRARY_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run([sys.executable, "-m", *args], cwd=cwd, env=env, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


MOCK = ["--backend", "mock", "--cache", "none"]


def check_library(lib):
    for r in lib:
        assert set(r) <= set(LIBRARY_FIELDS), sorted(set(r) - set(LIBRARY_FIELDS))
        assert r["split"] in ("train", "test")
        assert r.get("output_enum") != r["score_enum"]


def check_records(rows, meta=True):
    assert rows
    for r in rows:
        assert set(r) >= {"id", "prompt", "completion"}
        if meta:
            assert tuple(r["meta"]) == META_KEYS
        assert r["prompt"][0]["role"] == "user" and r["completion"][0]["role"] == "assistant"
        p = r["prompt"][0]["content"]
        assert "<<" not in p and "{context}" not in p and "{tool_turn}" not in p


def test_concepts_to_training_records(tmp_path, concepts_file, agents_file):
    out = tmp_path / "out"
    run("judge_data.rubric_build", "--concepts", str(concepts_file), "--out",
        str(out / "rubric_library.jsonl"), "--presentations", "2", "--holdout-fraction", "1.0",
        *MOCK, cwd=tmp_path)
    lib = read_jsonl(out / "rubric_library.jsonl")
    check_library(lib)
    assert len(lib) == 4
    assert {r["concept_id"] for r in lib} == {"c0001", "c0002"}
    by_id = {r["rubric_id"]: r for r in lib}
    assert {r["split"] for r in lib} == {"test"}
    concepts = read_jsonl(out / "concepts.jsonl")
    assert all(list(c) == ["concept_id", "concept", "level", "domain"] for c in concepts)
    assert (out / "rubric_build_report.json").exists()

    run("judge_data.trace_synth", "--rubric-library", str(out / "rubric_library.jsonl"),
        "--agent-registry", str(agents_file), "--out", str(out / "pairs.jsonl"), "--verify",
        *MOCK, cwd=tmp_path)
    pairs = read_jsonl(out / "pairs.jsonl")
    assert len(pairs) == sum(len(r["score_enum"]) for r in lib)
    assert all(p["verified_severity"] in ("absent", "partial", "full") for p in pairs)

    run("judge_data.annotate", "--pairs", str(out / "pairs.jsonl"), "--out",
        str(out / "output.jsonl"), "--agent-registry", str(agents_file), *MOCK, cwd=tmp_path)
    rows = read_jsonl(out / "output.jsonl")
    check_records(rows)
    assert len(rows) == len(pairs)
    assert {r["meta"]["rubric_id"] for r in rows} == set(by_id)
    assert {r["meta"]["teacher"] for r in rows} == {"mock"}
    judgments = read_jsonl(out / "output.judgments.jsonl")
    assert len(judgments) == len(pairs) and all(j["ok"] for j in judgments)


def test_seeds_path_runs_clean_room(tmp_path):
    seeds = tmp_path / "seeds.jsonl"
    seeds.write_text("".join(json.dumps({"rubric_idx": i, "metric_name": f"Seed {i}",
                                         "definition": f"Whether the reply is polite, case {i}."})
                             + "\n" for i in range(4)))
    run("judge_data.rubric_build", "--seeds", str(seeds), "--out", str(tmp_path / "lib.jsonl"),
        "--embed-backend", "hash", "--functional-test", "2", *MOCK, cwd=tmp_path)
    report = json.loads((tmp_path / "rubric_build_report.json").read_text())
    assert report["cleanroom"]["checked"] == report["generation"]["rubrics"]
    assert report["functional_test"]["in_enum"] == 2


def test_matching_pipeline(tmp_path, concepts_file, pool_file):
    lib = tmp_path / "rubric_library.jsonl"
    run("judge_data.rubric_build", "--concepts", str(concepts_file), "--out", str(lib), *MOCK,
        cwd=tmp_path)
    run("judge_data.rubric_trace_match", "--rubric-library", str(lib), "--traces",
        str(pool_file), "--traces-limit", "6", "--cap", "3", "--out", str(tmp_path / "m"), *MOCK,
        cwd=tmp_path)
    assert read_jsonl(tmp_path / "m" / "pairs.jsonl")
    run("judge_data.annotate", "--pairs", str(tmp_path / "m"),
        "--rubric-library", str(lib), "--out", str(tmp_path / "a"), "--strip-pct", "50", *MOCK,
        cwd=tmp_path)
    run("judge_data.rubric_trace_match.assemble", "--annotated", str(tmp_path / "a"),
        "--rubric-library", str(lib), "--out", str(tmp_path / "train"), cwd=tmp_path)
    check_library(read_jsonl(lib))
    rows = read_jsonl(tmp_path / "train" / "train.jsonl")
    check_records(rows)
    assert {r["meta"]["split"] for r in rows} == {"train"}
    assert all(r["completion"][0]["content"].startswith("```json") for r in rows)
    assert json.loads((tmp_path / "train" / "manifest.json").read_text())["records"] == len(rows)
    out = run("judge_data.rubric_trace_match.verify", "--file", str(tmp_path / "train" / "train.jsonl"),
              "--rubric-library", str(lib), cwd=tmp_path)
    assert "hard violations 0 of" in out


def test_annotate_rejects_options_of_the_other_source(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    pairs.write_text("")
    (tmp_path / "m").mkdir()
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    for args, msg in [
        (["--pairs", str(pairs), "--strip-pct", "30"], "--strip-pct applies only to matched"),
        (["--pairs", str(tmp_path / "m"), "--agent-registry", "x"], "applies only to synthesized"),
        (["--pairs", str(tmp_path / "m")], "--rubric-library is required"),
        (["--pairs", str(tmp_path / "m"), "--pairs", str(pairs)], "not a mix"),
    ]:
        r = subprocess.run([sys.executable, "-m", "judge_data.annotate", *args, "--out",
                            str(tmp_path / "o"), *MOCK], cwd=tmp_path, env=env,
                           capture_output=True, text=True)
        assert r.returncode == 2 and msg in r.stderr, r.stderr


def test_recipe_with_mock_backend(tmp_path, concepts_file, agents_file):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHON": sys.executable}
    out = tmp_path / "recipe"
    r = subprocess.run(["bash", str(ROOT / "recipes" / "build_training_data.sh"),
                        "--concepts", str(concepts_file), "--agents", str(agents_file),
                        "--out", str(out), "--verify", *MOCK], env=env, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    check_records(read_jsonl(out / "output.jsonl"))
    # Reusing the library skips phase 1.
    r = subprocess.run(["bash", str(ROOT / "recipes" / "build_training_data.sh"),
                        "--rubric-library", str(out / "rubric_library.jsonl"), "--agents",
                        str(agents_file), "--out", str(out), *MOCK], env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0 and "Reusing rubric library" in r.stdout, r.stdout + r.stderr


def test_gapfill_rerender_variants(tmp_path, concepts_file):
    lib = tmp_path / "rubric_library.jsonl"
    run("judge_data.rubric_build", "--concepts", str(concepts_file), "--out", str(lib), *MOCK,
        cwd=tmp_path)
    gap = tmp_path / "gapfill_library.jsonl"
    run("judge_data.rubric_build.gapfill", "--library", str(lib), "--out", str(gap),
        "--presentations", "1", "--plan-scale", "0.02", "--embed-backend", "hash", *MOCK,
        cwd=tmp_path)
    rows = read_jsonl(gap)
    check_library(rows)
    assert rows and all(r["concept_id"].startswith("gap_") for r in rows)
    assert all(set(r) == {"concept", "ok", "reject_reason"}
               for r in read_jsonl(tmp_path / "library_audit.jsonl"))

    before = {r["rubric_id"]: r for r in read_jsonl(lib)}
    run("judge_data.rubric_build.rerender", "--library", str(lib), cwd=tmp_path)
    after = {r["rubric_id"]: r for r in read_jsonl(lib)}
    check_library(after.values())
    assert set(after) == set(before)
    assert all(after[k]["split"] == before[k]["split"] for k in before)

    var = tmp_path / "variants.jsonl"
    run("judge_data.rubric_build.variants", "--library", str(lib), "--out", str(var),
        "--variants", "base,numeric,nonjson_xml", "--skip-no-task", cwd=tmp_path)
    rows = read_jsonl(var)
    check_library(rows)
    assert len(rows) == 3 * len(after)
    assert any(r["rubric_id"].endswith("#nonjson_xml") for r in rows)
