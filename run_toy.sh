#!/usr/bin/env bash

############################### 
# Training a mt-dnn model
# Note that this is a toy setting and please refer our paper for detailed hyper-parameters.
############################### 

#python prepro.py
#python train.py
python train.py --task_def experiments/glue/mediqa_task_def_training.yml --data_dir ../data/canonical_data/bert_large_uncased/ --train_datasets mednli,rqe,mediqa,medquad --test_datasets mednli,rqe,mediqa