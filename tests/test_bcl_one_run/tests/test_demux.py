from pathlib import Path
import pytest


@pytest.mark.parametrize("sample", ["zfish-hash"])
def test_demux_output_files_exist(sample: str):
    demux_path = Path(__file__).parent.parent / "output" / "zfish" / "demux_reads"
    assert demux_path.exists()
    assert (demux_path / f"{sample}_R1.fastq.gz").exists()
    assert (demux_path / f"{sample}_R2.fastq.gz").exists()