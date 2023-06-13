import pandas as pd


def sanity_samples(log, samples, config):
    """
    Checks the provided sample sheet for sanity and inconsistensies with the supplied config.

    Args:
        samples (pandas object): The file location of the spreadsheet.
        config (dict): The config dictionary.

    Returns:
        bool: True if the sample sheet is valid, False otherwise.
    """

    log.info("Checking sanity: Sample sheet.")

    # Check if the sample sheet is empty.
    if samples.empty:
        log.error("Sanity check (Sample sheet) - Sample sheet is empty!")
        return False

    # Check if the sample sheet contains the required columns.
    required_columns = set(["sequencing_name", "barcode_rt", "sample_name", "species"])
    if not required_columns.issubset(samples.columns):
        log.error("Sanity check (Sample sheet) - Sample sheet is missing required column(s): {}".format(", ".join(required_columns.difference(samples.columns))))
        return False

    # Check for duplicate RT barcodes within the same sequencing sample.
    if samples.groupby("sequencing_name")["barcode_rt"].apply(lambda x: x.duplicated().any()).any():
        log.error(
            "Sanity check (Sample sheet) - Sample sheet contains duplicate RT barcodes within the same sequencing sample: {}".format(
                ", ".join(samples.groupby("sequencing_name")["barcode_rt"].apply(lambda x: x[x.duplicated()]).unique()),
            )
        )
        return False

    # Check if the sample sheet contains species which are not defined in the config.
    if not set(samples["species"].unique()).issubset(config["species"].keys()):
        log.error(
            "Sanity check (Sample sheet) - Sample sheet contains species which are not defined in the config: {}".format(
                ", ".join(set(samples["species"].unique()).difference(config["species"].keys()))
            )
        )
        return False

    # Read in the barcodes, as defined in the config.
    barcodes = pd.read_csv(config["path_barcodes"], sep="\t", comment="#")
    barcodes_rt = barcodes.query("type == 'rt'")["barcode"].unique()

    # Check if the sample sheet contains RT barcodes which are not defined in the config.
    if not set(samples["barcode_rt"].unique()).issubset(barcodes_rt):
        log.error(
            "Sanity check (Sample sheet) - Sample sheet contains RT barcodes which are not defined in the config: {}".format(", ".join(set(samples["barcode_rt"].unique()).difference(barcodes_rt)))
        )
        return False

    # Otherwise, the sample sheet is valid.
    return True


def sanity_barcodes(log, path_barcodes):
    """
    Checks the provided barcodes file for sanity.

    Args:
        path_barcodes (str): The file location of the barcodes file.

    Returns:
        bool: True if the barcodes file is valid, False otherwise.
    """

    log.info("Checking sanity: Barcode files.")

    # Read in the barcodes.
    barcodes = pd.read_csv(path_barcodes, sep="\t", comment="#")

    # Check if the barcodes file is empty.
    if barcodes.empty:
        log.error("Sanity check (Barcodes) - Barcodes file is empty!")
        return False

    # Check if the barcodes file contains the required columns.
    required_columns = set(["type", "barcode", "sequence"])
    if not set(required_columns).issubset(barcodes.columns):
        log.error("Sanity check (Barcodes) - Barcodes file is missing required column(s): {}".format(", ".join(required_columns.difference(barcodes.columns))))
        return False

    # Check if all barcode types are defined.
    required_columns = set(["rt", "p5", "p7", "ligation"])
    if not set(required_columns).issubset(barcodes["type"].unique()):
        log.error("Sanity check (Barcodes) - Barcodes file is missing barcode type(s): {}".format(", ".join(required_columns.difference(barcodes["type"].unique()))))
        return False

    # Check if the barcodes file contains duplicate barcodes per type.
    if barcodes.groupby("type")["barcode"].apply(lambda x: x.duplicated().any()).any():
        # Print the duplicate barcodes per type with barcode (type)
        duplicated_barcodes = barcodes.groupby("type")["barcode"].apply(lambda x: x[x.duplicated()]).unique()
        for barcode in duplicated_barcodes:
            log.error("Sanity check (Barcodes) - Barcode {} is duplicated in type {}".format(barcode, barcodes.query("barcode == @barcode")["type"].unique()[0]))

        return False

    # Check if barcode sequences contain only valid nucleotides (ATCG).
    if not barcodes["sequence"].str.contains("^[ATCG]+$").all():
        # Print the invalid barcodes
        invalid_barcodes = barcodes[~barcodes["sequence"].str.contains("^[ATCG]+$")]
        log.error("Sanity check (Barcodes) - Barcodes file contains invalid nucleotides (only ATCG allowed):\n{}".format(invalid_barcodes))

        return False

    # If all checks pass, the barcodes file is valid.
    return True
