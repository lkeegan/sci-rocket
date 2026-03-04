from pathlib import Path
import pickle
import pytest


@pytest.mark.parametrize("sample", ["ZAe-10hpf-28", "ZAe-14hpf-28"])
def test_demux_output_files_exist(sample: str):
    demux_path = Path(__file__).parent.parent / "output" / "fastq_from_aviti_one_run" / "demux_reads"
    assert demux_path.exists()
    assert (demux_path / f"{sample}_R1.fastq.gz").exists()
    assert (demux_path / f"{sample}_R2.fastq.gz").exists()


@pytest.mark.parametrize("experiment", ["fastq_from_aviti_one_run", "fastq_from_aviti_two_runs"])
def test_qc_pickle_has_expected_max_r2_read_length(experiment: str):
    test_root = Path(__file__).parent.parent
    experiment_path = test_root / "output" / experiment
    demux_path = experiment_path / "demux_reads"
    path_qc = demux_path / f"{experiment}_qc.pickle"

    assert path_qc.exists()

    with open(path_qc, "rb") as handle:
        qc = pickle.load(handle)

    assert qc["max_r2_read_length"] == 128
