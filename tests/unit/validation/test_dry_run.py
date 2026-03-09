import os
import subprocess
from pathlib import Path


SNAKEFILE = Path(__file__).resolve().parents[3] / "workflow" / "Snakefile"


def run_snakemake_dry_run(config_path: Path, workdir: Path, cache_dir: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache_dir)

    return subprocess.run(
        [
            "snakemake",
            "--dry-run",
            "--cores",
            "1",
            "-s",
            str(SNAKEFILE),
            "--configfile",
            str(config_path),
            "-d",
            str(workdir),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def write_minimal_samples_and_barcodes(tmp_path: Path) -> tuple[Path, Path]:
    run_dir = tmp_path / "run1"
    run_dir.mkdir()

    samples_path = tmp_path / "samples.tsv"
    samples_path.write_text(
        "path_reads\texperiment_name\tp5\tp7\trt\tsample_name\tspecies\tn_expected_cells\n"
        f"{run_dir}\texp1\tA01\tA01\tP01-A01\ts1\tmouse\t1000\n"
    )

    barcodes_path = tmp_path / "barcodes.tsv"
    barcodes_path.write_text(
        "type\tbarcode\tsequence\n"
        "ligation\tLIG1\tACTTGATTGT\n"
        "p5\tA01\tCGTTCTATCA\n"
        "p7\tA01\tCTAAGCCTTG\n"
        "rt\tP01-A01\tGCCGCAACGA\n"
    )

    return samples_path, barcodes_path


def test_snakemake_dry_run_reports_schema_validation_errors(tmp_path):
    config_path = tmp_path / "invalid_config.yaml"
    config_path.write_text("settings:\n  scatter_fastq_split: 0\n")

    result = run_snakemake_dry_run(
        config_path=config_path,
        workdir=tmp_path,
        cache_dir=tmp_path / "cache",
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Error validating config file." in combined_output
    assert "scatter_fastq_split" in combined_output


def test_snakemake_dry_run_accepts_valid_config(tmp_path):
    samples_path, barcodes_path = write_minimal_samples_and_barcodes(tmp_path)
    genome_path = tmp_path / "genome.fa"
    gtf_path = tmp_path / "genes.gtf"
    genome_path.write_text(">chr1\nACGT\n")
    gtf_path.write_text("chr1\ttest\texon\t1\t4\t.\t+\t.\tgene_id \"g1\";\n")

    config_path = tmp_path / "valid_config.yaml"
    config_path.write_text(
        f'path_samples: "{samples_path}"\n'
        f'path_barcodes: "{barcodes_path}"\n'
        f'dir_output: "{tmp_path / "out"}"\n'
        "species:\n"
        "  mouse:\n"
        f'    genome: "{genome_path}"\n'
        f'    genome_gtf: "{gtf_path}"\n'
    )

    result = run_snakemake_dry_run(
        config_path=config_path,
        workdir=tmp_path,
        cache_dir=tmp_path / "cache",
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "This was a dry-run" in combined_output


def test_snakemake_dry_run_reports_missing_reference_paths(tmp_path):
    samples_path, barcodes_path = write_minimal_samples_and_barcodes(tmp_path)
    gtf_path = tmp_path / "genes.gtf"
    gtf_path.write_text("chr1\ttest\texon\t1\t4\t.\t+\t.\tgene_id \"g1\";\n")

    config_path = tmp_path / "missing_reference_config.yaml"
    config_path.write_text(
        f'path_samples: "{samples_path}"\n'
        f'path_barcodes: "{barcodes_path}"\n'
        f'dir_output: "{tmp_path / "out"}"\n'
        "species:\n"
        "  mouse:\n"
        f'    genome: "{tmp_path / "missing.fa"}"\n'
        f'    genome_gtf: "{gtf_path}"\n'
    )

    result = run_snakemake_dry_run(
        config_path=config_path,
        workdir=tmp_path,
        cache_dir=tmp_path / "cache",
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Config path validation failed" in combined_output
    assert "species.mouse.genome does not exist or is not a file" in combined_output
