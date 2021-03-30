#! /bin/sh
python experiments/glue/glue_prepro.py --root_dir /Users/ksubramanian2/Documents/Clinical_QA_Datasets --mediqa_gt_dir /Users/ksubramanian2/Documents/CQA_Example/data --glue_dataset none --mediqa_dataset all --other_dataset none
python prepro_std.py --model bert-large-uncased --root_dir data/canonical_data --task_def experiments/glue/mediqa_task_def.yml --do_lower_case $1
