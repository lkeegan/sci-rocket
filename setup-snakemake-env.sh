#!/usr/bin/env bash
# setup-snakemake-env.sh –  create a Snakemake conda‑compatible env for scirocket
# 
# Usage:
#   ./ setup-snakemake-env.sh [manager]
#       manager : micromamba | mamba | conda   (optional)
#
# If no manager is given the script auto‑detects the first one that
# appears on $PATH (conda → mamba → micromamba).

###################################
# Safety idiom: stop immediately if something goes wrong
set -euo pipefail

###################################
# 1. Detect which package manager is available
if [[ "${#}" -gt 0 ]]; then               # a positional argument was supplied
    case "${1}" in
        conda|mamba|micromamba) MGR="${1}" ;;
        *)
            echo "Error: Unknown manager '${1}'."
            echo "Supported values: conda, mamba, micromamba."
            exit 1
            ;;
    esac
else                                        # no argument → auto‑detect in path
    for cand in conda mamba micromamba; do
        if command -v "$cand" >/dev/null 2>&1; then
            MGR="$cand"
            break
        fi
    done

    if [[ -z "${MGR:-}" ]]; then
        echo "Error: No conda‑compatible package manager found."
        echo "Make sure a compatible manager (micromamba, mamba, or conda) is available."
        exit 1
    fi
fi

###################################
# 2. Create (or replace) the environment
echo "Using $MGR to create the 'snakemake' environment ..."
$MGR create -y -n snakemake \
    -c conda-forge -c bioconda \
    python=3.11.7 snakemake=7.32.4 mamba pandas numpy 

# $MGR will tell you if you were successful and how to continue
