from pathlib import Path
import csv


def read_tsv(filename: Path):
    data = []
    with open(filename, 'r', newline='', encoding='utf-8') as f:
        tsv_reader = csv.reader(f, delimiter='\t')
        next(tsv_reader)
        for row in tsv_reader:
            data.append(row)
    return data


def test_hashing_metrics():
    hashing_metrics = Path(__file__).parent.parent / "output" / "Drer.ZAe" / "hashing" / "Drer.ZAe_hashing_metrics.tsv"
    assert hashing_metrics.exists()
    data = read_tsv(hashing_metrics)
    # hashing metrics change depending on the value of scatter_fastq_split,
    # so for now we just check that there is some data with the correct sample_name
    assert len(data) > 0
    assert data[0][0] == 'Drer.ZAe'
