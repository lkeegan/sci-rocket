from pathlib import Path
import csv
import gzip
import pickle
from collections import Counter
import pytest


@pytest.mark.parametrize("sample", ["zfish-hash"])
def test_demux_output_files_exist(sample: str):
    demux_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "demux_reads"
    assert demux_path.exists()
    assert (demux_path / f"{sample}_R1.fastq.gz").exists()
    assert (demux_path / f"{sample}_R2.fastq.gz").exists()


def _read_whitelist(path: Path) -> set[str]:
    with open(path, "r", encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def _read_barcodes(path: Path, barcode_type: str) -> dict[str, str]:
    barcodes = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["type"] == barcode_type:
                barcodes[row["barcode"]] = row["sequence"].strip()
    return barcodes


def _reverse_complement(sequence: str) -> str:
    return sequence[::-1].translate(str.maketrans("ATCG", "TAGC"))


def _read_fastq_names(path: Path) -> list[str]:
    names = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i % 4 == 0:
                header = line.rstrip("\n")
                assert header.startswith("@")
                names.append(header[1:].split(" ", 1)[0])
    return names


def _count_fastq_reads(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return sum(1 for _ in handle) // 4


def _iter_fastq_sequences(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i % 4 == 1:
                yield line.rstrip("\n")


def test_demux_whitelists_subset_of_configured_barcodes():
    test_root = Path(__file__).parent.parent
    demux_path = test_root / "output" / "bcl_one_run" / "demux_reads"
    barcodes_path = test_root.parent / "barcodes_bcl.tsv"

    whitelist_p5 = _read_whitelist(demux_path / "bcl_one_run_whitelist_p5.txt")
    whitelist_p7 = _read_whitelist(demux_path / "bcl_one_run_whitelist_p7.txt")
    whitelist_ligation = _read_whitelist(demux_path / "bcl_one_run_whitelist_ligation.txt")
    whitelist_rt = _read_whitelist(demux_path / "bcl_one_run_whitelist_rt.txt")

    barcodes_p5 = _read_barcodes(barcodes_path, "p5")
    barcodes_p7 = _read_barcodes(barcodes_path, "p7")
    barcodes_ligation = _read_barcodes(barcodes_path, "ligation")
    barcodes_rt = _read_barcodes(barcodes_path, "rt")

    # Sample sheet uses p5 A03:H03, so include A03/H03 and exclude A01/A12.
    assert _reverse_complement(barcodes_p5["A03"]) in whitelist_p5
    assert _reverse_complement(barcodes_p5["H03"]) in whitelist_p5
    assert _reverse_complement(barcodes_p5["A01"]) not in whitelist_p5
    assert _reverse_complement(barcodes_p5["A12"]) not in whitelist_p5

    # Sample sheet uses p7 C01:C12, so include C01/C12 and exclude A01/B01.
    assert barcodes_p7["C01"] in whitelist_p7
    assert barcodes_p7["C12"] in whitelist_p7
    assert barcodes_p7["A01"] not in whitelist_p7
    assert barcodes_p7["B01"] not in whitelist_p7

    # Ligation whitelist should include all ligation barcodes from barcodes_bcl.tsv,
    # with 9nt barcodes padded to 10nt by appending "G".
    expected_ligation = {
        sequence if len(sequence) == 10 else sequence + "G"
        for sequence in barcodes_ligation.values()
    }
    assert whitelist_ligation == expected_ligation
    assert all(len(sequence) == 10 for sequence in whitelist_ligation)
    assert "ACTTGATTGT" in whitelist_ligation
    assert "GGCGTTAATG" in whitelist_ligation
    assert "GGCGTTAAT" not in whitelist_ligation
    assert "AAAAAAAAAA" not in whitelist_ligation

    # Sample sheet uses RT P01-{A..H}{01..07}, so include in-range and exclude out-of-range.
    assert barcodes_rt["P01-A01"] in whitelist_rt
    assert barcodes_rt["P01-H07"] in whitelist_rt
    assert barcodes_rt["P01-A08"] not in whitelist_rt
    assert barcodes_rt["P02-A01"] not in whitelist_rt


def test_discarded_logs_consistent_with_discarded_fastqs():
    demux_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "demux_reads"
    path_log = demux_path / "log_bcl_one_run_discarded_reads.tsv.gz"
    path_r1 = demux_path / "bcl_one_run_R1_discarded.fastq.gz"
    path_r2 = demux_path / "bcl_one_run_R2_discarded.fastq.gz"

    assert path_log.exists()
    assert path_r1.exists()
    assert path_r2.exists()

    with gzip.open(path_log, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames == ["read_name", "p5", "p7", "ligation", "rt", "umi", "sample_name"]
        rows = list(reader)

    assert len(rows) > 0
    # Merged discard logs should contain exactly one header row.
    assert all(row["read_name"] != "read_name" for row in rows)
    assert all(row["sample_name"] == "?" for row in rows)

    observed = {(row["p5"], row["p7"], row["ligation"], row["rt"]) for row in rows}
    # Explicit discarded examples from the fixture output.
    assert ("ACTACTTGAG", "TCTTGAGGTT", "LIG9", "CGCTCCTAAC") in observed
    assert ("G03", "C05", "LIG53", "GCAGACGCCT") in observed
    assert ("F03", "ATGGCAGATA", "LIG14", "P01-E02") in observed

    n_reads_r1 = _count_fastq_reads(path_r1)
    n_reads_r2 = _count_fastq_reads(path_r2)

    assert len(rows) == n_reads_r1 == n_reads_r2


def test_discarded_log_read_names_match_discarded_fastqs():
    demux_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "demux_reads"
    path_log = demux_path / "log_bcl_one_run_discarded_reads.tsv.gz"
    path_r1 = demux_path / "bcl_one_run_R1_discarded.fastq.gz"
    path_r2 = demux_path / "bcl_one_run_R2_discarded.fastq.gz"

    assert path_log.exists()
    assert path_r1.exists()
    assert path_r2.exists()

    with gzip.open(path_log, "rt", encoding="utf-8", newline="") as handle:
        log_names = [row["read_name"] for row in csv.DictReader(handle, delimiter="\t")]

    assert Counter(log_names) == Counter(_read_fastq_names(path_r1))
    assert Counter(log_names) == Counter(_read_fastq_names(path_r2))


def test_sample_fastqs_have_paired_reads_and_r1_length_48nt():
    test_root = Path(__file__).parent.parent
    demux_path = test_root / "output" / "bcl_one_run" / "demux_reads"
    samplesheet_path = test_root / "samplesheet.tsv"

    with open(samplesheet_path, "r", encoding="utf-8", newline="") as handle:
        sample_names = sorted({row["sample_name"] for row in csv.DictReader(handle, delimiter="\t")})

    for sample_name in sample_names:
        path_r1 = demux_path / f"{sample_name}_R1.fastq.gz"
        path_r2 = demux_path / f"{sample_name}_R2.fastq.gz"
        assert path_r1.exists()
        assert path_r2.exists()

        n_r1 = _count_fastq_reads(path_r1)
        n_r2 = _count_fastq_reads(path_r2)
        assert n_r1 == n_r2
        assert all(len(seq) == 48 for seq in _iter_fastq_sequences(path_r1))


def test_qc_pickle_consistent_with_demux_outputs():
    demux_path = Path(__file__).parent.parent / "output" / "bcl_one_run" / "demux_reads"
    path_qc = demux_path / "bcl_one_run_qc.pickle"
    path_log = demux_path / "log_bcl_one_run_discarded_reads.tsv.gz"
    path_discard_r1 = demux_path / "bcl_one_run_R1_discarded.fastq.gz"
    path_discard_r2 = demux_path / "bcl_one_run_R2_discarded.fastq.gz"
    path_sample_r1 = demux_path / "zfish-hash_R1.fastq.gz"
    path_sample_r2 = demux_path / "zfish-hash_R2.fastq.gz"

    assert path_qc.exists()
    assert path_log.exists()
    assert path_discard_r1.exists()
    assert path_discard_r2.exists()
    assert path_sample_r1.exists()
    assert path_sample_r2.exists()

    with open(path_qc, "rb") as handle:
        qc = pickle.load(handle)

    with gzip.open(path_log, "rt", encoding="utf-8", newline="") as handle:
        n_discard_log_rows = sum(1 for _ in csv.DictReader(handle, delimiter="\t"))
    n_discard_r1 = _count_fastq_reads(path_discard_r1)
    n_discard_r2 = _count_fastq_reads(path_discard_r2)
    n_sample_r1 = _count_fastq_reads(path_sample_r1)
    n_sample_r2 = _count_fastq_reads(path_sample_r2)

    assert qc["experiment_name"] == "bcl_one_run"
    assert qc["n_pairs_success"] + qc["n_pairs_failure"] == qc["n_pairs"]

    assert n_discard_log_rows == n_discard_r1 == n_discard_r2 == qc["n_pairs_failure"]
    assert n_sample_r1 == n_sample_r2
    assert qc["sample_success"]["zfish-hash"]["n_pairs_success"] == qc["n_pairs_success"]
    assert n_sample_r1 + qc["n_hashing"] == qc["n_pairs_success"]
    assert n_sample_r1 + n_discard_r1 + qc["n_hashing"] == qc["n_pairs"]
    assert qc["max_r2_read_length"] == 84


def test_qc_pickle_covers_all_samples_from_samplesheet():
    test_root = Path(__file__).parent.parent
    demux_path = test_root / "output" / "bcl_one_run" / "demux_reads"
    samplesheet_path = test_root / "samplesheet.tsv"
    path_qc = demux_path / "bcl_one_run_qc.pickle"

    assert path_qc.exists()

    with open(samplesheet_path, "r", encoding="utf-8", newline="") as handle:
        sample_names = {row["sample_name"] for row in csv.DictReader(handle, delimiter="\t")}
    with open(path_qc, "rb") as handle:
        qc = pickle.load(handle)

    assert set(qc["sample_success"].keys()) == sample_names
    assert sum(entry["n_pairs_success"] for entry in qc["sample_success"].values()) == qc["n_pairs_success"]
