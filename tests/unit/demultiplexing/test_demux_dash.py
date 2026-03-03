import pytest
import pandas as pd

from workflow.rules.scripts.demultiplexing.demux_dash import (
    calculate_hashing_summary,
    parse_summary_metrics,
    resolve_solo_feature_paths,
)


def test_calculate_hashing_summary_matches_expected_aggregation():
    df_hashing = pd.DataFrame(
        [
            # sample_1, cell_a: ratio = 10 / 2 = 5
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 10},
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 2},
            # sample_1, cell_b: only one hash, ratio = NA
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H3", "cell_barcode": "cell_b", "count": 8},
            # sample_1, cell_c: ratio = 9 / 3 = 3
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H1", "cell_barcode": "cell_c", "count": 9},
            {"experiment_name": "exp1", "sample_name": "sample_1", "hashing_name": "H2", "cell_barcode": "cell_c", "count": 3},
            # sample_2 reuses cell_a barcode to confirm grouping is sample-aware.
            {"experiment_name": "exp1", "sample_name": "sample_2", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 6},
            {"experiment_name": "exp1", "sample_name": "sample_2", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 3},
        ]
    )

    summary = calculate_hashing_summary(df_hashing)
    summary_by_sample = {row["sample_name"]: row for row in summary}

    assert set(summary_by_sample) == {"sample_1", "sample_2"}

    sample_1 = summary_by_sample["sample_1"]
    assert sample_1["count_total"] == 32
    assert sample_1["cells_passing"] == 2
    assert sample_1["fraction_passing"] == pytest.approx(2 / 3)
    assert sample_1["mean_count"] == pytest.approx((12 + 8 + 12) / 3)
    assert sample_1["median_ratio"] == pytest.approx(4.0)
    assert sample_1["mean_ratio"] == pytest.approx(4.0)

    sample_2 = summary_by_sample["sample_2"]
    assert sample_2["count_total"] == 9
    assert sample_2["cells_passing"] == 0
    assert sample_2["fraction_passing"] == pytest.approx(0.0)
    assert sample_2["mean_count"] == pytest.approx(9.0)
    assert sample_2["median_ratio"] == pytest.approx(2.0)
    assert sample_2["mean_ratio"] == pytest.approx(2.0)


def test_calculate_hashing_summary_includes_samples_without_cell_rows():
    df_hashing = pd.DataFrame(
        [
            {"sample_name": "sample_with_reads", "hashing_name": "H1", "cell_barcode": "cell_a", "count": 4},
            {"sample_name": "sample_with_reads", "hashing_name": "H2", "cell_barcode": "cell_a", "count": 2},
        ]
    )

    summary = calculate_hashing_summary(df_hashing, sample_names=["sample_with_reads", "sample_empty"])
    summary_by_sample = {row["sample_name"]: row for row in summary}

    assert set(summary_by_sample) == {"sample_with_reads", "sample_empty"}

    sample_empty = summary_by_sample["sample_empty"]
    assert sample_empty["count_total"] == 0
    assert sample_empty["cells_passing"] == 0
    assert sample_empty["fraction_passing"] is None
    assert sample_empty["mean_count"] is None
    assert sample_empty["median_ratio"] is None
    assert sample_empty["mean_ratio"] is None


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
