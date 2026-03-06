import argparse
from pathlib import Path
import sys

import pandas as pd


def parse_feature_list(features):
    """
    Parse feature tokens that may be whitespace and/or comma separated.
    """

    if not features:
        return []

    parsed = []
    for value in features:
        for token in value.replace(",", " ").split():
            token = token.strip()
            if token and token not in parsed:
                parsed.append(token)
    return parsed


def load_barcode_lookup(path_barcodes):
    """
    Build lookup dictionaries from the barcode sheet.
    """

    barcodes = pd.read_csv(path_barcodes, sep="\t", dtype=str)

    # Add extra G to the ligation sequence if sequence is 9nt long.
    barcodes.loc[barcodes["type"] == "ligation", "sequence"] = barcodes.loc[
        barcodes["type"] == "ligation", "sequence"
    ].apply(lambda x: x + "G" if len(x) == 9 else x)

    # Generate dictionary with barcode names as keys and sequences as values.
    barcodes_dict = dict.fromkeys(barcodes.type.unique())
    for barcode_type in barcodes_dict.keys():
        barcodes_dict[barcode_type] = dict(
            zip(
                barcodes.loc[barcodes["type"] == barcode_type, "sequence"],
                barcodes.loc[barcodes["type"] == barcode_type, "barcode"],
            )
        )

    # The p5 index needs to be reverse complemented.
    barcodes_dict["p5"] = {
        k[::-1].translate(str.maketrans("ATCG", "TAGC")): v
        for k, v in barcodes_dict["p5"].items()
    }
    return barcodes_dict


def convert_barcodes(path_starsolo_barcodes, path_barcodes, path_out):
    """
    Converts the sequence-based barcodes to their respective barcode name.

    Parameters:
        path_starsolo_barcodes (str): Path to the STARSolo barcodes.tsv.
        path_barcodes (str): Path to the barcoding scheme.
        path_out (str): Path to store converted barcodes.tsv.

    Returns:
        None
    """

    barcodes_dict = load_barcode_lookup(path_barcodes)

    # Read STARSolo barcodes, line by line.
    with open(path_starsolo_barcodes, "r") as f, open(path_out, "w") as fh_out:
        for line in f:
            # Get barcode sequences (separator is _).
            barcode_parts = line.strip().split("_")

            # For each barcode, get the barcode name.
            barcodes_converted = "_".join(
                [
                    barcodes_dict["p7"][barcode_parts[0]],
                    barcodes_dict["p5"][barcode_parts[1]],
                    barcodes_dict["ligation"][barcode_parts[2]],
                    barcodes_dict["rt"][barcode_parts[3]],
                ]
            )

            # Write to output.
            fh_out.write(barcodes_converted + "\n")


def convert_solo_dir(path_solo_out, path_barcodes, features=None):
    """
    Convert barcodes in all feature folders that contain barcodes.tsv files.
    """

    solo_out = Path(path_solo_out)
    if not solo_out.exists():
        raise FileNotFoundError(f"STARSolo output directory not found: {path_solo_out}")

    requested_features = parse_feature_list(features)
    feature_dirs = requested_features if requested_features else sorted(
        path.name for path in solo_out.iterdir() if path.is_dir()
    )

    converted_files = 0
    for feature in feature_dirs:
        feature_dir = solo_out / feature
        if not feature_dir.exists() or not feature_dir.is_dir():
            continue

        for matrix_set in ("raw", "filtered"):
            path_input = feature_dir / matrix_set / "barcodes.tsv"
            path_output = feature_dir / matrix_set / "barcodes_converted.tsv"

            if path_input.exists():
                convert_barcodes(
                    path_starsolo_barcodes=str(path_input),
                    path_barcodes=path_barcodes,
                    path_out=str(path_output),
                )
                converted_files += 1

    if converted_files == 0:
        raise FileNotFoundError(
            f"No STARSolo barcode files found to convert in: {path_solo_out}"
        )


def main(arguments):
    # Setup argument parser.
    parser = argparse.ArgumentParser(
        description="Convert the sequences from STARSolo barcodes.tsv into their respective barcode name.",
        add_help=False,
    )
    parser.add_argument(
        "--solo_out_dir",
        required=True,
        type=str,
        help="(str) Path to a STARSolo output directory (*_Solo.out).",
    )
    parser.add_argument(
        "--features",
        required=False,
        nargs="+",
        type=str,
        help="(str) Optional list of STARSolo features to convert.",
    )
    parser.add_argument(
        "--barcodes", required=True, type=str, help="(str) Path to the barcoding scheme."
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Display help and exit.",
    )

    # Parse arguments.
    args = parser.parse_args()

    convert_solo_dir(
        path_solo_out=args.solo_out_dir,
        path_barcodes=args.barcodes,
        features=args.features,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit()
