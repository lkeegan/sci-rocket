#   * Generate QC-dashboard (sci-dash). *
#
#   1. sci-dash:                Generates the QC-dashboard for a given sequencing run.
#############

# Get the samples for a given sequencing run (and sci-dash).
def getsamples_sequencing(wildcards):
    df = samples_unique[samples_unique["experiment_name"] == wildcards.experiment_name]
    files = [out(f"{s.experiment_name}/alignment/{s.sample_name}_{s.species}_Aligned.sortedByCoord.out.bam.bai") for s in df.itertuples(index=False, name='Row')]

    return files

rule sci_dash:
    input:
        lambda w: getsamples_sequencing(w),
        qc=out("{experiment_name}/demux_reads/{experiment_name}_qc.pickle"),
    output:
        dash_folder=directory(out("{experiment_name}/sci-dash/")),
        dash_json=out("{experiment_name}/sci-dash/js/qc_data.js"),
    threads: 1
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/sci_dash.txt")
    params:
        path_star=out("{experiment_name}/alignment/"),
        # Optional hashing output. 
        metrics_hashing=out("{experiment_name}/hashing/{experiment_name}_hashing_metrics.tsv"),
        benchmarks_folder=out("benchmarks/{experiment_name}")
    conda:
        "envs/sci-rocket.yaml",
    message:
        "Generating sci-dashboard report ({wildcards.experiment_name})."
    shell:
        """
        # Generate the sci-dashboard report.
        cp -R {workflow.basedir}/scirocket-dash/* {output.dash_folder}

        # Combine the sample-specific QC and STARSolo metrics.
        python3 {workflow.basedir}/rules/scripts/demultiplexing/demux_dash.py \
        --path_out {output.dash_json} \
        --path_pickle {input.qc} \
        --path_star {params.path_star} \
        --path_hashing {params.metrics_hashing} \
        --path_benchmarks {params.benchmarks_folder}

        # Remove all empty (leftover) folders.
        find {dir_output}/{wildcards.experiment_name}/ -empty -type d -delete
        """
