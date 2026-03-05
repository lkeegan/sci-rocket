#   * Convert reads to Undetermined.fastq.gz files with p5+p7 in the read-name. *
#
#   1. make_fake_samplesheet:       Generate fake sample-sheet to allow indexes to be added to R1/R2.
#   2. reads2fastq:                   Convert bcl to fastq with p5 and p7 indexes within the read name.
#############

def get_path(sequencing_name, experiment_name):
    """
    Return the path to the reads for a given sequencing run.
    """
    return samples_unique.query("sequencing_name == @sequencing_name & experiment_name == @experiment_name").path_reads.values[0]


def get_sequencing_lanes():
    """
    Return optional globally configured lane IDs.
    """
    return preprocess.get_configured_sequencing_lanes(config)


def get_fake_bcl_samplesheet():
    """
    Build fake BCL sample-sheet contents, with optional lane restriction.
    """
    lanes = get_sequencing_lanes()
    rows = [f"{lane},fake,fake,NNNNNNNNNN,NNNNNNNNNN" for lane in lanes] if lanes else [",fake,fake,NNNNNNNNNN,NNNNNNNNNN"]
    return "[DATA]\nLane,Sample_ID,Sample_Name,index,index2\n" + "\n".join(rows) + "\n"


def get_fake_aviti_manifest():
    """
    Build fake AVITI run-manifest contents, with optional lane restriction.
    """
    lanes = get_sequencing_lanes()
    lane_field = "+".join(lanes) if lanes else "1+2"
    return f"[Samples]\nSampleName,Index1,Index2,Lane\nfake,AAAAAAAAAA,AAAAAAAAAA,{lane_field}\n"


rule install_bases2fastq:
    output:
        bases2fastq_exe=out("resources/bases2fastq/bases2fastq"),
    params:
        bases2fastq_exe = config["settings"].get("bases2fastq_exe", ""),
    log:
        out("logs/step1_reads2fastq/install_bases2fastq.log"),
    shell:
        r"""
        exec > "{log}" 2>&1
        mkdir -p $(dirname {output.bases2fastq_exe})
        if [ -n "{params.bases2fastq_exe}" ] && [ -x "{params.bases2fastq_exe}" ]; then
            echo "Using user-provided Bases2Fastq executable: {params.bases2fastq_exe}"
            ln -sf "{params.bases2fastq_exe}" {output.bases2fastq_exe}
        elif command -v bases2fastq >/dev/null 2>&1; then
            found_exe=$(command -v bases2fastq)
            echo "Using Bases2Fastq found on PATH: $found_exe"
            ln -sf "$found_exe" {output.bases2fastq_exe}
        else
            echo "Downloading latest release of Bases2Fastq executable"
            tmpdir=$(mktemp -d)
            curl -L https://bases2fastq-release.s3.amazonaws.com/bases2fastq-latest.tar.gz -o "$tmpdir/bases2fastq.tar.gz"
            tar -xvf "$tmpdir/bases2fastq.tar.gz" -C "$tmpdir"
            install -m 0755 "$tmpdir/bases2fastq" {output.bases2fastq_exe}
            rm -rf "$tmpdir"
        fi
        """


rule reads2fastq:
    input:
        path=lambda w: get_path(w.sequencing_name, w.experiment_name),
        bases2fastq_exe=rules.install_bases2fastq.output.bases2fastq_exe,
    output:
        R1=temp(out("{experiment_name}/raw_reads/{sequencing_name}/Undetermined_S0_R1_001.fastq.gz")),
        R2=temp(out("{experiment_name}/raw_reads/{sequencing_name}/Undetermined_S0_R2_001.fastq.gz")),
        tmp=temp(directory(out("{experiment_name}/raw_reads/{sequencing_name}/tmp"))),
    log:
        out("logs/step1_reads2fastq/reads2fastq_{experiment_name}_{sequencing_name}.log"),
    threads: 40
    resources:
        mem_mb=1024 * 48,
    benchmark:
        out("benchmarks/{experiment_name}/reads2fastq_{sequencing_name}.txt")
    params:
        path_out=out("{experiment_name}/raw_reads/{sequencing_name}"),
        extra=config["settings"]["bcl2fastq"],
        lanes=lambda _: ",".join(get_sequencing_lanes() or []),
        fake_bcl_samplesheet=lambda _: get_fake_bcl_samplesheet(),
        fake_aviti_manifest=lambda _: get_fake_aviti_manifest(),
    conda:
        "envs/sci-rocket.yaml",
    message: "Converting reads to fastq with p5 and p7 indexes within the read name ({wildcards.experiment_name}: {wildcards.sequencing_name})."
    shell:
        r"""
        exec > "{log}" 2>&1
        mkdir -p {output.tmp}
        
        if [[ -f "{input.path}/RunInfo.xml" ]]; then
            echo "Found RunInfo.xml in {input.path}: treating input as BCL run folder."
            echo "Running bcl2fastq to convert to fastq.gz"
            if [[ -n "{params.lanes}" ]]; then
                echo "Restricting BCL conversion to lane(s): {params.lanes}"
            else
                echo "No lane restriction configured; using all lanes."
            fi
            cat > "{params.path_out}/fake_bcl_sample_sheet.csv" << 'EOF_BCL'
{params.fake_bcl_samplesheet}
EOF_BCL
            # 40 cores / 40GB RAM: 2GB/core needed according to Illumina bcl2fastq docs
            bcl2fastq \
            {params.extra} \
            -R "{input.path}" \
            --sample-sheet "{params.path_out}/fake_bcl_sample_sheet.csv" \
            --output-dir "{params.path_out}" \
            --loading-threads 8 \
            --processing-threads 30 \
            --writing-threads 2
        elif [[ -d "{input.path}/BaseCalls" ]]; then
            echo "Found BaseCalls/ in {input.path} (and no RunInfo.xml): treating input as AVITI run folder"
            echo "Running Bases2Fastq to convert to fastq.gz, then using fastq-fix-i5 to reverse-complement i5 in R1 headers"
            if [[ -n "{params.lanes}" ]]; then
                echo "Restricting AVITI conversion to lane(s): {params.lanes}"
            else
                echo "No lane restriction configured; defaulting AVITI lane field to 1+2."
            fi
            cat > "{params.path_out}/fake_aviti_run_manifest.csv" << 'EOF_AVITI'
{params.fake_aviti_manifest}
EOF_AVITI
            # 8 cores / 48GB RAM: 6GB/core needed according to https://docs.elembio.io/docs/bases2fastq/setup/#memory-and-performance
            {input.bases2fastq_exe} \
            --run-manifest "{params.path_out}/fake_aviti_run_manifest.csv" \
            --num-threads 8 \
            --skip-multi-qc \
            --skip-qc-report \
            {input.path} \
            {output.tmp}
            # Reverse-complement i5 index in R1 fastq headers
            pigz -dc "{output.tmp}/Samples/DefaultProject/fake/fake_R1.fastq.gz" \
              | fastq-fix-i5 \
              | pigz -c > "{output.R1}"
            mv "{output.tmp}/Samples/DefaultProject/fake/fake_R2.fastq.gz" "{output.R2}"
        else
            echo "No RunInfo.xml or BaseCalls folder found in {input.path}, treating input as FASTQ folder"
            # Look for fastq files of the form *_R1*fastq.gz and *_R2*fastq.gz
            mapfile -t R1_FILES < <(find "{input.path}" -maxdepth 1 -type f -iname "*R1*.fastq.gz")
            mapfile -t R2_FILES < <(find "{input.path}" -maxdepth 1 -type f -iname "*R2*.fastq.gz")
    
            if [[ ${{#R1_FILES[@]}} -ne 1 || ${{#R2_FILES[@]}} -ne 1 ]]; then
                echo "ERROR: Expected exactly one R1 and one R2 .fastq.gz in {input.path}"
                echo "Found ${{#R1_FILES[@]}} R1 files:"
                printf '  %s\n' "${{R1_FILES[@]}}"
                echo "Found ${{#R2_FILES[@]}} R2 files:"
                printf '  %s\n' "${{R2_FILES[@]}}"
                exit 1
            fi
            
            R1="$(realpath "${{R1_FILES[0]}}")"
            R2="$(realpath "${{R2_FILES[0]}}")"

            echo "Found fastq.gz files, creating symlinks:"
            echo "  R1: $R1 -> {output.R1}"
            echo "  R2: $R2 -> {output.R2}"

            ln -sf "$R1" "{output.R1}"
            ln -sf "$R2" "{output.R2}"
        fi
        """

def get_sequencing_runs(experiment_name):
    """Return a list of sequencing runs."""
    return samples_unique.query("experiment_name == @experiment_name").sequencing_name.unique().tolist()

rule merge_sequencing_runs:
    input:
        R1=lambda w: expand(out("{experiment_name}/raw_reads/{sequencing_name}/Undetermined_S0_R1_001.fastq.gz"), experiment_name=w.experiment_name, sequencing_name=get_sequencing_runs(w.experiment_name)),
        R2=lambda w: expand(out("{experiment_name}/raw_reads/{sequencing_name}/Undetermined_S0_R2_001.fastq.gz"), experiment_name=w.experiment_name, sequencing_name=get_sequencing_runs(w.experiment_name)),
    output:
        R1=out("{experiment_name}/raw_reads/Undetermined_S0_R1_001.fastq.gz"),
        R2=out("{experiment_name}/raw_reads/Undetermined_S0_R2_001.fastq.gz"),
    log:
        out("logs/step1_reads2fastq/merge_sequencing_runs_{experiment_name}.log"),
    threads: 1
    resources:
        mem_mb=1024 * 2,
    params:
        total_sequencing_runs=lambda w: len(get_sequencing_runs(w.experiment_name)),
    message: "Merge sequencing runs ({wildcards.experiment_name})."
    benchmark:
        out("benchmarks/{experiment_name}/merge_sequencing_runs.txt")
    shell:
        """
        exec > "{log}" 2>&1
        # If only one sequencing run, then just hardlink it (and remove the original).
        if [ {params.total_sequencing_runs} -eq 1 ]; then
            echo "Only one sequencing run found, creating hardlinks."
            ln {input.R1} {output.R1}
            ln {input.R2} {output.R2}
        else
            echo "Multiple sequencing runs found, concatenating fastq.gz files."
            cat {input.R1} > {output.R1}
            cat {input.R2} > {output.R2}
        fi
        """
