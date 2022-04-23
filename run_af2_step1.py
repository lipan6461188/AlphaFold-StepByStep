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
#  AlphaFold2 Step 1 -- Search homologous sequences and templates
#  Usage: run_af2_step1.py /path/to/input.fasta /path/to/output_dir
#
#

import json
import gzip
import os
import pathlib
import pickle
import random
import shutil
import sys
import time
from typing import Dict, Union, Optional
import configparser
import argparse
import numpy as np

cur_path = pathlib.Path(__file__).parent.resolve()

ini_config = configparser.ConfigParser(allow_no_value=True)
assert len(ini_config.read(os.path.join(cur_path, 'config.ini'))) > 0, "Read config.ini failed"

sys.path.insert(0, ini_config['ALPHAFOLD2']['alphafold_path'])

from alphafold.common import protein
from alphafold.common import residue_constants
from alphafold.data import pipeline
from alphafold.data import templates
from alphafold.data.tools import hhsearch
from alphafold.data.tools import hmmsearch
from alphafold.model import config
from alphafold.model import model
from alphafold.model import data

parser = argparse.ArgumentParser(description='AlphaFold2 Step 1 -- Search homologous sequences and templates')

parser.add_argument('input_file', metavar='input_file', type=str, help='The fasta file to process, must one sequence.')
parser.add_argument('output_dir', metavar='output_dir', type=str, help='Path to a directory that will store the results.')
parser.add_argument('--max_template_date', default='2021-11-03', type=str, help="Maximun date to search for templates.")

args = parser.parse_args()

features_output_path = os.path.join(args.output_dir, 'features.pkl.gz')

if os.path.exists(features_output_path):
    print(f"Info: {features_output_path} exists, please delete it and try again.")
    exit(0)

#################################
### Auxiliary functions
#################################

def check_executable(config_set_value, executable_exe):
    if config_set_value != '':
        assert os.path.exists(config_set_value), f"{config_set_value} not exists"
        return config_set_value
    executable_exe = shutil.which(executable_exe)
    assert executable_exe is not None, f"{executable_exe} not found in PATH"
    return executable_exe

def check_file(config_set_value):
    assert os.path.exists(config_set_value) or os.path.exists(config_set_value + "_a3m.ffdata"), f"{config_set_value} not exists"
    return config_set_value

#################################
### Excutable files
#################################

jackhmmer_binary_path   = check_executable(ini_config['EXCUTABLE']['jackhmmer_binary_path'], "jackhmmer")
hhblits_binary_path     = check_executable(ini_config['EXCUTABLE']['hhblits_binary_path'], "hhblits")
hhsearch_binary_path    = check_executable(ini_config['EXCUTABLE']['hhsearch_binary_path'], "hhsearch")
hmmsearch_binary_path   = check_executable(ini_config['EXCUTABLE']['hmmsearch_binary_path'], "hmmsearch")
hmmbuild_binary_path    = check_executable(ini_config['EXCUTABLE']['hmmbuild_binary_path'], "hmmbuild")
kalign_binary_path      = check_executable(ini_config['EXCUTABLE']['kalign_binary_path'], "kalign")

#################################
### Database files
#################################

uniref90_database_path      = check_file(ini_config['DATABASE']['uniref90_database_path'])
mgnify_database_path        = check_file(ini_config['DATABASE']['mgnify_database_path'])
template_mmcif_dir          = check_file(ini_config['DATABASE']['template_mmcif_dir'])
obsolete_pdbs_path          = check_file(ini_config['DATABASE']['obsolete_pdbs_path'])
uniclust30_database_path    = check_file(ini_config['DATABASE']['uniclust30_database_path'])
bfd_database_path           = check_file(ini_config['DATABASE']['bfd_database_path'])
pdb70_database_path         = check_file(ini_config['DATABASE']['pdb70_database_path'])

#################################
### Options
#################################

max_template_date           = args.max_template_date # Use the latest templates
use_precomputed_msas        = False
use_small_bfd               = False
MAX_TEMPLATE_HITS           = 20

#################################
### Define searcher, featurizer and pipeline
#################################

template_searcher = hhsearch.HHSearch(
    binary_path=hhsearch_binary_path,
    databases=[pdb70_database_path])

template_featurizer = templates.HhsearchHitFeaturizer(
    mmcif_dir=template_mmcif_dir,
    max_template_date=max_template_date,
    max_hits=MAX_TEMPLATE_HITS,
    kalign_binary_path=kalign_binary_path,
    release_dates_path=None,
    obsolete_pdbs_path=obsolete_pdbs_path)

data_pipeline = pipeline.DataPipeline(
    jackhmmer_binary_path = jackhmmer_binary_path,
    hhblits_binary_path = hhblits_binary_path,
    uniref90_database_path = uniref90_database_path,
    mgnify_database_path = mgnify_database_path,
    bfd_database_path = bfd_database_path,
    uniclust30_database_path = uniclust30_database_path,
    small_bfd_database_path = None,
    template_searcher = template_searcher,
    template_featurizer = template_featurizer,
    use_small_bfd = use_small_bfd,
    use_precomputed_msas = use_precomputed_msas)

#################################
### Run pipeline
#################################

msa_output_dir = os.path.join(args.output_dir, 'msas')
if not os.path.exists(msa_output_dir):
    os.makedirs(msa_output_dir)

feature_dict = data_pipeline.process(
        input_fasta_path = args.input_file,
        msa_output_dir = msa_output_dir)

pickle.dump(feature_dict, gzip.open(features_output_path, 'wb'), protocol=4)

