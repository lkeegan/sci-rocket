from pathlib import Path
import json
import pytest


def load_scidash_data(experiment: str) -> dict:
    data_path = Path(__file__).parent.parent / "output" / experiment / "sci-dash" / "js" / "qc_data.js"
    assert data_path.exists()
    with open(data_path, "r") as f:
        json_data = f.read().split("var data = ")[1]
        return json.loads(json_data)


@pytest.mark.parametrize("experiment", ["bcl_two_runs", "fastq_from_bcl_one_run", "fastq_from_bcl_two_runs"])
@pytest.mark.parametrize("field", [
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
    "hashing_summary",
]
)
def test_output_consistent_between_experiments(experiment: str, field: str):
    one_run_data = load_scidash_data("bcl_one_run")
    experiment_data = load_scidash_data(experiment)
    assert one_run_data[field] == experiment_data[field]
