import json

from judge_data.rubric_build import assemble, render
from judge_data.rubric_trace_match import resplit


def _rub(rid, cid, n=2, lang="en", numeric=False):
    scale = [{"label": f"L{i}", "definition": "d", **({"value": i / (n - 1)} if numeric else {})}
             for i in range(n)]
    return render.record(rid, cid, "c", "TRACE", scale, "Judge {context}. {assistant_turn}",
                         ["context", "assistant_turn"], task="Judge.", language=lang)


def test_scale_family_from_shape():
    assert render.scale_family("categorical", 2) == "binary"
    assert render.scale_family("categorical", 5) == "ordinal_5"
    assert render.scale_family("categorical", 14) == "wide_14"
    assert render.scale_family("numerical", 4) == "numerical_4"


def test_holdout_cuts_whole_concepts():
    rubs = [_rub(f"c{i}_{j}", f"c{i}") for i in range(20) for j in range(3)]
    out = assemble.build_corpus(rubs, concept_holdout_fraction=0.25, holdout_scale_families=set(),
                                holdout_languages=set(), seed=1)
    by_concept = {}
    for r in out:
        by_concept.setdefault(r["concept_id"], set()).add(r["split"])
    assert all(len(s) == 1 for s in by_concept.values())  # never split across train and test
    assert sum(s == {"test"} for s in by_concept.values()) == 5


def test_holdout_axes():
    rubs = [_rub("w", "c0", n=14, lang="ja"), _rub("f", "c1", n=14),
            _rub("l", "c2", lang="ja"), _rub("t", "c3")]
    out = {r["rubric_id"]: r for r in assemble.build_corpus(rubs, concept_holdout_fraction=0.0)}
    assert out["w"]["holdout_axes"] == ["scale_family", "language"]
    assert out["f"]["holdout_axes"] == ["scale_family"]
    assert out["l"]["holdout_axes"] == ["language"]
    assert out["t"]["split"] == "train" and out["t"]["holdout_axes"] == []


def test_concept_holdout_draws_from_every_concept():
    rubs = [_rub(f"c{i}_0", f"c{i}") for i in range(10)]
    out = assemble.build_corpus(rubs, concept_holdout_fraction=1.0, holdout_scale_families=set(),
                                holdout_languages=set())
    assert {r["split"] for r in out} == {"test"}


def test_repair_invented_placeholders():
    r = _rub("x", "c")
    r["task"] = "Judge {made_up}."
    r["rendered_prompt"] = "Judge {context} and {made_up}. {assistant_turn}"
    (out,), counts = assemble.repair([r])
    assert "{made_up}" not in out["rendered_prompt"] and "{context}" in out["rendered_prompt"]
    assert out["task"] == "Judge made_up."
    assert counts == {"removed_invented_placeholders": 1}


def test_corpus_stats_and_write(tmp_path):
    rubs = assemble.build_corpus([_rub("a", "c1"), _rub("b", "c2", lang="ja")])
    rubs[0]["extra"] = "not a library field"
    st = assemble.corpus_stats(rubs)
    assert st["total"] == 2 and st["test"] == 1
    assemble.write_corpus(rubs, str(tmp_path / "o.jsonl"))
    rows = [json.loads(x) for x in (tmp_path / "o.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert all(set(r) <= set(assemble.LIBRARY_FIELDS) for r in rows)
    assert all("output_enum" not in r and "exclude_reason" not in r for r in rows)


def _library(tmp_path):
    def lib(rid, cid, n=2, lang="en", split="train", axes=()):
        r = _rub(rid, cid, n=n, lang=lang)
        r.update(split=split, holdout_axes=list(axes))
        return r
    rows = [lib("fixed", "fixed", n=14),
            lib("C1", "k1", split="test", axes=["concept"]),
            lib("C2", "k1", n=3, split="test", axes=["concept"]),
            lib("L1", "k2", lang="ja", split="test", axes=["language"]),
            lib("W1", "k4", n=14, split="test", axes=["scale_family"]),
            lib("T1", "k3")]
    p = tmp_path / "lib.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


def _rec(rid, tid):
    return {"meta": {"rubric_id": rid, "trace_id": tid}}


def test_resplit_plan_assign_and_contamination(tmp_path):
    plan = resplit.plan(_library(tmp_path), {"tA", "tB"}, trace_cut=10000,
                        scale_families={"wide_14"}, n_concepts=5)
    assert plan["test_traces"] == {"tA", "tB"}  # cut at 100 percent
    assert plan["held_langs"] == {"ja"}
    assert plan["kept_concepts"] == {"k1"}
    # A train rubric carries wide_14, so wide_14 cannot be held out and the train rubric stays put.
    assert plan["held_families"] == set() and plan["not_held"]["scale_families"] == ["wide_14"]
    recs = [_rec("fixed", "tA"), _rec("fixed", "t0"), _rec("C1", "t1"), _rec("C2", "t2"),
            _rec("L1", "t3"), _rec("W1", "t5"), _rec("T1", "t4")]
    for r in recs:
        r["meta"]["split"] = resplit.assign(r["meta"], plan)
    assert [r["meta"]["split"] for r in recs] == ["test_trace", "train", "test_axis", "test_axis",
                                                   "test_lang", "train", "train"]
    assert resplit.check(recs, plan) == []
    # A held out trace leaking into train is caught.
    leak = _rec("T1", "tA")
    leak["meta"]["split"] = "train"
    assert any("held out traces" in p for p in resplit.check(recs + [leak], plan))
    # A held out concept leaking into train is caught.
    leak = _rec("C1", "t9")
    leak["meta"]["split"] = "train"
    assert any("held out concepts" in p for p in resplit.check(recs + [leak], plan))
    # Folding the language into train is allowed on purpose.
    assert resplit.assign(recs[4]["meta"], plan, fold_lang_into_train=True) == "train"


def test_resplit_holds_out_scale_family_without_train_carrier(tmp_path):
    lib = tmp_path / "lib.jsonl"
    rows = [l for l in _library(tmp_path).read_text().splitlines()
            if json.loads(l)["rubric_id"] != "fixed"]
    lib.write_text("\n".join(rows) + "\n")
    plan = resplit.plan(lib, set(), scale_families={"wide_14"}, n_concepts=0)
    assert plan["held_families"] == {"wide_14"} and "W1" in plan["test_axis_rubrics"]
