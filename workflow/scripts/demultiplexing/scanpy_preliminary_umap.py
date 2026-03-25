import argparse
import json
import os
import sys

import scanpy as sc

try:
    from .starsolo_paths import resolve_solo_feature_paths
except ImportError:
    from starsolo_paths import resolve_solo_feature_paths


def _round_series(values, digits):
    return [round(float(value), digits) for value in values]


def _build_unavailable_payload(sample, feature, n_cells_input, message):
    return {
        "sample_name": sample,
        "feature": feature,
        "status": "unavailable",
        "message": message,
        "n_cells_input": int(n_cells_input),
        "n_cells_plot": 0,
        "x": [],
        "y": [],
        "metrics": {},
    }


def _load_filtered_adata(filtered_dir):
    adata = sc.read_10x_mtx(
        str(filtered_dir),
        var_names="gene_symbols",
        make_unique=True,
        compressed=False,
    )
    adata.var_names_make_unique()
    adata.obs_names_make_unique()
    adata.var["mt"] = adata.var_names.str.upper().str.startswith("MT-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True, log1p=True)
    return adata


def _preprocess_for_umap(adata, random_seed):
    adata = adata.copy()

    if adata.n_obs < 3 or adata.n_vars < 2:
        return None

    sc.pp.normalize_total(adata)
    sc.pp.log1p(adata)
    use_highly_variable = False
    try:
        sc.pp.highly_variable_genes(adata, n_top_genes=min(2000, adata.n_vars))
    except Exception:
        pass
    else:
        if "highly_variable" in adata.var:
            use_highly_variable = int(adata.var["highly_variable"].sum()) >= 2

    if adata.n_obs < 3 or adata.n_vars < 2:
        return None

    n_comps = min(50, adata.n_obs - 1, adata.n_vars - 1)
    n_neighbors = min(15, adata.n_obs - 1)
    if n_comps < 2 or n_neighbors < 2:
        return None

    try:
        sc.tl.pca(adata, n_comps=n_comps, use_highly_variable=use_highly_variable)
        sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_comps, random_state=random_seed)
        sc.tl.umap(adata, random_state=random_seed, init_pos="random")
    except Exception:
        return None

    return adata


def generate_preliminary_umap(path_star, sample, solo_features=None, random_seed=0):
    solo_paths = resolve_solo_feature_paths(
        path_star,
        sample,
        preferred_features=solo_features,
        require_filtered_matrix=True,
    )

    sc.settings.verbosity = 0
    base_adata = _load_filtered_adata(solo_paths["filtered_dir"])

    n_cells_input = int(base_adata.n_obs)
    if n_cells_input == 0 or base_adata.n_vars == 0:
        return _build_unavailable_payload(
            sample,
            solo_paths["feature"],
            n_cells_input,
            "No filtered cells or genes available for UMAP.",
        )

    adata = _preprocess_for_umap(base_adata, random_seed)

    if adata is None:
        return _build_unavailable_payload(
            sample,
            solo_paths["feature"],
            n_cells_input,
            "Too few cells or genes remained after preprocessing to compute a stable UMAP.",
        )

    return {
        "sample_name": sample,
        "feature": solo_paths["feature"],
        "status": "ok",
        "message": "",
        "n_cells_input": n_cells_input,
        "n_cells_plot": int(adata.n_obs),
        "x": _round_series(adata.obsm["X_umap"][:, 0], 4),
        "y": _round_series(adata.obsm["X_umap"][:, 1], 4),
        "metrics": {
            "log1p_n_genes_by_counts": _round_series(adata.obs["log1p_n_genes_by_counts"], 4),
            "log1p_total_counts": _round_series(adata.obs["log1p_total_counts"], 4),
            "pct_counts_mt": _round_series(adata.obs["pct_counts_mt"], 2),
        },
    }


def main(arguments):
    parser = argparse.ArgumentParser(
        description="Generate a compact per-sample preliminary UMAP payload from filtered STARsolo output.",
        add_help=False,
    )
    parser.add_argument("--path_star", required=True, type=str, help="(str) Path to the STAR alignment folder.")
    parser.add_argument("--sample", required=True, type=str, help="(str) Sample name.")
    parser.add_argument("--path_out", required=True, type=str, help="(str) Path to store compact UMAP JSON.")
    parser.add_argument(
        "--solo_features",
        required=False,
        nargs="+",
        type=str,
        help="(str) Preferred STARSolo feature(s) to resolve before applying fallback.",
    )
    parser.add_argument(
        "--random_seed",
        required=False,
        type=int,
        default=0,
        help="(int) Random seed used for UMAP reproducibility.",
    )
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Display help and exit.")

    args = parser.parse_args(arguments)
    payload = generate_preliminary_umap(
        path_star=args.path_star,
        sample=args.sample,
        solo_features=args.solo_features,
        random_seed=args.random_seed,
    )

    os.makedirs(os.path.dirname(args.path_out), exist_ok=True)
    with open(args.path_out, "w") as handle:
        json.dump(payload, handle, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit()
