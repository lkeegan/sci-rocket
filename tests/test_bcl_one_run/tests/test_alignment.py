from pathlib import Path
import pytest


@pytest.mark.parametrize("sample", ["zfish-hash"])
def test_alignment_output_files_exist(sample: str):
    alignment_path = Path(__file__).parent.parent / "output" / "zfish" / "alignment"
    assert alignment_path.exists()
    assert (alignment_path / f"{sample}_Zebrafish_Aligned.sortedByCoord.out.bam").exists()
    assert (alignment_path / f"{sample}_Zebrafish_Aligned.sortedByCoord.out.bam.bai").exists()
    assert (alignment_path / f"{sample}_Zebrafish_Solo.out").is_dir()
