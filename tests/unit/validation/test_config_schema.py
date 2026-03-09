from pathlib import Path

import pytest
from snakemake.exceptions import WorkflowError
from snakemake.utils import validate


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "workflow" / "schemas" / "config.schema.yaml"


def minimal_valid_config() -> dict:
    return {
        "path_samples": "samples.tsv",
        "path_barcodes": "barcodes.tsv",
        "dir_output": "out",
        "species": {
            "mouse": {
                "genome": "genome.fa",
                "genome_gtf": "genes.gtf",
            }
        },
    }


def test_validate_applies_defaults_for_optional_fields():
    config = minimal_valid_config()

    validate(config, schema=str(SCHEMA_PATH))

    assert config["species"]["mouse"]["star_index"] == ""
    assert config["settings"]["scatter_fastq_split"] == 10
    assert config["settings"]["sequencing_lanes"] == ""
    assert config["settings"]["star_solo_features"] == "GeneFull_Ex50pAS"
    assert "star_align_mem_mb" not in config["settings"]
    assert config["path_mgp"] == ""
    assert "url_repeatmasker" in config


@pytest.mark.parametrize("required_key", [
    "path_samples",
    "path_barcodes",
    "dir_output",
    "species",
])
def test_validate_requires_required_top_level_keys(required_key: str):
    config = minimal_valid_config()
    del config[required_key]

    with pytest.raises(WorkflowError, match=required_key):
        validate(config, schema=str(SCHEMA_PATH))


def test_validate_rejects_unknown_top_level_keys():
    config = minimal_valid_config()
    config["unknown_key"] = "x"

    with pytest.raises(WorkflowError, match="Additional properties are not allowed"):
        validate(config, schema=str(SCHEMA_PATH))


def test_validate_rejects_invalid_scatter_fastq_split():
    config = minimal_valid_config()
    config["settings"] = {"scatter_fastq_split": 0}

    with pytest.raises(WorkflowError, match="less than the minimum of 1"):
        validate(config, schema=str(SCHEMA_PATH))


def test_validate_rejects_invalid_sequencing_lanes_format():
    config = minimal_valid_config()
    config["settings"] = {"sequencing_lanes": "1+B"}

    with pytest.raises(WorkflowError, match="does not match"):
        validate(config, schema=str(SCHEMA_PATH))


def test_validate_rejects_string_star_align_mem_mb():
    config = minimal_valid_config()
    config["settings"] = {"star_align_mem_mb": "65536"}

    with pytest.raises(WorkflowError, match="'65536' is not of type 'integer'"):
        validate(config, schema=str(SCHEMA_PATH))
