#! /bin/sh
python experiments/glue/glue_prepro.py --root_dir /Users/ksubramanian2/Documents/Clinical_QA_Datasets --mediqa_gt_dir /Users/ksubramanian2/Documents/CQA_Example/data --glue_dataset none --mediqa_dataset all --other_dataset none
#Bert
python prepro_std.py --model bert-large-uncased --root_dir data/canonical_data --task_def experiments/glue/mediqa_task_def.yml --do_lower_case $1
#SciBert
python prepro_std.py --model ../bert_models/scibert_scivocab_uncased/ --result_dir scibert_uncased --root_dir data/canonical_data --task_def experiments/glue/mediqa_task_def.yml --do_lower_case $1
#BioBert
python prepro_std.py --model ../bert_models/biobert-base-cased-v1.1/ --result_dir biobert_cased --root_dir data/canonical_data --task_def experiments/glue/mediqa_task_def.yml --do_lower_case $1
#BlueBert
python prepro_std.py --model ../bert_models/NCBI_BERT_pubmed_mimic_uncased_L-12_H-768_A-12/ --result_dir bluebert_uncased --root_dir data/canonical_data --task_def experiments/glue/mediqa_task_def.yml --do_lower_case $1