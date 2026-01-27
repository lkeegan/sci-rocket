#   * Generate sample-specific .fastq.gz files by demultiplexing the sci-seq barcodes. *
#
#   1. split_R1:                            Split the R1 file into smaller files which will be handled in parallel.
#   2. split_R2:                            Split the R2 file into smaller files which will be handled in parallel.
#   3. demultiplex_fastq_split:             Demultiplex each splitted R1 and R2 file to generate sample-specific fastq.gz files (in parallel).
#   4. gather_demultiplexed_sequencing:     Combine the discarded and whitelist files (from multiple parallel jobs).
#   5. gather_demultiplexed_samples:        Combine the sample-specific fastq.fz files (from multiple parallel jobs).
#############

# ---- Split R1 and R2 files into smaller files which will be handled in parallel. ----
rule split_R1:
    input:
        out("{experiment_name}/raw_reads/Undetermined_S0_R1_001.fastq.gz"),
    output:
        temp(
            scatter.fastq_split(
                out("{{experiment_name}}/raw_reads_split/R1_{scatteritem}.fastq.gz")
            )
        ),
    threads: 5
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/split_R1.txt")
    params:
        out=lambda w: [
            "-o " +
            out(f"{w.experiment_name}/raw_reads_split/R1_{i}-of-")
            + str(workflow._scatter["fastq_split"])
            + ".fastq.gz"
            for i in range(1, workflow._scatter["fastq_split"] + 1)
        ],
    conda:
        "envs/sci-rocket.yaml",        
    message:
        "Generating multiple evenly-sized R1 chunks ({wildcards.experiment_name})."
    shell:
        """
        fastqsplitter -i {input} {params.out} -t 1 -c 1
        """


rule split_R2:
    input:
        out("{experiment_name}/raw_reads/Undetermined_S0_R2_001.fastq.gz"),
    output:
        temp(
            scatter.fastq_split(
                out("{{experiment_name}}/raw_reads_split/R2_{scatteritem}.fastq.gz")
            )
        ),
    threads: 5
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/split_R2.txt")
    params:
        out=lambda w: [
            "-o " +
            out(f"{w.experiment_name}/raw_reads_split/R2_{i}-of-")
            + str(workflow._scatter["fastq_split"])
            + ".fastq.gz"
            for i in range(1, workflow._scatter["fastq_split"] + 1)
        ],
    conda:
        "envs/sci-rocket.yaml",
    message:
        "Generating multiple evenly-sized R2 chunks ({wildcards.experiment_name})."
    shell:
        """
        fastqsplitter -i {input} {params.out} -t 1 -c 1
        """

# ---- Demultiplex each splitted R1 and R2 file to generate sample-specific fastq.gz files. ----
       
rule demultiplex_fastq_split:
    input:
        R1=out("{experiment_name}/raw_reads_split/R1_{scatteritem}.fastq.gz"),
        R2=out("{experiment_name}/raw_reads_split/R2_{scatteritem}.fastq.gz"),
    output:
        out_dir=temp(directory(out("{experiment_name}/demux_reads_scatter/{scatteritem}"))),
        discard_R1=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_R1_discarded.fastq.gz")),
        discard_R2=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/{experiment_name}_R2_discarded.fastq.gz")),
        discard_log=temp(out("{experiment_name}/demux_reads_scatter/{scatteritem}/log_{experiment_name}_discarded_reads.tsv.gz")),
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
        --out {output.out_dir} &> {log}
        """


rule gather_demultiplexed_sequencing:
    input:
        gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/")),
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
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_R1_discarded.fastq.gz -print0 | xargs -0 cat > {output.R1_discarded}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_R2_discarded.fastq.gz -print0 | xargs -0 cat > {output.R2_discarded}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name log_{wildcards.experiment_name}_discarded_reads.tsv.gz -print0 | xargs -0 cat > {output.discarded_log}

        # Move the whitelist files.
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_whitelist_p7.txt -print0 | xargs -0 cat | sort -u > {output.whitelist_p7}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_whitelist_p5.txt -print0 | xargs -0 cat | sort -u > {output.whitelist_p5}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_whitelist_ligation.txt -print0 | xargs -0 cat | sort -u > {output.whitelist_ligation}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.experiment_name}_whitelist_rt.txt -print0 | xargs -0 cat | sort -u > {output.whitelist_rt}
        """

rule gather_demultiplexed_samples:
    input:
        gather.fastq_split(out("{{experiment_name}}/demux_reads_scatter/{scatteritem}/")),
    output:
        R1=out("{experiment_name}/demux_reads/{sample_name}_R1.fastq.gz"),
        R2=out("{experiment_name}/demux_reads/{sample_name}_R2.fastq.gz"),
    threads: 1
    resources:
        mem_mb=1024 * 10,
    benchmark:
        out("benchmarks/{experiment_name}/gather_demultiplexed_samples_{sample_name}.txt")
    params:
        path_demux_scatter=lambda w: out(f"{w.experiment_name}/demux_reads_scatter/")
    message:
        "Combining the sample-specific fastq.fz files ({wildcards.experiment_name})."
    shell:
        """
        # Combine files.
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.sample_name}_R1.fastq.gz -print0 | xargs -0 cat > {output.R1}
        find {params.path_demux_scatter} -maxdepth 2 -type f -name {wildcards.sample_name}_R2.fastq.gz -print0 | xargs -0 cat > {output.R2}
        """
