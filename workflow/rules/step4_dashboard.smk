#   * Generate QC-dashboard (sci-dash). *
#
#   1. sci-dash:                Generates the QC-dashboard for a given sequencing run.
#############


rule sci_dash:
    input:
        lambda w: getsamples_sequencing(w),
        qc="{experiment_name}/demux_reads/{experiment_name}_qc.pickle"
    output:
        dash_folder=directory("{experiment_name}/sci-dash/"),
        dash_json="{experiment_name}/sci-dash/js/qc_data.js",
    threads: 1
    resources:
        mem_mb=1024 * 10,
    benchmark:
        "benchmarks/sci_dash_{experiment_name}.txt"
    params:
        # Optional hashing output. 
        metrics_hashing="{experiment_name}/hashing/{experiment_name}_hashing_metrics.tsv"
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
        --path_star {wildcards.experiment_name}/alignment/ \
        --path_hashing {params.metrics_hashing}

        # Remove all empty (leftover) folders.
        find ./{wildcards.experiment_name}/ -empty -type d -delete
        """
