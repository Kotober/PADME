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
import time
import itertools
from multiprocessing import Pool

prot_desc_path="davis_data/prot_desc.csv"
def load_prot_desc_dict(prot_desc_path):
  df = pd.read_csv(prot_desc_path, index_col=0)
  prot_desc_dict = {}
  for row in df.itertuples():
    descriptor = row[2:]
    descriptor = np.array(descriptor)
    pdb.set_trace()
    descriptor = np.reshape(descriptor, (len(descriptor), 1))    
    prot_desc_dict[row[0]] = descriptor
  	
  return prot_desc_dict

def inner_loop2(i, y_true_1, y_pred_1, y_true, y_pred):
  summ = 0.0
  total_pairs = 0
  for j in range(i+1, len(y_true)):
    y_true_2 = y_true[j]      
    if y_true_1 == y_true_2:
      continue
    y_pred_2 = y_pred[j]
    total_pairs += 1
    if y_pred_1 == y_pred_2:
      summ += 0.5
      continue
    concord = np.sign(y_true_1 - y_true_2) == np.sign(y_pred_1 - y_pred_2)
    summ += concord * 1.0
  return summ, total_pairs

def inner_loop(i, y_true_1, y_pred_1, y_true, y_pred):
  summ = 0.0
  total_pairs = 0
  y_true_sublist = y_true[(i+1):len(y_true)]
  y_pred_sublist = y_pred[(i+1):len(y_pred)]
  valid_pairs = y_true_sublist != y_true_1
  y_true_diff = np.sign(y_true_sublist - y_true_1)
  y_pred_diff = np.sign(y_pred_sublist - y_pred_1)
  
  raw_comparison = (y_true_diff * y_pred_diff + 1)/2
  scores = raw_comparison * valid_pairs
  summ = sum(scores)
  total_pairs = sum(valid_pairs)
  return summ, total_pairs

def concordance_index(y_true, y_pred):
  total_pairs = 0
  sum_score = 0.0
  CPU_COUNT = int(0.6*os.cpu_count())

  with Pool(processes=CPU_COUNT) as pool:
    i = 0
    while i < len(y_true) - 1:
      #k = i % (2*CPU_COUNT)
      if i == 0:
        procs = []
        results = []
      y_true_1 = y_true[i]
      y_pred_1 = y_pred[i]

      procs.append(pool.apply_async(inner_loop, [i, y_true_1, y_pred_1, y_true, y_pred]))
      i += 1
      #if k == 2*CPU_COUNT-1 or i == len(y_true) - 1:
      if i == len(y_true) - 1:
        results = [proc.get() for proc in procs]
        summ = [res[0] for res in results]
        pairs = [res[1] for res in results]
        sum_score += sum(summ)
        total_pairs += sum(pairs)
        
  return sum_score/total_pairs

def concordance_index2(y_true, y_pred):
  total_pairs = 0
  sum_score = 0.0
  for i in range(len(y_true) - 1):
    y_true_1 = y_true[i]
    y_pred_1 = y_pred[i]
    for j in range(i+1, len(y_true)):
      y_true_2 = y_true[j]      
      if y_true_1 == y_true_2:
        continue
      y_pred_2 = y_pred[j]
      total_pairs += 1
      if y_pred_1 == y_pred_2:
        sum_score += 0.5
        continue
      concord = np.sign(y_true_1 - y_true_2) == np.sign(y_pred_1 - y_pred_2)
      sum_score += concord * 1.0
  return sum_score/total_pairs

def concordance_index3(y_true, y_pred):
  y_true_comb = np.array(list(itertools.combinations(y_true, 2)))
  y_pred_comb = np.array(list(itertools.combinations(y_pred, 2)))
  y_true_diff = np.sign(y_true_comb[:, 0] - y_true_comb[:, 1])
  y_pred_diff = np.sign(y_pred_comb[:, 0] - y_pred_comb[:, 1])
  valid_pairs = y_true_diff != 0.0
  #pdb.set_trace()
  #valid_pairs = np.invert(y_true_draw)
  raw_comparison = (y_true_diff * y_pred_diff + 1)/2
  scores = raw_comparison * valid_pairs
  return sum(scores)/sum(valid_pairs)

def concordance_index4(y_true, y_pred):
  y_true_1 = tf.expand_dims(y_true, 0)
  y_true_2 = tf.expand_dims(y_true, 1)
  y_pred_1 = tf.expand_dims(y_pred, 0)
  y_pred_2 = tf.expand_dims(y_pred, 1)
  #z = tf.reshape(tf.subtract(y_true_1, y_true_2))
  y_true_diff = tf.sign(tf.subtract(y_true_1, y_true_2))
  y_true_diff = tf.matrix_band_part(y_true_diff, 0, -1)
  y_pred_diff = tf.sign(tf.subtract(y_pred_1, y_pred_2))
  y_pred_diff = tf.matrix_band_part(y_pred_diff, 0, -1)
  ones = tf.ones_like(y_pred_diff)
  mask_a = tf.matrix_band_part(ones, 0, -1)
  mask_b = tf.matrix_band_part(ones, 0, 0)
  mask = tf.cast(mask_a - mask_b, dtype=tf.bool)
  y_pred_diff_flat = tf.boolean_mask(y_pred_diff, mask)
  y_true_diff_flat = tf.boolean_mask(y_true_diff, mask)
  valid_pairs = tf.not_equal(y_true_diff_flat, 0.0)
  valid_pairs = tf.cast(valid_pairs, dtype=tf.float64)
    
  raw_comparison = (y_true_diff_flat * y_pred_diff_flat + 1)/2
  scores = tf.multiply(raw_comparison, valid_pairs)
  quotient = tf.reduce_sum(scores)/tf.reduce_sum(valid_pairs)
  sess = tf.Session()
  quotient = sess.run(quotient)
  return quotient

if __name__=="__main__":
  #prot_desc_dict = load_prot_desc_dict(prot_desc_path)
  np.random.seed(seed=43)
  y_true = np.random.rand(10000)
  y_pred = np.random.rand(10000)
  y_true[300:500] = 2.0
  y_pred[200:400] = 2.0  
  time_start = time.time()
  result = concordance_index4(y_true, y_pred)
  time_end = time.time()
  print(result)
  print("time used:", time_end-time_start)
  np.random.seed(seed=24)
  y_true = np.random.rand(10000)
  y_pred = np.random.rand(10000)
  y_true[300:600] = 2.0
  y_pred[0:400] = 2.0
  time_start = time.time()
  result = concordance_index4(y_true, y_pred)
  time_end = time.time()
  print(result)
  print("time used:", time_end-time_start)