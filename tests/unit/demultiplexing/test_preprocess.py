import pytest
import pathlib
import workflow.rules.scripts.demultiplexing.preprocess as preprocess
import pandas as pd


def write_tsv(path, header, rows):
    pathlib.Path(path).write_text("\t".join(header) + "\n" + "\n".join("\t".join(map(str, r)) for r in rows) + "\n")


@pytest.fixture
def test_config(tmp_path) -> dict:
    # Minimal samplesheet
    samples_path = tmp_path / "samples.tsv"
    write_tsv(samples_path,
              header=["path_reads", "experiment_name", "p5", "p7", "rt", "sample_name", "species", "n_expected_cells"],
              rows=[["run", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample1", "mouse", "10000"]])

    # Minimal barcodes file
    barcodes_path = tmp_path / "barcodes.tsv"
    write_tsv(barcodes_path, header=["type", "barcode", "sequence"],
              rows=[["ligation", "LIG1", "ACTTGATTGT"],
                    ["p5", "A01", "CGTTCTATCA"],
                    ["p7", "A01", "CTAAGCCTTG"],
                    ["rt", "P01-B02", "GCCGCAACGA"],
                    ])

    return {"path_samples": str(samples_path),
            "path_barcodes": str(barcodes_path),
            "species": {"mouse": {"genome": "", "genome_gtf": "", "star_index": ""}}}


def test_get_samples_deduplicated_sequencing_names(test_config: dict):
    write_tsv(test_config["path_samples"],
              header=["path_reads", "experiment_name", "p5", "p7", "rt", "sample_name", "species", "n_expected_cells"],
              rows=[
                  ["/path/r1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample1", "mouse", "10000"],
                  ["/other/r1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample2", "mouse", "10000"],
                  ["/path/r1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample3", "mouse", "10000"],
                  ["/x/r1", "exp2", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample4", "mouse", "10000"],
                  ["/other/r2", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample5", "mouse", "10000"],
                  ["/path/r1", "exp2", "A02:H02", "H01:H12", "P01-A01:P01-D12", "sample6", "mouse", "10000"],
                  ["/other/r1", "exp", "A01:B01", "H06:H12", "P01-A01:P01-D12", "sample7", "mouse", "10000"],
              ], )
    samples = preprocess.get_samples(test_config)
    assert samples["sequencing_name"][0] == "r1"  # exp/r1: first r1 in exp, so ok as is
    assert samples["sequencing_name"][
               1] == "r1_1"  # exp/r1_1: second r1 in exp & has different path (/other/r1) to first one, so renamed
    assert samples["sequencing_name"][2] == "r1"  # exp/r1: repeat of first r1 path in exp, so ok as is
    assert samples["sequencing_name"][3] == "r1"  # exp2/r1: different experiment, so ok as is
    assert samples["sequencing_name"][4] == "r2"  # exp/r2: first r2 in exp, so ok as is
    assert samples["sequencing_name"][5] == "r1_1"  # exp2/r1_1: second r1 in exp2 with different path, so renamed
    assert samples["sequencing_name"][6] == "r1_1"  # exp1/r1_1: same path & exp as sample 2


def test_get_samples_path_reads_with_multiple_paths(test_config: dict):
    write_tsv(
        test_config["path_samples"],
        header=["path_reads", "experiment_name", "p5", "p7", "rt", "sample_name", "species", "n_expected_cells"],
        rows=[
            # single path, no semicolon -> single row
            ["path/r1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s1", "mouse", "10000"],
            # single path, trailing semicolon -> single row
            ["/path/r2;", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s2", "mouse", "10000"],
            # two paths separated by a semicolon with trailing slashes -> two rows without trailing slashes
            ["/path/a/;/path/b/", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000"],
            # four paths separated by semicolons -> four rows
            ["/path/a1;/path/a2;/path/a3;/path/a4", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse",
             "10000"],
            # duplicate paths in same cell -> single row with single path
            ["c://dup;c://dup", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s4", "mouse", "10000"],
            # whitespace around tokens -> single rows with trimmed paths
            [" /ws1 ;  /ws2  ", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s5", "mouse", "10000"],
            # empty tokens from double semicolons + trailing -> two rows with trimmed paths
            [";/x;;/y;", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s6", "mouse", "10000"],
        ],
    )

    expected_samples = pd.DataFrame([
        ["path/r1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s1", "mouse", "10000", "r1"],
        ["/path/r2", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s2", "mouse", "10000", "r2"],
        ["/path/a", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "a"],
        ["/path/b", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "b"],
        ["/path/a1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "a1"],
        ["/path/a2", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "a2"],
        ["/path/a3", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "a3"],
        ["/path/a4", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s3", "mouse", "10000", "a4"],
        ["c://dup", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s4", "mouse", "10000", "dup"],
        ["/ws1", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s5", "mouse", "10000", "ws1"],
        ["/ws2", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s5", "mouse", "10000", "ws2"],
        ["/x", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s6", "mouse", "10000", "x"],
        ["/y", "exp", "A02:H02", "H01:H12", "P01-A01:P01-D12", "s6", "mouse", "10000", "y"],
    ], columns=["path_reads", "experiment_name", "p5", "p7", "rt", "sample_name", "species", "n_expected_cells", "sequencing_name"])

    samples = preprocess.get_samples(test_config)
    pd.testing.assert_frame_equal(samples.reset_index(drop=True), expected_samples, check_dtype=False)


def test_get_samples_ignores_comment_lines(test_config: dict):
    pathlib.Path(test_config["path_samples"]).write_text(
        "\n".join(
            [
                "# comment line should be ignored",
                "path_reads\texperiment_name\tp5\tp7\trt\tsample_name\tspecies\tn_expected_cells",
                "/path/r1\texp\tA02:H02\tH01:H12\tP01-A01:P01-D12\tsample1\tmouse\t10000",
                "# second comment should also be ignored",
                "/path/r2\texp\tA02:H02\tH01:H12\tP01-A01:P01-D12\tsample2\tmouse\t10000",
            ]
        )
        + "\n"
    )

    samples = preprocess.get_samples(test_config)

    assert len(samples) == 2
    assert set(samples["sample_name"]) == {"sample1", "sample2"}


@pytest.mark.parametrize(
    "lane_config,expected",
    [
        (None, None),
        ("", None),
        ("2", ["2"]),
        ("1,2", ["1", "2"]),
        ("1, 2, 03", ["1", "2", "3"]),
    ],
)
def test_parse_sequencing_lanes_valid(lane_config, expected):
    assert preprocess.parse_sequencing_lanes(lane_config) == expected


@pytest.mark.parametrize("lane_config", ["A", "0", "1+B", "1,,2", [1, 2], 2, {"x": 1}])
def test_parse_sequencing_lanes_invalid(lane_config):
    with pytest.raises(ValueError):
        preprocess.parse_sequencing_lanes(lane_config)


def test_get_configured_sequencing_lanes_global_setting():
    config = {"settings": {"sequencing_lanes": "2,3"}}
    assert preprocess.get_configured_sequencing_lanes(config) == ["2", "3"]


def test_get_configured_sequencing_lanes_dict_is_invalid():
    config = {"settings": {"sequencing_lanes": {"default": "2", "run2": "3+4"}}}
    with pytest.raises(ValueError):
        preprocess.get_configured_sequencing_lanes(config)
