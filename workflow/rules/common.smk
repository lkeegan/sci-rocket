import sys

sys.path.append(f"{workflow.basedir}/scripts/demultiplexing")
import preprocess

# Extract unique samples and perform sanity checks on sample sheet and barcodes
samples_unique = preprocess.get_samples(config)

# Extract optional haplotyping samples (Mus musculus)
samples_unique_haplotyping = preprocess.get_haplotyping_samples(samples_unique)

# Constrain wildcard values to resolve downstream mixtures.
wildcard_constraints:
    **preprocess.get_wildcard_constraints(samples_unique, ["sequencing_name", "experiment_name", "sample_name"]),
    **preprocess.get_wildcard_constraints(samples_unique_haplotyping, ["strain1", "strain2"]),

# Output path helper.
dir_output = config["dir_output"].rstrip("/")
def out(p: str) -> str:
    return f"{dir_output}/{p.lstrip('/')}"
