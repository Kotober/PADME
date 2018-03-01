from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import tensorflow as tf
import pandas as pd
import argparse
import os
import sys
import pwd
import pdb
import csv
import re
import math
import time

def load_sequence_dict(sequence_df, sequence_field, phospho_field):
  prot_desc_dict = {}
  for row in sequence_df.itertuples():
    sequence = row[sequence_field]
    phosphorylated = row[phospho_field]
    prot_desc_dict[row[0]] = [phosphorylated, sequence]
  return prot_desc_dict

'''
dfdavis = pd.read_csv('../davis_data/Bio_results.csv', header = 2, index_col=0, usecols=range(3, 76))
molListdavis = list(dfdavis)
dfmetz = pd.read_csv('../metz_data/Metz_interaction.csv', header = 0, index_col=0, usecols=range(2, 10))
molListmetz = list(dfmetz.index)
molListmetz = [molName for molName in molListmetz if molName == molName]
dfkiba = pd.read_csv('../KIBA_data/Smiles_bio_results.csv', header = 0, index_col=0, usecols=range(1, 8))
molListkiba = list(dfkiba.index)
davis_mol = set(molListdavis)
metz_mol = set(molListmetz)
kiba_mol = set(molListkiba)
pdb.set_trace()
'''
dfm = pd.read_csv('../metz_data/restructured.csv', header = 0, index_col=False)
dfd = pd.read_csv('../davis_data/restructured.csv', header = 0, index_col=False)
dfk = pd.read_csv('../KIBA_data/restructured.csv', header = 0, index_col=False)
# dfk = dfk.head(200)
# dfm = dfm.head(200)
# dfd = dfd.head(200)
#dfm = dfm.sort_values(by=['proteinName', 'smiles'])
#dfd = dfd.sort_values(by=['proteinName', 'smiles'])
kiba_sequence_df = pd.read_csv('../KIBA_data/prot_desc.csv', header=0, 
  index_col=0, usecols=range(0, 3))
metz_sequence_df = pd.read_csv('../metz_data/prot_desc_Metz.csv', header=0, 
  index_col=0, usecols=range(0, 6))
davis_sequence_df = pd.read_csv('../davis_data/prot_desc.csv', header=0, 
  index_col=0, usecols=range(0, 3))
time_start = time.time()
kiba_sequence_dict = load_sequence_dict(kiba_sequence_df, 1, 2)
metz_sequence_dict = load_sequence_dict(metz_sequence_df, 4, 5)
davis_sequence_dict = load_sequence_dict(davis_sequence_df, 1, 2)

dict_names = ['kiba', 'metz', 'davis']
sequence_dicts = {dict_names[0]: kiba_sequence_dict, dict_names[1]: metz_sequence_dict, 
  dict_names[2]: davis_sequence_dict}
df_dicts = {dict_names[0]: dfk, dict_names[1]: dfm, dict_names[2]: dfd}
#pdb.set_trace()

invalid_val = -100
davis_value = []
metz_value = []
kiba_value = []
dict_values = {dict_names[0]: kiba_value, dict_names[1]: metz_value, 
  dict_names[2]: davis_value}
protein_name = []
protein_origin = []
cmpd_smiles = []
kiba_leftout = [True]*len(dfk)
davis_leftout = [True]*len(dfd)
metz_leftout = [True]*len(dfm)
dict_leftout = {dict_names[0]: kiba_leftout, dict_names[1]: metz_leftout, 
  dict_names[2]: davis_leftout}
prot_correspondence_dict = {dict_names[1]: {}, dict_names[2]: {}}
cmpd_correspondence_dict = {dict_names[1]: {}, dict_names[2]: {}}
remaining_entries = {dict_names[0]: [], dict_names[1]: [], dict_names[2]: []}

for ind, dataset_nm in enumerate(dict_names):
  remaining_entries[dataset_nm] = np.where(dict_leftout[dataset_nm])[0]
  datafrm = df_dicts[dataset_nm]
  curr_seq_dict = sequence_dicts[dataset_nm]
  curr_values = dict_values[dataset_nm]
  
  for i in remaining_entries[dataset_nm]:
    curr_prot = datafrm.iloc[i]['proteinName']
    curr_cmpd = datafrm.iloc[i]['smiles']
    curr_intxn = datafrm.iloc[i]['interaction_value']
    prot_identity = curr_seq_dict[curr_prot]
    for dict_key in dict_names[(ind + 1):]:
      prot_crpd_dict = prot_correspondence_dict[dict_key]
      cmpd_crpd_dict = cmpd_correspondence_dict[dict_key]
      seq_dict = sequence_dicts[dict_key]
      values_list = dict_values[dict_key]
      data_leftout = dict_leftout[dict_key]
      df = df_dicts[dict_key]
      no_matching = False
      if curr_prot not in prot_crpd_dict:
        prot_correspondence = [seq_dict[a] == prot_identity for a 
          in df.iloc[:]['proteinName']]
        prot_crpd_dict[curr_prot] = prot_correspondence
      else:
        prot_correspondence = prot_crpd_dict[curr_prot]
      if sum(prot_correspondence) == 0:
        no_matching = True

      if not no_matching:
        if curr_cmpd not in cmpd_crpd_dict:
          cmpd_correspondence = [curr_cmpd == b for b in df.iloc[:]['smiles']]
          cmpd_crpd_dict[curr_cmpd] = cmpd_correspondence
        else:
          cmpd_correspondence = cmpd_crpd_dict[curr_cmpd]

        if sum(cmpd_correspondence) == 0:
          no_matching = True
        if not no_matching:
          exact_correspondence = [a and b for a, b in zip(prot_correspondence, 
            cmpd_correspondence)]
          #if sum(prot_correspondence) > 0:
          #  pdb.set_trace()
          if sum(exact_correspondence):
            # There are exact correspondences.
            position = np.where(exact_correspondence)[0]
            
            # if len(position) != 1:
            #    print('dataset: ', dict_key)
            #    print('At KIBA index: ', i)
            #    print('matching:', len(position))
            for pos in position:
              intxn = df.iloc[pos]['interaction_value']            
              data_leftout[pos] = False
          else:
            no_matching = True

      if no_matching:
        intxn = invalid_val
      values_list.append(intxn)
      
    for prev_dataset_nm in dict_names[:ind]:
      dict_values[prev_dataset_nm].append(invalid_val)

    curr_values.append(curr_intxn)
    protein_name.append(curr_prot)
    protein_origin.append(dataset_nm)
    cmpd_smiles.append(curr_cmpd)    
  
  del remaining_entries[dataset_nm]
  del dict_leftout[dataset_nm]
  del sequence_dicts[dataset_nm]
  del df_dicts[dataset_nm]
  if ind + 1 <= len(dict_names) - 1:
    del prot_correspondence_dict[dict_names[ind + 1]]
    del cmpd_correspondence_dict[dict_names[ind + 1]]

#pdb.set_trace()
# kiba_value = np.array(kiba_value)  
# metz_value = np.array(metz_value)
# davis_value = np.array(davis_value)
#interaction_bin = (interactions >= 7.6) * 1

shuffled = np.random.permutation(range(len(kiba_value)))
with open('davis-metz-kiba.csv', 'w', newline='') as csvfile:
  fieldnames = ['davis', 'metz', 'kiba', 'smiles', 'proteinName', 'protein_dataset']
  writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
  writer.writeheader()
  for i in range(len(kiba_value)):    
    # will start writing rows.    
    #intxn_bin = interaction_bin[i][j]
    index = shuffled[i]
    #index = i
    davis_val = davis_value[index]    
    metz_val = metz_value[index]      
    kiba_val = kiba_value[index] 
    davis_val = '' if davis_val == invalid_val else davis_val    
    metz_val = '' if metz_val == invalid_val else metz_val
    #if kiba_val == invalid_val:
    #  pdb.set_trace()
    kiba_val = '' if kiba_val == invalid_val else kiba_val
    writer.writerow({'davis': davis_val, 'metz': metz_val, 'kiba': kiba_val,
      'smiles': cmpd_smiles[index], 'proteinName': protein_name[index],
      'protein_dataset': protein_origin[index]})

time_finish = time.time()
print("time used: ", time_finish - time_start)