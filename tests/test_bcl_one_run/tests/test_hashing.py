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
    hashing_metrics = Path(__file__).parent.parent / "output" / "zfish" / "hashing" / "zfish_hashing_metrics.tsv"
    assert hashing_metrics.exists()
    data = read_tsv(hashing_metrics)
    assert len(data) == 1675
    # check top three
    assert data[0] == ['zfish', 'zfish-hash', '20uM_P7_G10', 'AATATTACTTGAACTGCATCCCAAGGATTGTCCAATCATC', '10', '3']
    assert data[1] == ['zfish', 'zfish-hash', '40uM_P7_F12', 'CGCGGCCATACGGCGAGACCTACTTGCGTGGCGTTGGAGC', '10', '6']
    assert data[2] == ['zfish', 'zfish-hash', '40uM_P7_B12', 'ATTGGCAGATGTTGACGGCCGCTCTTAGTGTCCGGCCTCG', '8', '5']
