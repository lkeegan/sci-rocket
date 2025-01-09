from pathlib import Path
import pytest


@pytest.mark.parametrize("sample", ["ZAe-10hpf-28", "ZAe-14hpf-28"])
def test_alignment_output_files_exist(sample: str):
    alignment_path = Path("Drer.ZAe") / "alignment"
    assert alignment_path.exists()
    assert (alignment_path / f"{sample}_Zebrafish_Aligned.sortedByCoord.out.bam").exists()
    assert (alignment_path / f"{sample}_Zebrafish_Aligned.sortedByCoord.out.bam.bai").exists()
    assert (alignment_path / f"{sample}_Zebrafish_Solo.out").is_dir()
