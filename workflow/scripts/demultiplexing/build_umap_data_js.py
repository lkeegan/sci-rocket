import argparse
import json
import os
import sys

COLOR_OPTIONS = [
    {"key": "plain", "label": "Plain"},
    {"key": "log1p_n_genes_by_counts", "label": "Genes per cell (log1p)"},
    {"key": "log1p_total_counts", "label": "Total counts (log1p)"},
    {"key": "pct_counts_mt", "label": "Mitochondrial reads (%)"},
]
DEFAULT_COLOR_KEY = "log1p_n_genes_by_counts"


def build_umap_payload(path_inputs):
    samples = {}
    for path_input in path_inputs:
        with open(path_input, "r") as handle:
            sample_payload = json.load(handle)
        sample_name = sample_payload["sample_name"]
        samples[sample_name] = sample_payload

    return {
        "default_color_key": DEFAULT_COLOR_KEY,
        "color_options": COLOR_OPTIONS,
        "samples": samples,
    }


def main(arguments):
    parser = argparse.ArgumentParser(
        description="Combine per-sample preliminary UMAP JSON files into a compact dashboard JS payload.",
        add_help=False,
    )
    parser.add_argument("--path_out", required=True, type=str, help="(str) Path to store dashboard UMAP JS.")
    parser.add_argument(
        "--path_inputs",
        required=False,
        nargs="*",
        default=[],
        type=str,
        help="(str) Per-sample compact UMAP JSON files.",
    )
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Display help and exit.")

    args = parser.parse_args(arguments)
    payload = build_umap_payload(args.path_inputs)

    os.makedirs(os.path.dirname(args.path_out), exist_ok=True)
    with open(args.path_out, "w") as handle:
        handle.write("var umapData = ")
        json.dump(payload, handle, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit()
