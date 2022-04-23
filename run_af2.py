#!/usr/bin/env python
#-*- coding:utf-8 -*-
###############################################
#
#
#   Run AlphaFold2 step by step
#   (https://github.com/deepmind/alphafold)
#   Author: Pan Li (lipan@shuimubio.com)
#                    @ Shuimu BioScience
#        https://www.shuimubio.com/
#
#
################################################

#
#
#  AlphaFold2 Step 1-4
#  Usage: run_af2.py [--skip_refine] /path/to/input.fasta /path/to/output
#   Step 1: Search homologous sequences and templates
#   Step 2: Run models 1-5 to produce the unrelaxed models
#   Step 3: Relax models
#   Step 4: Sort models
#
#

running_str = """
Run AlphaFold2 step by step
# Step 1: Search homologous sequences and templates
# Step 2: Run models 1-5 to produce the unrelaxed models
# Step 3: Relax models. Very slow for large protein complex
# Step 4: Sort models
"""

import json
import os
import pathlib
import pickle
import random
import shutil
import sys
import time
import gzip
from typing import Dict, Union, Optional
import numpy as np
import argparse

cur_path = pathlib.Path(__file__).parent.resolve()
parser = argparse.ArgumentParser(description='AlphaFold2 pipeline')

parser.add_argument('input_file', metavar='input_file', type=str, help='The fasta file to process, must contain one sequence.')
parser.add_argument('output_dir', metavar='output_dir', type=str, help='Path to a directory that will store the results.')
parser.add_argument('--max_template_date', default='2021-11-03', type=str, help="Maximun date to search for templates.")
parser.add_argument('--skip_refine', action='store_true', help='Skip the refine step (step 3)')
parser.add_argument('--models', default='1,2,3,4,5', type=str, help="Models to run, seperated by comma. (1,2,3 or 1_ptm,2_ptm)")

args = parser.parse_args()

print(running_str, flush=True)

step1_file = os.path.join(cur_path, 'run_af2_step1.py')
step2_file = os.path.join(cur_path, 'run_af2_step2.py')
step3_file = os.path.join(cur_path, 'run_af2_step3.py')
step4_file = os.path.join(cur_path, 'run_af2_step4.py')

models_to_run = args.models.split(',')
for model_name in models_to_run:
    if model_name.endswith('_ptm'):
        model_idx = model_name.split('_')[0]
        assert 1 <= int(model_idx) <= 5
    else:
        model_idx = int(model_name)
        assert 1 <= int(model_idx) <= 5

########################
### Step 1
########################

cmd = f"python {step1_file} {args.input_file} {args.output_dir} --max_template_date {args.max_template_date}"

print("Run Step 1: Search homologous sequences and templates")
if os.system(cmd) != 0:
    print("Step 1 Failed")
    exit(-1)

########################
### Step 2
########################

cmd = f"python {step2_file} {args.output_dir}/features.pkl.gz {args.output_dir} --models {args.models}"

print("Run Step 2: Run models 1-5 to produce the unrelaxed models")
if os.system(cmd) != 0:
    print("Step 2 Failed")
    exit(-1)

########################
### Step 3
########################

print("Run Step 3: Relax models. Very slow for large protein complex")
if args.skip_refine:
    print("Step 3 skipped")
else:
    for model_name in models_to_run:
        cmd = f"python {step3_file} {args.output_dir}/unrelaxed_model_{model_name}.pdb {args.output_dir}/relaxed_model_{model_name}.pdb"
        if os.system(cmd) != 0:
            print("Step 3 Failed")
            exit(-1)

########################
### Step 4
########################

model_pkls = ",".join([ f'{args.output_dir}/result_model_{model_name}.pkl.gz' for model_name in models_to_run ])

if args.skip_refine:
    model_pdbs = ",".join([ f'{args.output_dir}/unrelaxed_model_{model_name}.pdb' for model_name in models_to_run ])
else:
    model_pdbs = ",".join([ f'{args.output_dir}/relaxed_model_{model_name}.pdb' for model_name in models_to_run ])

cmd = f"python {step4_file} {model_pkls} {model_pdbs} {args.output_dir}"

print("Run Step 4: Sort models")
if os.system(cmd) != 0:
    print("Step 4 Failed")
    exit(-1)


