#   * Generate sample-specific .fastq.gz files by demultiplexing the sci-seq barcodes. *
#
#   1. split_reads:                         Split R1 and R2 files into smaller files which will be handled in parallel.
#   3. demultiplex_fastq_split:             Demultiplex each split R1 and R2 file to generate sample-specific fastq.gz files (in parallel).
#   4. gather_demultiplexed_sequencing:     Combine the discarded and whitelist files (from multiple parallel jobs).
#   5. gather_demultiplexed_samples:        Combine the sample-specific fastq.gz files (from multiple parallel jobs).
#############

# ---- Split R1 and R2 files into smaller files which will be handled in parallel. ----
rule split_reads:
    input:
        out("{experiment_name}/raw_reads/Undetermined_S0_{read}_001.fastq.gz"),
    output:
        temp(
            scatter.fastq_split(
                out("{{experiment_name}}/raw_reads_split/{{read}}_{scatteritem}.fastq.gz")
            )
        ),
    wildcard_constraints:
        read="R[12]",
    threads: 5
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/split_{read}.txt")
    params:
        out_args=lambda w, output: " ".join(f"-o {path}" for path in output),
    conda:
        "envs/sci-rocket.yaml",        
    message:
        "Generating multiple evenly-sized {wildcards.read} chunks ({wildcards.experiment_name})."
    shell:
        """
        fastqsplitter -i {input} {params.out_args} -t 1 -c 1
        """

# ---- Helper for explicit per-sample scatter outputs in demultiplex_fastq_split. ----
def get_sample_names():
    return sorted(samples_unique["sample_name"].unique().tolist())


# ---- Demultiplex each split R1 and R2 file and emit sample-specific fastq.gz files. ----
rule demultiplex_fastq_split:
    input:
        R1=out("{experiment_name}/raw_reads_split/R1_{scatteritem}.fastq.gz"),
        R2=out("{experiment_name}/raw_reads_split/R2_{scatteritem}.fastq.gz"),
    output:
        discard_R1=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_R1_discarded.fastq.gz")),
        discard_R2=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_R2_discarded.fastq.gz")),
        discard_log=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/log_{experiment_name}_discarded_reads.tsv.gz")),
        qc=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_qc.pickle")),
        whitelist_p7=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_whitelist_p7.txt")),
        whitelist_p5=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_whitelist_p5.txt")),
        whitelist_ligation=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_whitelist_ligation.txt")),
        whitelist_rt=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_whitelist_rt.txt")),
        sample_R1=temp(expand(out("{{experiment_name}}/demux_reads_scatter/{{scatteritem}}/{sample_name}_R1.fastq.gz"), sample_name=get_sample_names())),
        sample_R2=temp(expand(out("{{experiment_name}}/demux_reads_scatter/{{scatteritem}}/{sample_name}_R2.fastq.gz"), sample_name=get_sample_names())),
    log:
        out("logs/step2_demultiplexing_reads/demultiplex_fastq_split_{experiment_name}_{scatteritem}.log"),
    threads: 1
    resources:
        mem_mb=1024 * 5,
    benchmark:
        out("benchmarks/{experiment_name}/demultiplex_fastq_split_{scatteritem}.txt")
    params:
        path_samples=config["path_samples"],
        path_barcodes=config["path_barcodes"],
        path_out=out("{experiment_name}/demux_reads_scatter/{scatteritem}"),
    conda:
        "envs/sci-rocket.yaml",
    message:
        "Demultiplexing the scattered .fastq.gz files ({wildcards.experiment_name})."
    shell:
        """
        python {workflow.basedir}/rules/scripts/demultiplexing/demux_rocket.py \
        --experiment_name {wildcards.experiment_name} \
        --samples {params.path_samples} \
        --barcodes {params.path_barcodes} \
        --r1 {input.R1} --r2 {input.R2} \
        --out {params.path_out} &> {log}
        """


rule gather_demultiplexed_sequencing:
    input:
        discard_R1=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_R1_discarded.fastq.gz")),
        discard_R2=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_R2_discarded.fastq.gz")),
        discard_log=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/log_{{experiment_name}}_discarded_reads.tsv.gz")),
        qc_pickles=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_qc.pickle")),
        whitelist_p7=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_whitelist_p7.txt")),
        whitelist_p5=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_whitelist_p5.txt")),
        whitelist_ligation=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_whitelist_ligation.txt")),
        whitelist_rt=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{experiment_name}}_whitelist_rt.txt")),
    output:
        R1_discarded=out("{experiment_name}/demux_reads/{experiment_name}_R1_discarded.fastq.gz"),
        R2_discarded=out("{experiment_name}/demux_reads/{experiment_name}_R2_discarded.fastq.gz"),
        discarded_log=out("{experiment_name}/demux_reads/log_{experiment_name}_discarded_reads.tsv.gz"),
        qc=out("{experiment_name}/demux_reads/{experiment_name}_qc.pickle"),
        whitelist_p7=out("{experiment_name}/demux_reads/{experiment_name}_whitelist_p7.txt"),
        whitelist_p5=out("{experiment_name}/demux_reads/{experiment_name}_whitelist_p5.txt"),
        whitelist_ligation=out("{experiment_name}/demux_reads/{experiment_name}_whitelist_ligation.txt"),
        whitelist_rt=out("{experiment_name}/demux_reads/{experiment_name}_whitelist_rt.txt"),
    log:
        out("logs/step2_demultiplexing_reads/gather_demultiplexed_sequencing_{experiment_name}.log"),
    threads: 1
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/gather_demultiplexed_sequencing.txt")
    params:
        path_demux_scatter=lambda w: out(f"{w.experiment_name}/demux_reads_scatter/")
    conda:
        "envs/sci-rocket.yaml",
    message:
        "Combining the discarded and whitelist files ({wildcards.experiment_name})."
    shell:
        """
        # Combine pickles.
        python {workflow.basedir}/rules/scripts/demultiplexing/demux_gather.py --path_demux_scatter {params.path_demux_scatter} --path_out {output.qc}

        # Combine the sequencing-specific R1/R2 discarded reads and logs.
        cat {input.discard_R1} > {output.R1_discarded}
        cat {input.discard_R2} > {output.R2_discarded}
        printf "read_name\tp5\tp7\tligation\trt\tumi\tsample_name\n" | gzip -c > {output.discarded_log}
        cat {input.discard_log} >> {output.discarded_log}

        # Move the whitelist files.
        cat {input.whitelist_p7} | sort -u > {output.whitelist_p7}
        cat {input.whitelist_p5} | sort -u > {output.whitelist_p5}
        cat {input.whitelist_ligation} | sort -u > {output.whitelist_ligation}
        cat {input.whitelist_rt} | sort -u > {output.whitelist_rt}
        """

rule gather_demultiplexed_samples:
    input:
        R1_scatter=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{sample_name}}_R1.fastq.gz")),
        R2_scatter=gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/{{sample_name}}_R2.fastq.gz")),
    output:
        R1=out("{experiment_name}/demux_reads/{sample_name}_R1.fastq.gz"),
        R2=out("{experiment_name}/demux_reads/{sample_name}_R2.fastq.gz"),
    threads: 1
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/gather_demultiplexed_samples_{sample_name}.txt")
    message:
        "Combining the sample-specific fastq.gz files ({wildcards.experiment_name})."
    shell:
        """
        # Combine files.
        cat {input.R1_scatter} > {output.R1}
        cat {input.R2_scatter} > {output.R2}
        """
