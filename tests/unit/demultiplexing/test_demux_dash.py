import pytest
import pandas as pd

from workflow.scripts.demultiplexing.build_umap_data_js import build_umap_payload
from workflow.scripts.demultiplexing.demux_dash import (
    HASH_COUNT_BIN_LABELS,
    calculate_hashing_bin_summary,
    calculate_hashing_summary,
    calculate_hashing_summary_filtered,
    parse_summary_metrics,
    resolve_solo_feature_paths,
)


def test_calculate_hashing_summary_matches_expected_aggregation():
    df_hashing = pd.DataFrame(
        [
            # sample_1, cell_a: ratio = 10 / 2 = 5
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 10, "n_umi": 6},
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 2, "n_umi": 2},
            # sample_1, cell_b: only one hash, ratio = 8 / 1 = 8 (pseudocount)
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H3", "cell_barcode": "cell_b", "count": 8, "n_umi": 4},
            # sample_1, cell_c: ratio = 9 / 3 = 3
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_c", "count": 9, "n_umi": 5},
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_c", "count": 3, "n_umi": 1},
            # sample_2 reuses cell_a barcode to confirm grouping is sample-aware.
            {"experiment_name": "exp1", "sample_name": "sample_2", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 6, "n_umi": 3},
            {"experiment_name": "exp1", "sample_name": "sample_2", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 3, "n_umi": 2},
        ]
    )

    summary = calculate_hashing_summary(df_hashing)
    summary_by_sample = {row["sample_name"]: row for row in summary}

    assert set(summary_by_sample) == {"sample_1", "sample_2"}

    sample_1 = summary_by_sample["sample_1"]
    assert sample_1["hash_count_total"] == 32
    assert sample_1["hash_umi_total"] == 15
    assert sample_1["cells_passing"] == 3
    assert sample_1["fraction_passing"] == pytest.approx(1.0)
    assert sample_1["mean_hash_count"] == pytest.approx((12 + 8 + 12) / 3)
    assert sample_1["median_hash_ratio"] == pytest.approx(5.0)
    assert sample_1["mean_hash_ratio"] == pytest.approx((5 + 8 + 3) / 3)
    assert sample_1["total_cells"] == 3

    sample_2 = summary_by_sample["sample_2"]
    assert sample_2["hash_count_total"] == 9
    assert sample_2["hash_umi_total"] == 3
    assert sample_2["cells_passing"] == 0
    assert sample_2["fraction_passing"] == pytest.approx(0.0)
    assert sample_2["mean_hash_count"] == pytest.approx(9.0)
    assert sample_2["median_hash_ratio"] == pytest.approx(2.0)
    assert sample_2["mean_hash_ratio"] == pytest.approx(2.0)
    assert sample_2["total_cells"] == 1


def test_calculate_hashing_summary_includes_samples_without_cell_rows():
    df_hashing = pd.DataFrame(
        [
            {"sample_name": "sample_with_reads", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 4, "n_umi": 2},
            {"sample_name": "sample_with_reads", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 2, "n_umi": 1},
        ]
    )

    summary = calculate_hashing_summary(df_hashing, sample_names=["sample_with_reads", "sample_empty"])
    summary_by_sample = {row["sample_name"]: row for row in summary}

    assert set(summary_by_sample) == {"sample_with_reads", "sample_empty"}

    sample_empty = summary_by_sample["sample_empty"]
    assert sample_empty["hash_count_total"] == 0
    assert sample_empty["hash_umi_total"] == 0
    assert sample_empty["cells_passing"] == 0
    assert sample_empty["fraction_passing"] is None
    assert sample_empty["mean_hash_count"] is None
    assert sample_empty["median_hash_ratio"] is None
    assert sample_empty["mean_hash_ratio"] is None
    assert sample_empty["total_cells"] == 0


def test_calculate_hashing_summary_filtered_uses_hash_umi_total_threshold():
    df_hashing = pd.DataFrame(
        [
            # Filtered out (top n_umi = 4).
            {"sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 10, "n_umi": 4},
            {"sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 1, "n_umi": 1},
            # Kept (top n_umi = 5).
            {"sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_b", "count": 6, "n_umi": 5},
            {"sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_b", "count": 3, "n_umi": 2},
        ]
    )

    summary = calculate_hashing_summary_filtered(df_hashing, sample_names=["sample_1"])
    sample_1 = summary[0]

    assert sample_1["total_cells"] == 1
    assert sample_1["hash_count_total"] == 9
    assert sample_1["hash_umi_total"] == 5
    assert sample_1["mean_hash_count"] == pytest.approx(9.0)
    assert sample_1["cells_passing"] == 0
    assert sample_1["fraction_passing"] == pytest.approx(0.0)


def test_calculate_hashing_bin_summary_returns_all_bins_with_labels():
    df_hashing = pd.DataFrame(
        [
            # sample_1, cell_a -> bin 1-10, passing
            {"sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 7, "n_umi": 6},
            {"sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 1, "n_umi": 1},
            # sample_1, cell_b -> bin 21-30, not passing
            {"sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_b", "count": 15, "n_umi": 5},
            {"sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_b", "count": 10, "n_umi": 2},
            # sample_2, cell_c -> bin 100+, passing
            {"sample_name": "sample_2", "hashing_name": "H1", "cell_barcode": "cell_c", "count": 120, "n_umi": 8},
            {"sample_name": "sample_2", "hashing_name": "H2", "cell_barcode": "cell_c", "count": 10, "n_umi": 3},
        ]
    )

    rows = calculate_hashing_bin_summary(df_hashing, sample_names=["sample_1", "sample_2"])
    assert len(rows) == 2 * len(HASH_COUNT_BIN_LABELS)

    lookup = {(row["sample_name"], row["count_bin"]): row for row in rows}

    sample1_1_10 = lookup[("sample_1", "1-10")]
    assert sample1_1_10["n_cells"] == 1
    assert sample1_1_10["fraction_passing"] == pytest.approx(1.0)
    assert sample1_1_10["label"] == "100% (n=1)"

    sample1_21_30 = lookup[("sample_1", "21-30")]
    assert sample1_21_30["n_cells"] == 1
    assert sample1_21_30["fraction_passing"] == pytest.approx(0.0)
    assert sample1_21_30["label"] == "0% (n=1)"

    sample1_100_plus = lookup[("sample_1", "100+")]
    assert sample1_100_plus["n_cells"] == 0
    assert sample1_100_plus["fraction_passing"] is None
    assert sample1_100_plus["label"] == "·"

    sample2_100_plus = lookup[("sample_2", "100+")]
    assert sample2_100_plus["n_cells"] == 1
    assert sample2_100_plus["fraction_passing"] == pytest.approx(1.0)
    assert sample2_100_plus["label"] == "100% (n=1)"


def test_parse_summary_metrics_supports_gene_feature_labels(tmp_path):
    summary_path = tmp_path / "Summary.csv"
    summary_path.write_text(
        "\n".join(
            [
                "Number of Reads,100",
                "Sequencing Saturation,0.5",
                "Reads Mapped to Genome: Unique+Multiple,0.9",
                "Reads Mapped to Genome: Unique,0.8",
                "Reads Mapped to Gene: Unique+Multiple Gene,0.7",
                "Reads Mapped to Gene: Unique Gene,0.6",
                "Estimated Number of Cells,12",
                "Mean Reads per Cell,50",
                "Mean UMI per Cell,20",
                "Mean Gene per Cell,11",
            ]
        )
    )

    metrics = parse_summary_metrics(summary_path)

    assert metrics["total_reads"] == 100
    assert metrics["sequencing_saturation"] == pytest.approx(0.5)
    assert metrics["perc_mapped_reads_genome"] == pytest.approx(0.9)
    assert metrics["perc_unique_reads_genome_unique"] == pytest.approx(0.8)
    assert metrics["perc_mapped_reads_gene"] == pytest.approx(0.7)
    assert metrics["perc_unique_reads_gene_unique"] == pytest.approx(0.6)
    assert metrics["estimated_cells"] == 12
    assert metrics["mean_reads_per_cell"] == 50
    assert metrics["mean_umi_per_cell"] == 20
    assert metrics["mean_genes_per_cell"] == 11


def test_resolve_solo_feature_paths_falls_back_to_gene(tmp_path):
    path_star = tmp_path / "alignment"
    sample = "sample_a"
    solo_dir = path_star / f"{sample}_Zebrafish_Solo.out"
    gene_dir = solo_dir / "Gene"
    (gene_dir / "filtered").mkdir(parents=True)

    (gene_dir / "Summary.csv").write_text("Number of Reads,1\n")
    (gene_dir / "CellReads.stats").write_text("CB\tcbMatch\tgenomeU\tgenomeM\texonic\tintronic\texonicAS\tintronicAS\tmito\nA\t1\t0\t0\t0\t0\t0\t0\t0\n")
    (gene_dir / "filtered" / "barcodes.tsv").write_text("A\n")

    resolved = resolve_solo_feature_paths(path_star, sample)

    assert resolved["feature"] == "Gene"
    assert resolved["summary"] == gene_dir / "Summary.csv"
    assert resolved["cellreads"] == gene_dir / "CellReads.stats"
    assert resolved["filtered_barcodes"] == gene_dir / "filtered" / "barcodes.tsv"


def test_resolve_solo_feature_paths_prefers_configured_feature(tmp_path):
    path_star = tmp_path / "alignment"
    sample = "sample_a"
    solo_dir = path_star / f"{sample}_Zebrafish_Solo.out"

    for feature in ("GeneFull_Ex50pAS", "Gene"):
        feature_dir = solo_dir / feature
        (feature_dir / "filtered").mkdir(parents=True)
        (feature_dir / "Summary.csv").write_text("Number of Reads,1\n")
        (feature_dir / "CellReads.stats").write_text(
            "CB\tcbMatch\tgenomeU\tgenomeM\texonic\tintronic\texonicAS\tintronicAS\tmito\n"
            "A\t1\t0\t0\t0\t0\t0\t0\t0\n"
        )
        (feature_dir / "filtered" / "barcodes.tsv").write_text("A\n")

    resolved = resolve_solo_feature_paths(path_star, sample, preferred_features=["Gene"])

    assert resolved["feature"] == "Gene"
    assert resolved["summary"] == solo_dir / "Gene" / "Summary.csv"


def test_resolve_solo_feature_paths_requires_filtered_matrix_for_umap(tmp_path):
    path_star = tmp_path / "alignment"
    sample = "sample_a"
    solo_dir = path_star / f"{sample}_Zebrafish_Solo.out"

    gene_dir = solo_dir / "Gene"
    (gene_dir / "filtered").mkdir(parents=True)
    (gene_dir / "Summary.csv").write_text("Number of Reads,1\n")
    (gene_dir / "CellReads.stats").write_text(
        "CB\tcbMatch\tgenomeU\tgenomeM\texonic\tintronic\texonicAS\tintronicAS\tmito\n"
        "A\t1\t0\t0\t0\t0\t0\t0\t0\n"
    )
    (gene_dir / "filtered" / "barcodes.tsv").write_text("A\n")

    gene_full_dir = solo_dir / "GeneFull_Ex50pAS"
    (gene_full_dir / "filtered").mkdir(parents=True)
    (gene_full_dir / "Summary.csv").write_text("Number of Reads,1\n")
    (gene_full_dir / "CellReads.stats").write_text(
        "CB\tcbMatch\tgenomeU\tgenomeM\texonic\tintronic\texonicAS\tintronicAS\tmito\n"
        "A\t1\t0\t0\t0\t0\t0\t0\t0\n"
    )
    (gene_full_dir / "filtered" / "barcodes.tsv").write_text("A\n")
    (gene_full_dir / "filtered" / "features.tsv").write_text("ENSG0001\tGeneA\tGene Expression\n")
    (gene_full_dir / "filtered" / "matrix.mtx").write_text(
        "%%MatrixMarket matrix coordinate integer general\n1 1 1\n1 1 1\n"
    )

    resolved = resolve_solo_feature_paths(
        path_star,
        sample,
        preferred_features=["Gene"],
        require_filtered_matrix=True,
    )

    assert resolved["feature"] == "GeneFull_Ex50pAS"
    assert resolved["filtered_matrix"] == gene_full_dir / "filtered" / "matrix.mtx"


def test_build_umap_payload_collects_sample_payloads(tmp_path):
    sample_a = tmp_path / "sample_a.json"
    sample_b = tmp_path / "sample_b.json"
    sample_a.write_text(
        '{"sample_name":"sample_a","status":"ok","feature":"Gene","n_cells_input":3,"n_cells_plot":3,"x":[0.1],"y":[0.2],"metrics":{"log1p_total_counts":[1.0]}}'
    )
    sample_b.write_text(
        '{"sample_name":"sample_b","status":"unavailable","feature":"Gene","n_cells_input":0,"n_cells_plot":0,"x":[],"y":[],"metrics":{}}'
    )

    payload = build_umap_payload([str(sample_a), str(sample_b)])

    assert payload["default_color_key"] == "log1p_n_genes_by_counts"
    assert [option["key"] for option in payload["color_options"]] == [
        "plain",
        "log1p_n_genes_by_counts",
        "log1p_total_counts",
        "pct_counts_mt",
    ]
    assert set(payload["samples"]) == {"sample_a", "sample_b"}
    assert payload["samples"]["sample_a"]["feature"] == "Gene"
