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
    assert len(data) == 176
    # check top five
    assert data[0] == ['Drer.ZAe', 'ZAe-14hpf-28', '10uM_P7_D7', 'TTGATTGGCGGGCCGTCAACAATTCTAGGTTTAATTGAAT', '22', '22']
    assert data[1] == ['Drer.ZAe', 'ZAe-14hpf-28', '10uM_P7_A8', 'CTAGCCAGCCCTTAATCTTGCGTCTTCCTGTATCATGATC', '17', '17']
    assert data[2] == ['Drer.ZAe', 'ZAe-14hpf-28', '10uM_P7_B7', 'GCATATGAGCCTCCTGGACCTGATGCGATGGTTACGCAAG', '15', '15']
    assert data[3] == ['Drer.ZAe', 'ZAe-14hpf-28', '10uM_P7_A7', 'TTGGCAAGCCGGTCTCGCCGATGGTTGGTGACTATAGGTT', '15', '15']
    assert data[4] == ['Drer.ZAe', 'ZAe-14hpf-28', '10uM_P7_C7', 'TGCGACCTCTGGTCTCGCCGTGGATTCTATGAGCATATGG', '14', '14']
