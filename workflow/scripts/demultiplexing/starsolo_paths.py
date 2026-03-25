from __future__ import annotations

from pathlib import Path

DEFAULT_FEATURE_FALLBACK = [
    "GeneFull_Ex50pAS",
    "GeneFull_ExonOverIntron",
    "GeneFull",
    "Gene",
]


def parse_feature_list(features) -> list[str]:
    """
    Parse feature tokens that may be whitespace and/or comma separated.
    """

    if not features:
        return []

    if isinstance(features, str):
        values = [features]
    else:
        values = list(features)

    parsed: list[str] = []
    for value in values:
        for token in str(value).replace(",", " ").split():
            token = token.strip()
            if token and token not in parsed:
                parsed.append(token)

    return parsed


def build_feature_preference(
    preferred_features=None,
    discovered_features=None,
) -> list[str]:
    """
    Build feature search order from configured preference, defaults and discovery.
    """

    candidate_features: list[str] = []
    for feature in parse_feature_list(preferred_features):
        if feature not in candidate_features:
            candidate_features.append(feature)

    for feature in DEFAULT_FEATURE_FALLBACK:
        if feature not in candidate_features:
            candidate_features.append(feature)

    if discovered_features:
        for feature in discovered_features:
            if feature and feature not in candidate_features:
                candidate_features.append(feature)

    return candidate_features


def resolve_solo_feature_paths(
    path_star,
    sample: str,
    preferred_features=None,
    require_filtered_matrix: bool = False,
):
    """
    Resolve STARSolo feature-specific paths for one sample with feature fallback.
    """

    solo_dirs = sorted(Path(path_star).glob(f"{sample}_*_Solo.out"))
    if not solo_dirs:
        raise FileNotFoundError(
            f"No STARSolo output directory found for sample '{sample}' in {path_star}"
        )

    solo_dir = solo_dirs[0]
    discovered_features = sorted(
        summary.parent.name for summary in solo_dir.glob("*/Summary.csv")
    )
    candidate_features = build_feature_preference(
        preferred_features=preferred_features,
        discovered_features=discovered_features,
    )

    for feature in candidate_features:
        feature_dir = solo_dir / feature
        summary = feature_dir / "Summary.csv"
        cellreads = feature_dir / "CellReads.stats"
        filtered_dir = feature_dir / "filtered"
        filtered_barcodes = filtered_dir / "barcodes.tsv"
        filtered_features = filtered_dir / "features.tsv"
        filtered_matrix = filtered_dir / "matrix.mtx"
        filtered_barcodes_converted = filtered_dir / "barcodes_converted.tsv"

        required = [summary, cellreads, filtered_barcodes]
        if require_filtered_matrix:
            required.extend([filtered_features, filtered_matrix])

        if all(path.exists() for path in required):
            return {
                "feature": feature,
                "solo_dir": solo_dir,
                "feature_dir": feature_dir,
                "summary": summary,
                "cellreads": cellreads,
                "filtered_dir": filtered_dir,
                "filtered_barcodes": filtered_barcodes,
                "filtered_features": filtered_features,
                "filtered_matrix": filtered_matrix,
                "filtered_barcodes_converted": filtered_barcodes_converted,
            }

    missing = (
        "Summary.csv, CellReads.stats, filtered/barcodes.tsv, filtered/features.tsv and filtered/matrix.mtx"
        if require_filtered_matrix
        else "Summary.csv, CellReads.stats and filtered/barcodes.tsv"
    )
    raise FileNotFoundError(
        f"Could not resolve STARSolo {missing} for sample '{sample}' in {solo_dir} "
        f"using feature order {candidate_features}"
    )
