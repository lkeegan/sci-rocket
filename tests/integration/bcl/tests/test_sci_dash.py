import json
from pathlib import Path

def test_sci_dash_data():
    data_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "sci-dash" / "js" / "qc_data.js"
    umap_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "sci-dash" / "js" / "umap_data.js"
    assert data_path.exists()
    assert umap_path.exists()
    with open(data_path, "r") as f:
        json_data = f.read().split("var data = ")[1]
        data = json.loads(json_data)
    with open(umap_path, "r") as f:
        json_umap = f.read().split("var umapData = ")[1]
        umap_data = json.loads(json_umap)
    assert data["experiment_name"] == "bcl_one_run"
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
    assert data["sample_success"]["zfish-hash"]["starsolo_feature"] == "GeneFull_Ex50pAS"

    assert "zfish-hash" in data["hashing"]
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_correct"] == 15
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_corrected"] == 0
    assert data["hashing"]["zfish-hash"]["10uM_P7_A7"]["n_correct_upstream"] == 3

    # Check hashing summary consistency against per-hash counts.
    assert "hashing_summary" in data
    assert "hashing_summary_filt" in data
    assert "hashing_summary_bins" in data
    assert "hashing_summary_bin_labels" in data
    assert len(data["hashing_summary"]) == len(data["hashing"])
    assert len(data["hashing_summary_filt"]) == len(data["hashing"])
    assert set(row["sample_name"] for row in data["hashing_summary"]) == set(data["hashing"].keys())
    assert set(row["sample_name"] for row in data["hashing_summary_filt"]) == set(data["hashing"].keys())
    assert all("experiment_name" not in row for row in data["hashing_summary"])
    assert all("experiment_name" not in row for row in data["hashing_summary_filt"])

    for row in data["hashing_summary"]:
        sample = row["sample_name"]
        sample_hash_total = sum(
            v["n_correct"] + v["n_corrected"] + v["n_correct_upstream"] for v in data["hashing"][sample].values()
        )
        assert row["hash_count_total"] == sample_hash_total

    expected_bin_rows = len(data["hashing"]) * len(data["hashing_summary_bin_labels"])
    assert len(data["hashing_summary_bins"]) == expected_bin_rows

    assert data["rt_barcode_counts"]["P01"][0] == {'row': 'B', 'col': '1', 'frequency': 2048}

    assert umap_data["default_color_key"] == "log1p_n_genes_by_counts"
    assert [option["key"] for option in umap_data["color_options"]] == [
        "plain",
        "log1p_n_genes_by_counts",
        "log1p_total_counts",
        "pct_counts_mt",
    ]
    assert "zfish-hash" in umap_data["samples"]
    umap_sample = umap_data["samples"]["zfish-hash"]
    assert umap_sample["status"] == "ok"
    assert umap_sample["feature"] == "GeneFull_Ex50pAS"
    assert umap_sample["message"] == ""
    assert umap_sample["n_cells_plot"] > 0
    assert len(umap_sample["x"]) == len(umap_sample["y"]) == umap_sample["n_cells_plot"]
    assert umap_sample["n_cells_input"] >= umap_sample["n_cells_plot"]
    assert set(umap_sample["metrics"]) == {
        "log1p_n_genes_by_counts",
        "log1p_total_counts",
        "pct_counts_mt",
    }
    assert all(len(values) == umap_sample["n_cells_plot"] for values in umap_sample["metrics"].values())
