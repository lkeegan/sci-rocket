import json
from pathlib import Path

def test_sci_dash_data():
    data_path = Path(__file__).parent.parent / "output" / "zfish" / "sci-dash" / "js" / "qc_data.js"
    assert data_path.exists()
    with open(data_path, "r") as f:
        json_data = f.read().split("var data = ")[1]
        data = json.loads(json_data)
    assert data["experiment_name"] == "zfish"
    assert data["n_pairs"] == 100000
    assert data["n_pairs_success"] == 64044
    assert data["n_pairs_failure"] == 35956
    assert data["n_corrected_p5"] == 1025
    assert data["n_corrected_p7"] == 867
    assert data["n_corrected_ligation"] == 402
    assert data["n_corrected_rt"] == 656
    assert data["n_corrected_hashing"] == 274
    assert data["n_uncorrectable_p5"] == 23826
    assert data["n_uncorrectable_p7"] == 22050
    assert data["n_uncorrectable_ligation"] == 2072
    assert data["n_uncorrectable_rt"] == 15053
    assert data["n_hashing"] == 2302

    assert "zfish-hash" in data["sample_success"]

    assert "zfish-hash" in data["hashing"]
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_correct"] == 15
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_corrected"] == 0
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_correct_upstream"] == 0

    assert data["rt_barcode_counts"]["P01"][0] == {'row': 'B', 'col': '1', 'frequency': 2048}
