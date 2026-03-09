from workflow.scripts.demultiplexing.STARSolo_convertBarcodes import convert_solo_dir


def test_convert_solo_dir_converts_multiple_features(tmp_path):
    barcodes_path = tmp_path / "barcodes.tsv"
    barcodes_path.write_text(
        "\n".join(
            [
                "type\tbarcode\tsequence",
                "p7\tP7A\tGGGGGGGGGG",
                "p5\tP5A\tACGTACGTAC",
                "ligation\tLIGA\tCCCCCCCCCC",
                "rt\tRTA\tTTTTTTTTTT",
            ]
        )
    )

    solo_out = tmp_path / "sample_Solo.out"
    for feature in ["GeneFull_Ex50pAS", "Gene", "Velocyto"]:
        for matrix_set in ["raw", "filtered"]:
            matrix_dir = solo_out / feature / matrix_set
            matrix_dir.mkdir(parents=True, exist_ok=True)
            # STARSolo stores barcode sequence as p7_p5(library-orientated)_ligation_rt.
            (matrix_dir / "barcodes.tsv").write_text("GGGGGGGGGG_GTACGTACGT_CCCCCCCCCC_TTTTTTTTTT\n")

    convert_solo_dir(
        str(solo_out),
        str(barcodes_path),
        ["GeneFull_Ex50pAS", "Gene", "Velocyto"],
    )

    for feature in ["GeneFull_Ex50pAS", "Gene", "Velocyto"]:
        for matrix_set in ["raw", "filtered"]:
            converted = solo_out / feature / matrix_set / "barcodes_converted.tsv"
            assert converted.exists()
            assert converted.read_text().strip() == "P7A_P5A_LIGA_RTA"
