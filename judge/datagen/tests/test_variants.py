from judge_data.rubric_build import render, variants


def _rubric():
    """A compact layout rubric: `{context}` slots and a JSON schema output block."""
    scale = [{"label": "No", "definition": "n"}, {"label": "Yes", "definition": "y"}]
    return next(r for r in (render.render_record(f"r{i}", "c", "TRACE", "Judge.", scale, {})
                            for i in range(20)) if "<<" not in r["rendered_prompt"])


def test_all_variants_have_ids_and_keep_criteria():
    base = _rubric()
    rid = base["rubric_id"]
    out = variants.format_variants(base)
    assert [v["rubric_id"] for v in out] == [rid] + [f"{rid}#{k}" for k in list(variants.CONTRACTS)[1:]]
    assert all("variant" not in v for v in out)
    for v in out:
        assert "Judge." in v["rendered_prompt"]
        assert "{context}" in v["rendered_prompt"]


def test_nonjson_and_verdict_only():
    base = _rubric()
    by = {v["rubric_id"].partition("#")[2] or "base": v["rendered_prompt"]
          for v in variants.format_variants(base)}
    assert "<evaluation>" in by["nonjson_xml"] and "Here is the output JSON schema" not in by["nonjson_xml"]
    assert "score: <your score>" in by["nonjson_keyvalue"]
    assert "single word" in by["contract_bare_verdict"]


def test_unknown_variant_skipped():
    assert variants.format_variants(_rubric(), ["nope"]) == []
