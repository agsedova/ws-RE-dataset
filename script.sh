#!/bin/sh
#SBATCH --partition=All
#SBATCH --gres=gpu:0

module load /usr/bin/python3
/usr/bin/python3 collect_wikidata.py 1000000