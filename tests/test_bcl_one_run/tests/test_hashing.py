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
    assert data[0] == ['zfish', 'zfish-hash', '40uM_P7_F12', 'CGCGGCCATA_CGGCGAGACC_TACTTGCGTG_GCGTTGGAGC', 'C06_D03_LIG87_P01-A02', '10', '6']
    assert data[1] == ['zfish', 'zfish-hash', '20uM_P7_G10', 'AATATTACTT_GAACTGCATC_CCAAGGATTG_TCCAATCATC', 'C07_B03_LIG78_P01-F03', '10', '3']
    assert data[2] == ['zfish', 'zfish-hash', '40uM_P7_B12', 'ATTGGCAGAT_GTTGACGGCC_GCTCTTAGTG_TCCGGCCTCG', 'C08_A03_LIG68_P01-D04', '8', '5']
