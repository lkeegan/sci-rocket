from pathlib import Path
import pytest


@pytest.mark.parametrize("sample", ["ZAe-10hpf-28", "ZAe-14hpf-28"])
def test_demux_output_files_exist(sample: str):
    demux_path = Path(__file__).parent.parent / "output" / "Drer.ZAe" / "demux_reads"
    assert demux_path.exists()
    assert (demux_path / f"{sample}_R1.fastq.gz").exists()
    assert (demux_path / f"{sample}_R2.fastq.gz").exists()