import argparse
import pickle


def get_star_index_args(star_index_extra: str, path_qc_pickles: list[str]) -> str:
    extra = star_index_extra.strip()
    if extra:
        return extra

    if not path_qc_pickles:
        raise ValueError("No demux QC pickles provided to infer --sjdbOverhang.")

    max_len = 0
    for path_qc in path_qc_pickles:
        with open(path_qc, "rb") as handle:
            qc = pickle.load(handle)
        max_len = max(max_len, int(qc["max_r2_read_length"]))

    if max_len <= 1:
        raise ValueError(f"Invalid max_r2_read_length ({max_len}) across QC pickles.")

    return f"--sjdbOverhang {max_len - 1}"


def main():
    parser = argparse.ArgumentParser(
        description="Return STAR genomeGenerate args, computing --sjdbOverhang from QC when needed."
    )
    parser.add_argument(
        "--star-index-extra",
        default="",
        help="Raw settings.star_index value from config; if set, returned unchanged.",
    )
    parser.add_argument(
        "path_qc_pickles",
        nargs="*",
        help="Demultiplexing QC pickle paths used to infer max R2 read length.",
    )
    args = parser.parse_args()

    print(get_star_index_args(args.star_index_extra, args.path_qc_pickles))


if __name__ == "__main__":
    main()
