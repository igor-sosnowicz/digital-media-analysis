import importlib.util
import shutil

import pandas as pd

from digital_media_analysis import annotations, stance
from digital_media_analysis.paths import PROJECT_ROOT


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), PROJECT_ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_labels_leave_out_stance_files_in_the_same_folder(tmp_path):
    folder = tmp_path / "gold"
    folder.mkdir()
    pd.DataFrame([{"unit_id": "r1", "platform": "reddit", "annotator": "IS", "codebook_version": "2.0", "cites_source": 1,
                   "source_types": "media", "edit_about_sources": "", "uncertain": 0, "notes": ""}]).to_csv(folder / "IS.csv", index=False)
    pd.DataFrame([{"unit_id": "r1", "platform": "reddit", "annotator": "IS", "codebook_version": "2.2",
                   "consensus_stance": "supports", "uncertain": 0, "notes": ""}]).to_csv(folder / "stance_IS.csv", index=False)
    labels = annotations.load_labels("gold", tmp_path)
    assert labels["annotator"].tolist() == ["IS"] and "consensus_stance" not in labels
    assert stance.load_labels("gold", tmp_path)["consensus_stance"].tolist() == ["supports"]


def test_stance_thresholds_are_written_into_the_instrument_and_the_gate_is_checked(tmp_path):
    script = load_script("07b_validate_stance.py")
    copy = tmp_path / "stance_v1.py"
    shutil.copy(script.INSTRUMENT_PATH, copy)
    script.apply_thresholds({"relevance": 0.4, "supports": 0.6, "challenges": 0.7}, copy)
    lines = copy.read_text(encoding="utf-8").splitlines()
    assert "TUNED = True" in lines
    assert 'THRESHOLDS = {"relevance": 0.4, "supports": 0.6, "challenges": 0.7}' in lines
    assert script.gate({"challenges:f1": 0.55, "kappa": 0.41})["passed"]
    assert not script.gate({"challenges:f1": 0.45, "kappa": 0.9})["passed"]
    assert not script.gate({"challenges:f1": 0.9, "kappa": 0.39})["passed"]


def test_stance_agreement_counts_only_posts_coded_by_two_people():
    rows = [("u1", "A", "supports"), ("u1", "B", "supports"), ("u2", "A", "challenges"), ("u2", "B", "neutral"),
            ("u3", "A", "neutral"), ("u4", "B", "not_applicable")]
    labels = pd.DataFrame(rows, columns=["unit_id", "annotator", "consensus_stance"]).assign(platform="reddit")
    table = stance.agreement(labels, samples=50).set_index("variable")
    # u3 and u4 have one label each, so only u1 and u2 count.
    assert table.loc["consensus_stance", "units"] == 2
    assert table.loc["consensus_stance", "observed_agreement"] == 0.5
