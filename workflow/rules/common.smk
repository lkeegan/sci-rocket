def get_bcl2fastq_input(sequencing_name, experiment_name):
    """Return the path to the bcl file for a given sequencing run."""
    return samples_unique.query("sequencing_name == @sequencing_name & experiment_name == @experiment_name").path_bcl.values[0]


def get_folder_undetermined(sequencing_name, experiment_name):
    """Return the path to the folder containing the Undetermined fastq files (R1 and R2) for a given sequencing run from the samplesheet (path_fastq)."""
    if "path_fastq" not in samples_unique.columns:
        return ""
    else:
        if samples_unique.query("sequencing_name == @sequencing_name & experiment_name == @experiment_name").path_fastq.values[0] == "None":
            return ""
        else:
            # If yes, then use the path from the samplesheet.
            return samples_unique.query("sequencing_name == @sequencing_name & experiment_name == @experiment_name").path_fastq.values[0]


def get_sequencing_runs(experiment_name):
    """Return a list of sequencing runs."""
    return samples_unique.query("experiment_name == @experiment_name").sequencing_name.unique().tolist()


def get_expected_cells(wildcards):
    """Retrieve the expected no. of cells for a given (demultiplexed) sample."""
    x = samples_unique[samples_unique["sample_name"] == wildcards.sample_name]
    return x["n_expected_cells"].values[0]


def getsamples_sequencing(wildcards):
    """Get the samples for a given sequencing run (and sci-dash)."""
    x = samples_unique[samples_unique["experiment_name"] == wildcards.experiment_name]

    files = ["{experiment_name}/alignment/{sample_name}_{species}_Aligned.sortedByCoord.out.bam.bai".format(
        experiment_name=experiment_name,
        sample_name=sample_name,
        species=species,
    )
        for experiment_name, sample_name, species in zip(
            x["experiment_name"],
            x["sample_name"],
            x["species"],
        )]

    return files
