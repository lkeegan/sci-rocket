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
    assert "ZAe-10hpf-28" in data["sample_success"]
    assert "ZAe-14hpf-28" in data["sample_success"]
