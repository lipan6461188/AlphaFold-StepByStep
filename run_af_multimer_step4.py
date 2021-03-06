#!/usr/bin/env python
#-*- coding:utf-8 -*-
###############################################
#
#
#   Run AlphaFold-Multimer step by step
#   (https://github.com/deepmind/alphafold)
#   Author: Pan Li (lipan@shuimubio.com)
#                    @ Shuimu BioScience
#        https://www.shuimubio.com/
#
#
################################################

#
#
#  AlphaFold-Multimer Step 4 -- Sort models
#  Usage: run_af_multimer_step4.py result_multimer_1.pkl,...,result_multimer_5.pkl pdb_1.pdb,...,pdb_5.pdb /path/to/output
#
#

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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import argparse

parser = argparse.ArgumentParser(description='AlphaFold-Multimer Step 4 -- Sort models')

parser.add_argument('model_pkl_list', metavar='model_pkl_list', type=str, help='The result_model.pkl files generated by AlphaFold-Multimer step 2, seperated by comma.')
parser.add_argument('pdb_file_list', metavar='pdb_file_list', type=str, help='The PDB files generated by AlphaFold-Multimer step 2 or 3, seperated by comma.')
parser.add_argument('output_dir', metavar='output_dir', type=str, help='Path to a directory that will store the results.')

args = parser.parse_args()

######################
## Check inputs
######################

model_pkl_fn_list = args.model_pkl_list.split(',')
pdb_fn_list = args.pdb_file_list.split(',')

assert len(model_pkl_fn_list) == len(pdb_fn_list), "Error: model_pkl_list and pdb_file_list must be the same length"

output_dir = args.output_dir

assert os.path.exists(output_dir), "Error: output_dir does not exists"

######################
## Read inputs
######################

model_pkl_list = []
for model_pkl_fn in model_pkl_fn_list:
    if model_pkl_fn.endswith('.gz'):
        prediction_result = pickle.load(gzip.open(model_pkl_fn, 'rb'))
    else:
        prediction_result = pickle.load(open(model_pkl_fn, 'rb'))
    model_pkl_list.append({
        'ptm': prediction_result['ptm'],
        'iptm': prediction_result['iptm'],
        'ranking_confidence': prediction_result['ranking_confidence'],
        'plddt': prediction_result['plddt'],
        'predicted_aligned_error': prediction_result['predicted_aligned_error']
    })
    del prediction_result

######################
## Sort
######################

dec_order = np.argsort( [obj['ranking_confidence'] for obj in model_pkl_list] )[::-1]

######################
## Rename PDB file and log file
######################

for rank,i in enumerate(dec_order):
    shutil.copyfile( pdb_fn_list[i], os.path.join(output_dir, f'ranked_{rank+1}.pdb') )

log = { 
    "iptm+ptm": { f"model_{i+1}_multimer": model_pkl_list[i]['ranking_confidence'] for i in range(len(model_pkl_list)) },
    "order": [ f"model_{i+1}_multimer" for i in dec_order ]
}

with open( os.path.join(output_dir, 'ranking_debug.json'), 'w' ) as OUT:
    json.dump(log, OUT, indent=4)

######################
## Plot for visualization
######################

for rank,i in enumerate(dec_order):
    plt.figure(figsize=(8, 6))
    sns.heatmap( model_pkl_list[i]['predicted_aligned_error'], vmin=0.0, vmax=20.0 )
    plt.xlabel("Residual")
    plt.ylabel("Residual")
    plt.title(f"model_{i+1}_multimer rank={rank+1}")
    plt.tight_layout()
    plt.savefig( f"{output_dir}/model_{i+1}_predicted_aligned_error.png" )
    plt.close()
    
    plddt = model_pkl_list[i]['plddt']
    plt.figure(figsize=(12, 4))
    plt.bar(range(len(plddt)), plddt, linewidth=0.8)
    plt.xlabel("Residual")
    plt.ylabel("pLDDT")
    plt.title(f"model_{i+1}_multimer rank={rank+1}")
    plt.tight_layout()
    plt.savefig( f"{output_dir}/model_{i+1}_plddt.png" )
    plt.close()

