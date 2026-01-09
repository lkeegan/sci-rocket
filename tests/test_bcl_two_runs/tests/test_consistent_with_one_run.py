from pathlib import Path
import json
import pytest


def load_scidash_data(run_type: str) -> dict:
    data_path = Path(__file__).parent.parent.parent / f"test_{run_type}" / "output" / "zfish" / "sci-dash" / "js" / "qc_data.js"
    assert data_path.exists()
    with open(data_path, "r") as f:
        json_data = f.read().split("var data = ")[1]
        return json.loads(json_data)


@pytest.mark.parametrize("field", [
    "experiment_name",
    "n_pairs",
    "n_pairs_success",
    "n_pairs_failure",
    "n_corrected_p5",
    "n_corrected_p7",
    "n_corrected_ligation",
    "n_corrected_rt",
    "n_corrected_hashing",
    "n_uncorrectable_p5",
    "n_uncorrectable_p7",
    "n_uncorrectable_ligation",
    "n_uncorrectable_rt",
    "n_hashing",
    "top_uncorrectables",
    "p5_index_counts",
    "p7_index_counts",
    "rt_barcode_counts",
    "ligation_barcode_counts",
    "uncorrectables_sankey",
    "sample_success",
    "hashing",
]
)
def test_output_consistent_between_one_run_and_two_runs(field: str):
    """This test requires that the ci/test_bcl_one_run and ci/test_bcl_two_runs workflows have been run."""
    one_run_data = load_scidash_data("bcl_one_run")
    two_runs_data = load_scidash_data("bcl_two_runs")
    assert one_run_data[field] == two_runs_data[field]