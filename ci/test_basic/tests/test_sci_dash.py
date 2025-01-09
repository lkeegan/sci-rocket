import json
from pathlib import Path

def test_sci_dash_data():
    data_path = Path(__file__).parent.parent / "output" / "Drer.ZAe" / "sci-dash" / "js" / "qc_data.js"
    assert data_path.exists()
    with open(data_path, "r") as f:
        json_data = f.read().split("var data = ")[1]
        data = json.loads(json_data)
    assert data["experiment_name"] == "Drer.ZAe"
    assert data["n_pairs"] == 100000
    assert data["n_pairs_success"] == 19255
    assert data["n_pairs_failure"] == 80745
    assert data["n_corrected_p5"] == 447
    assert data["n_corrected_p7"] == 472
    assert data["n_corrected_ligation"] == 134
    assert data["n_corrected_rt"] == 425
    assert data["n_corrected_hashing"] == 37
    assert data["n_uncorrectable_p5"] == 7427
    assert data["n_uncorrectable_p7"] == 5113
    assert data["n_uncorrectable_ligation"] == 2158
    assert data["n_uncorrectable_rt"] == 78664
    assert data["n_hashing"] == 370

    assert "ZAe-10hpf-28" in data["sample_success"]
    assert "ZAe-14hpf-28" in data["sample_success"]

    assert "ZAe-10hpf-28" in data["hashing"]
    assert "ZAe-14hpf-28" in data["hashing"]
    assert data["hashing"]["ZAe-14hpf-28"]["10uM_P7_A8"]["n_correct"] == 111
    assert data["hashing"]["ZAe-14hpf-28"]["10uM_P7_A8"]["n_corrected"] == 23
    assert data["hashing"]["ZAe-14hpf-28"]["10uM_P7_A8"]["n_correct_upstream"] == 0
