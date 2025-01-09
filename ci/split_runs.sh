#!/usr/bin/env bash

# splits the reads from folder fastq into two folders, run1 and run2,
# each with half of the reads, so that combining the two gives the same reads as using the fast folder.

NFULL=$(zcat fastq/Undetermined_S0_R1_001.fastq.gz | wc -l)
N=$(($NFULL / 2))

mkdir -p run1
mkdir -p run2
rm -rf run1/*
rm -rf run2/*

for R in "1" "2"
do
    INFILE="fastq/Undetermined_S0_R${R}_001.fastq.gz"

    OUTFILE="run1/Undetermined_S0_R${R}_001.fastq"
    rm -f "${OUTFILE}.gz"
    echo "  - $INFILE -> $OUTFILE"
    zcat $INFILE | head -n $N > $OUTFILE
    echo "  - $OUTFILE -> ${OUTFILE}.gz"
    gzip $OUTFILE

    OUTFILE="run2/Undetermined_S0_R${R}_001.fastq"
    rm -f "${OUTFILE}.gz"
    echo "  - $INFILE -> $OUTFILE"
    zcat $INFILE | tail -n $N > $OUTFILE
    echo "  - $OUTFILE -> ${OUTFILE}.gz"
    gzip $OUTFILE
done
