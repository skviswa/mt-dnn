import os
import argparse
import random
from sys import path

path.append(os.getcwd())
from experiments.common_utils import dump_rows
from data_utils.task_def import DataFormat
from data_utils.log_wrapper import create_logger
from experiments.glue.glue_utils import *
from experiments.glue.mediqa_utils import load_mediqa, load_mednli, load_medquad, load_rqe, test_mode
from experiments.glue.glue_label_map import GLOBAL_MAP
from experiments.glue.mediqa_utils import shuffle_rqe

logger = create_logger(__name__, to_disk=True, log_file="glue_prepro.log")

glue_datasets = ['cola', 'mnli', 'mrpc', 'qnli', 'qqp', 'rte', 'scitail', 'snli', 'sst', 'stsb', 'wnli']
mediqa_datasets = ['mednli', 'rqe', 'mediqa', 'medquad']
dataset_choices = ['all', 'none']


def generate_gt_csv(data, dump_path):  # now only use for first 2 tasks of MEDIQA
    header = "pair_id,label"
    with open(dump_path, "w") as writer:
        writer.write("{}\n".format(header))
        for sample in data:
            uid, label = sample["uid"], sample["label"]
            if "task3_qa" not in dump_path:
                writer.write("{},{}\n".format(uid, label))
            else:
                qid, aid = uid.split("____")
                writer.write("{},{},{}\n".format(qid, aid, label))


def parse_args():
    glue_dataset_choice = glue_datasets + dataset_choices
    mediqa_dataset_choice = mediqa_datasets + dataset_choices
    parser = argparse.ArgumentParser(
        description="Preprocessing GLUE/SNLI/SciTail/MEDIQA dataset."
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--root_dir", type=str, default="data")
    parser.add_argument("--mediqa_gt_dir", type=str, default="mediqa")
    parser.add_argument(
        "--old_glue",
        action="store_true",
        help="whether it is old GLUE, refer official GLUE webpage for details",
    )
    parser.add_argument('--glue_dataset', choices=glue_dataset_choice, type=str.lower,
                        help="Choose which dataset you want to preprocess from GLUE. Currently supporting only all or none")
    parser.add_argument('--mediqa_dataset', choices=mediqa_dataset_choice, type=str.lower,
                        help="Choose which dataset you want to preprocess from MEDIQA. Currently supporting only all or none")
    parser.add_argument('--other_dataset', choices=mediqa_dataset_choice, type=str.lower,
                        help="Choose which dataset you want to preprocess from SciTail and SNLI. Currently supporting only all or none")
    args = parser.parse_args()
    return args


def main(args):
    is_old_glue = args.old_glue
    root = args.root_dir
    mediqa_gt_dir = args.mediqa_gt_dir
    assert os.path.exists(root)

    train_name = "dev" if test_mode else "train"

    canonical_data_suffix = "canonical_data"
    canonical_data_root = os.path.join(root, canonical_data_suffix)
    if not os.path.isdir(canonical_data_root):
        os.mkdir(canonical_data_root)

    glue_dataset_flag = -1
    if args.glue_dataset == 'all':
        glue_dataset_flag = 1
    elif args.glue_dataset == 'none':
        glue_dataset_flag = 0
    else:
        print("Currently supporting only all/none options for GLUE! Please consider running again with either choice!")
        exit(1)

    mediqa_dataset_flag = -1
    if args.mediqa_dataset == 'all':
        mediqa_dataset_flag = 1
    elif args.mediqa_dataset == 'none':
        mediqa_dataset_flag = 0
    else:
        print(
            "Currently supporting only all/none options for MEDIQA! Please consider running again with either choice!")
        exit(1)

    other_dataset_flag = -1
    if args.other_dataset == 'all':
        other_dataset_flag = 1
    elif args.other_dataset == 'none':
        other_dataset_flag = 0
    else:
        print(
            "Currently supporting only all/none options for SciTail and SNLI! Please consider running again with either choice!")
        exit(1)

    if other_dataset_flag:
        ######################################
        # SNLI/SciTail Tasks
        ######################################
        scitail_train_path = os.path.join(root, "SciTailV1.1/tsv_format/scitail_1.0_train.tsv")
        scitail_dev_path = os.path.join(root, "SciTailV1.1/tsv_format/scitail_1.0_dev.tsv")
        scitail_test_path = os.path.join(root, "SciTailV1.1/tsv_format/scitail_1.0_test.tsv")

        snli_train_path = os.path.join(root, "SNLI/train.tsv")
        snli_dev_path = os.path.join(root, "SNLI/dev.tsv")
        snli_test_path = os.path.join(root, "SNLI/test.tsv")

        # Load data
        scitail_train_data = load_scitail(scitail_train_path)
        scitail_dev_data = load_scitail(scitail_dev_path)
        scitail_test_data = load_scitail(scitail_test_path)
        logger.info("Loaded {} SciTail train samples".format(len(scitail_train_data)))
        logger.info("Loaded {} SciTail dev samples".format(len(scitail_dev_data)))
        logger.info("Loaded {} SciTail test samples".format(len(scitail_test_data)))

        snli_train_data = load_snli(snli_train_path)
        snli_dev_data = load_snli(snli_dev_path)
        snli_test_data = load_snli(snli_test_path)
        logger.info("Loaded {} SNLI train samples".format(len(snli_train_data)))
        logger.info("Loaded {} SNLI dev samples".format(len(snli_dev_data)))
        logger.info("Loaded {} SNLI test samples".format(len(snli_test_data)))

        # BUILD SciTail
        scitail_train_fout = os.path.join(canonical_data_root, "scitail_train.tsv")
        scitail_dev_fout = os.path.join(canonical_data_root, "scitail_dev.tsv")
        scitail_test_fout = os.path.join(canonical_data_root, "scitail_test.tsv")
        dump_rows(
            scitail_train_data, scitail_train_fout, DataFormat.PremiseAndOneHypothesis
        )
        dump_rows(scitail_dev_data, scitail_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(scitail_test_data, scitail_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with scitail")

        # BUILD SNLI
        snli_train_fout = os.path.join(canonical_data_root, "snli_train.tsv")
        snli_dev_fout = os.path.join(canonical_data_root, "snli_dev.tsv")
        snli_test_fout = os.path.join(canonical_data_root, "snli_test.tsv")
        dump_rows(snli_train_data, snli_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(snli_dev_data, snli_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(snli_test_data, snli_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with snli")

    if glue_dataset_flag:
        ######################################
        # GLUE tasks
        ######################################
        multi_train_path = os.path.join(root, "MNLI/train.tsv")
        multi_dev_matched_path = os.path.join(root, "MNLI/dev_matched.tsv")
        multi_dev_mismatched_path = os.path.join(root, "MNLI/dev_mismatched.tsv")
        multi_test_matched_path = os.path.join(root, "MNLI/test_matched.tsv")
        multi_test_mismatched_path = os.path.join(root, "MNLI/test_mismatched.tsv")

        mrpc_train_path = os.path.join(root, "MRPC/train.tsv")
        mrpc_dev_path = os.path.join(root, "MRPC/dev.tsv")
        mrpc_test_path = os.path.join(root, "MRPC/test.tsv")

        qnli_train_path = os.path.join(root, "QNLI/train.tsv")
        qnli_dev_path = os.path.join(root, "QNLI/dev.tsv")
        qnli_test_path = os.path.join(root, "QNLI/test.tsv")

        qqp_train_path = os.path.join(root, "QQP/train.tsv")
        qqp_dev_path = os.path.join(root, "QQP/dev.tsv")
        qqp_test_path = os.path.join(root, "QQP/test.tsv")

        rte_train_path = os.path.join(root, "RTE/train.tsv")
        rte_dev_path = os.path.join(root, "RTE/dev.tsv")
        rte_test_path = os.path.join(root, "RTE/test.tsv")

        wnli_train_path = os.path.join(root, "WNLI/train.tsv")
        wnli_dev_path = os.path.join(root, "WNLI/dev.tsv")
        wnli_test_path = os.path.join(root, "WNLI/test.tsv")

        stsb_train_path = os.path.join(root, "STS-B/train.tsv")
        stsb_dev_path = os.path.join(root, "STS-B/dev.tsv")
        stsb_test_path = os.path.join(root, "STS-B/test.tsv")

        sst_train_path = os.path.join(root, "SST-2/train.tsv")
        sst_dev_path = os.path.join(root, "SST-2/dev.tsv")
        sst_test_path = os.path.join(root, "SST-2/test.tsv")

        cola_train_path = os.path.join(root, "CoLA/train.tsv")
        cola_dev_path = os.path.join(root, "CoLA/dev.tsv")
        cola_test_path = os.path.join(root, "CoLA/test.tsv")

        ######################################
        # Loading DATA
        ######################################

        multinli_train_data = load_mnli(multi_train_path)
        multinli_matched_dev_data = load_mnli(multi_dev_matched_path)
        multinli_mismatched_dev_data = load_mnli(multi_dev_mismatched_path)
        multinli_matched_test_data = load_mnli(multi_test_matched_path, is_train=False)
        multinli_mismatched_test_data = load_mnli(
            multi_test_mismatched_path, is_train=False
        )

        logger.info("Loaded {} MNLI train samples".format(len(multinli_train_data)))
        logger.info(
            "Loaded {} MNLI matched dev samples".format(len(multinli_matched_dev_data))
        )
        logger.info(
            "Loaded {} MNLI mismatched dev samples".format(
                len(multinli_mismatched_dev_data)
            )
        )
        logger.info(
            "Loaded {} MNLI matched test samples".format(len(multinli_matched_test_data))
        )
        logger.info(
            "Loaded {} MNLI mismatched test samples".format(
                len(multinli_mismatched_test_data)
            )
        )

        mrpc_train_data = load_mrpc(mrpc_train_path)
        mrpc_dev_data = load_mrpc(mrpc_dev_path)
        mrpc_test_data = load_mrpc(mrpc_test_path, is_train=False)
        logger.info("Loaded {} MRPC train samples".format(len(mrpc_train_data)))
        logger.info("Loaded {} MRPC dev samples".format(len(mrpc_dev_data)))
        logger.info("Loaded {} MRPC test samples".format(len(mrpc_test_data)))

        qnli_train_data = load_qnli(qnli_train_path)
        qnli_dev_data = load_qnli(qnli_dev_path)
        qnli_test_data = load_qnli(qnli_test_path, is_train=False)
        logger.info("Loaded {} QNLI train samples".format(len(qnli_train_data)))
        logger.info("Loaded {} QNLI dev samples".format(len(qnli_dev_data)))
        logger.info("Loaded {} QNLI test samples".format(len(qnli_test_data)))

        if is_old_glue:
            random.seed(args.seed)
            qnnli_train_data = load_qnnli(qnli_train_path)
            qnnli_dev_data = load_qnnli(qnli_dev_path)
            qnnli_test_data = load_qnnli(qnli_test_path, is_train=False)
            logger.info("Loaded {} QNLI train samples".format(len(qnnli_train_data)))
            logger.info("Loaded {} QNLI dev samples".format(len(qnnli_dev_data)))
            logger.info("Loaded {} QNLI test samples".format(len(qnnli_test_data)))

        qqp_train_data = load_qqp(qqp_train_path)
        qqp_dev_data = load_qqp(qqp_dev_path)
        qqp_test_data = load_qqp(qqp_test_path, is_train=False)
        logger.info("Loaded {} QQP train samples".format(len(qqp_train_data)))
        logger.info("Loaded {} QQP dev samples".format(len(qqp_dev_data)))
        logger.info("Loaded {} QQP test samples".format(len(qqp_test_data)))

        rte_train_data = load_rte(rte_train_path)
        rte_dev_data = load_rte(rte_dev_path)
        rte_test_data = load_rte(rte_test_path, is_train=False)
        logger.info("Loaded {} RTE train samples".format(len(rte_train_data)))
        logger.info("Loaded {} RTE dev samples".format(len(rte_dev_data)))
        logger.info("Loaded {} RTE test samples".format(len(rte_test_data)))

        wnli_train_data = load_wnli(wnli_train_path)
        wnli_dev_data = load_wnli(wnli_dev_path)
        wnli_test_data = load_wnli(wnli_test_path, is_train=False)
        logger.info("Loaded {} WNLI train samples".format(len(wnli_train_data)))
        logger.info("Loaded {} WNLI dev samples".format(len(wnli_dev_data)))
        logger.info("Loaded {} WNLI test samples".format(len(wnli_test_data)))

        sst_train_data = load_sst(sst_train_path)
        sst_dev_data = load_sst(sst_dev_path)
        sst_test_data = load_sst(sst_test_path, is_train=False)
        logger.info("Loaded {} SST train samples".format(len(sst_train_data)))
        logger.info("Loaded {} SST dev samples".format(len(sst_dev_data)))
        logger.info("Loaded {} SST test samples".format(len(sst_test_data)))

        cola_train_data = load_cola(cola_train_path, header=False)
        cola_dev_data = load_cola(cola_dev_path, header=False)
        cola_test_data = load_cola(cola_test_path, is_train=False)
        logger.info("Loaded {} COLA train samples".format(len(cola_train_data)))
        logger.info("Loaded {} COLA dev samples".format(len(cola_dev_data)))
        logger.info("Loaded {} COLA test samples".format(len(cola_test_data)))

        stsb_train_data = load_sts(stsb_train_path)
        stsb_dev_data = load_sts(stsb_dev_path)
        stsb_test_data = load_sts(stsb_test_path, is_train=False)
        logger.info("Loaded {} STS-B train samples".format(len(stsb_train_data)))
        logger.info("Loaded {} STS-B dev samples".format(len(stsb_dev_data)))
        logger.info("Loaded {} STS-B test samples".format(len(stsb_test_data)))

        # BUILD MNLI
        multinli_train_fout = os.path.join(canonical_data_root, "mnli_train.tsv")
        multinli_matched_dev_fout = os.path.join(
            canonical_data_root, "mnli_matched_dev.tsv"
        )
        multinli_mismatched_dev_fout = os.path.join(
            canonical_data_root, "mnli_mismatched_dev.tsv"
        )
        multinli_matched_test_fout = os.path.join(
            canonical_data_root, "mnli_matched_test.tsv"
        )
        multinli_mismatched_test_fout = os.path.join(
            canonical_data_root, "mnli_mismatched_test.tsv"
        )
        dump_rows(
            multinli_train_data, multinli_train_fout, DataFormat.PremiseAndOneHypothesis
        )
        dump_rows(
            multinli_matched_dev_data,
            multinli_matched_dev_fout,
            DataFormat.PremiseAndOneHypothesis,
        )
        dump_rows(
            multinli_mismatched_dev_data,
            multinli_mismatched_dev_fout,
            DataFormat.PremiseAndOneHypothesis,
        )
        dump_rows(
            multinli_matched_test_data,
            multinli_matched_test_fout,
            DataFormat.PremiseAndOneHypothesis,
        )
        dump_rows(
            multinli_mismatched_test_data,
            multinli_mismatched_test_fout,
            DataFormat.PremiseAndOneHypothesis,
        )
        logger.info("done with mnli")

        mrpc_train_fout = os.path.join(canonical_data_root, "mrpc_train.tsv")
        mrpc_dev_fout = os.path.join(canonical_data_root, "mrpc_dev.tsv")
        mrpc_test_fout = os.path.join(canonical_data_root, "mrpc_test.tsv")
        dump_rows(mrpc_train_data, mrpc_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(mrpc_dev_data, mrpc_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(mrpc_test_data, mrpc_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with mrpc")

        qnli_train_fout = os.path.join(canonical_data_root, "qnli_train.tsv")
        qnli_dev_fout = os.path.join(canonical_data_root, "qnli_dev.tsv")
        qnli_test_fout = os.path.join(canonical_data_root, "qnli_test.tsv")
        dump_rows(qnli_train_data, qnli_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(qnli_dev_data, qnli_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(qnli_test_data, qnli_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with qnli")

        if is_old_glue:
            qnli_train_fout = os.path.join(canonical_data_root, "qnnli_train.tsv")
            qnli_dev_fout = os.path.join(canonical_data_root, "qnnli_dev.tsv")
            qnli_test_fout = os.path.join(canonical_data_root, "qnnli_test.tsv")
            dump_rows(
                qnnli_train_data, qnli_train_fout, DataFormat.PremiseAndMultiHypothesis
            )
            dump_rows(qnnli_dev_data, qnli_dev_fout, DataFormat.PremiseAndMultiHypothesis)
            dump_rows(
                qnnli_train_data, qnli_test_fout, DataFormat.PremiseAndMultiHypothesis
            )
            logger.info("done with qnli")

        qqp_train_fout = os.path.join(canonical_data_root, "qqp_train.tsv")
        qqp_dev_fout = os.path.join(canonical_data_root, "qqp_dev.tsv")
        qqp_test_fout = os.path.join(canonical_data_root, "qqp_test.tsv")
        dump_rows(qqp_train_data, qqp_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(qqp_dev_data, qqp_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(qqp_test_data, qqp_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with qqp")

        rte_train_fout = os.path.join(canonical_data_root, "rte_train.tsv")
        rte_dev_fout = os.path.join(canonical_data_root, "rte_dev.tsv")
        rte_test_fout = os.path.join(canonical_data_root, "rte_test.tsv")
        dump_rows(rte_train_data, rte_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rte_dev_data, rte_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rte_test_data, rte_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with rte")

        wnli_train_fout = os.path.join(canonical_data_root, "wnli_train.tsv")
        wnli_dev_fout = os.path.join(canonical_data_root, "wnli_dev.tsv")
        wnli_test_fout = os.path.join(canonical_data_root, "wnli_test.tsv")
        dump_rows(wnli_train_data, wnli_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(wnli_dev_data, wnli_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(wnli_test_data, wnli_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with wnli")

        sst_train_fout = os.path.join(canonical_data_root, "sst_train.tsv")
        sst_dev_fout = os.path.join(canonical_data_root, "sst_dev.tsv")
        sst_test_fout = os.path.join(canonical_data_root, "sst_test.tsv")
        dump_rows(sst_train_data, sst_train_fout, DataFormat.PremiseOnly)
        dump_rows(sst_dev_data, sst_dev_fout, DataFormat.PremiseOnly)
        dump_rows(sst_test_data, sst_test_fout, DataFormat.PremiseOnly)
        logger.info("done with sst")

        cola_train_fout = os.path.join(canonical_data_root, "cola_train.tsv")
        cola_dev_fout = os.path.join(canonical_data_root, "cola_dev.tsv")
        cola_test_fout = os.path.join(canonical_data_root, "cola_test.tsv")
        dump_rows(cola_train_data, cola_train_fout, DataFormat.PremiseOnly)
        dump_rows(cola_dev_data, cola_dev_fout, DataFormat.PremiseOnly)
        dump_rows(cola_test_data, cola_test_fout, DataFormat.PremiseOnly)
        logger.info("done with cola")

        stsb_train_fout = os.path.join(canonical_data_root, "stsb_train.tsv")
        stsb_dev_fout = os.path.join(canonical_data_root, "stsb_dev.tsv")
        stsb_test_fout = os.path.join(canonical_data_root, "stsb_test.tsv")
        dump_rows(stsb_train_data, stsb_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(stsb_dev_data, stsb_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(stsb_test_data, stsb_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with stsb")

    if mediqa_dataset_flag:
        ######################################
        # MedNLI Task
        ######################################

        mednli_train_path = os.path.join(
            root, "mednli-dataset/mli_{}_v1.jsonl".format(train_name)
        )  #'mediqa/task1_mednli/mli_{}_v1.jsonl'
        mednli_dev_path = os.path.join(
            root, "mednli-dataset/mli_dev_v1.jsonl"
        )  #'mediqa/task1_mednli/mli_dev_v1.jsonl'
        mednli_test_path = os.path.join(
            root, "mednli-dataset/mli_test_v1.jsonl"
        )  #'mediqa/task1_mednli/mli_test_v1.jsonl'
        mednli_realtest_path = os.path.join(
            root, "mednli-dataset/mednli_bionlp19_shared_task.jsonl"
        )  #'mediqa/task1_mednli/mednli_bionlp19_shared_task.jsonl'

        ######################################
        # RQE Task
        ######################################
        rqe_train_path = os.path.join(
            root, "RQE_Data_AMIA2016/RQE_Train_8588_AMIA2016.xml"
        )  #'mediqa/task2_rqe/RQE_Train_8588_AMIA2016.xml'
        rqe_dev_path = os.path.join(
            root, "RQE_Data_AMIA2016/RQE_Test_302_pairs_AMIA2016.xml"
        )  #'mediqa/task2_rqe/RQE_Test_302_pairs_AMIA2016.xml'
        rqe_test_path = os.path.join(
            root, "MEDIQA2019/MEDIQA_Task2_RQE/MEDIQA2019-Task2-RQE-TestSet.xml"
        )  #'mediqa/task2_rqe/MEDIQA_Task2_RQE_TestSet.xml'

        ######################################
        # QA Task
        ######################################

        mediqa_dir = os.path.join(root, "MEDIQA2019/MEDIQA_Task3_QA/")  #'mediqa/task3_qa/'
        ######################################
        # MedQuAD Task
        ######################################

        medquad_dir = os.path.join(root, "MedQuAD/")  #'mediqa/MedQuAD/'

    #################### MEDIQA 2019 DATA LOAD ################################
        mednli_train_data = load_mednli(mednli_train_path, GLOBAL_MAP["mednli"])
        mednli_dev_data = load_mednli(mednli_dev_path, GLOBAL_MAP["mednli"])
        mednli_test_data = load_mednli(mednli_test_path, GLOBAL_MAP["mednli"])
        mednli_realtest_data = load_mednli(mednli_realtest_path, GLOBAL_MAP["mednli"])
        mednli_train_data = mednli_train_data + mednli_dev_data
        mednli_dev_data = mednli_test_data
        mednli_test_data = mednli_realtest_data
        logger.info("Loaded {} MedNLI train samples".format(len(mednli_train_data)))
        logger.info("Loaded {} MedNLI dev samples".format(len(mednli_dev_data)))
        logger.info("Loaded {} MedNLI test samples".format(len(mednli_test_data)))

        rqe_train_data = load_rqe(rqe_train_path, GLOBAL_MAP["rqe"])
        rqe_dev_data = load_rqe(rqe_dev_path, GLOBAL_MAP["rqe"])
        rqe_test_data = load_rqe(rqe_test_path, GLOBAL_MAP["rqe"])
        logger.info("Loaded {} rqe train samples".format(len(rqe_train_data)))
        logger.info("Loaded {} rqe dev samples".format(len(rqe_dev_data)))
        logger.info("Loaded {} rqe test samples".format(len(rqe_test_data)))

        # shuffled version of RQE data
        rqe_shuff_train_data, rqe_shuff_dev_data, rqe_shuff_test_data = shuffle_rqe(
            rqe_train_data, rqe_dev_data, rqe_test_data
        )

        logger.info("Loaded {} rqe_shuff train samples".format(len(rqe_shuff_train_data)))
        logger.info("Loaded {} rqe_shuff dev samples".format(len(rqe_shuff_dev_data)))
        logger.info("Loaded {} rqe_shuff test samples".format(len(rqe_shuff_test_data)))

        (
            mediqa_train_data,
            mediqa_dev_data,
            mediqa_old_dev_data,
            mediqa_test_data,
            mediqa_split_data,
        ) = load_mediqa(mediqa_dir, GLOBAL_MAP["mediqa"], False)

        # mediqa_dev_data = load_mediqa(mediqa_dir,GLOBAL_MAP['mediqa'], is_train=False)
        logger.info("Loaded {} mediqa train samples".format(len(mediqa_train_data)))
        logger.info("Loaded {} mediqa dev samples".format(len(mediqa_dev_data)))
        logger.info("Loaded {} mediqa test samples".format(len(mediqa_test_data)))
        # pdb.set_trace()
        for pair in mediqa_split_data:
            train_data, dev_data = pair
            logger.info(
                "Loaded {},{} mediqa splitted samples".format(
                    len(train_data), len(dev_data)
                )
            )

        mednli_gt_path = os.path.join(mediqa_gt_dir, "mediqa/task1_mednli/gt_dev.csv")
        generate_gt_csv(mednli_dev_data, mednli_gt_path)
        rqe_gt_path = os.path.join(mediqa_gt_dir, "mediqa/task2_rqe/gt_dev.csv")
        generate_gt_csv(rqe_dev_data, rqe_gt_path)
        mediqa_gt_path = os.path.join(mediqa_gt_dir, "mediqa/task3_qa/gt_dev.csv")
        generate_gt_csv(mediqa_dev_data, mediqa_gt_path)

        add_num = 2
        medquad_train_data, medquad_dev_data = load_medquad(
            medquad_dir, negative_num=add_num
        )
        logger.info("Loaded {} medquad train samples".format(len(medquad_train_data)))
        logger.info("Loaded {} medquad dev samples".format(len(medquad_dev_data)))
        #############################################################################


        # # BUILD mednli
        mednli_train_fout = os.path.join(canonical_data_root, "mednli_train.tsv")
        mednli_dev_fout = os.path.join(canonical_data_root, "mednli_dev.tsv")
        mednli_test_fout = os.path.join(canonical_data_root, "mednli_test.tsv")
        dump_rows(mednli_train_data, mednli_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(mednli_dev_data, mednli_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(mednli_test_data, mednli_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with mednli")

        # BUILD rqe
        rqe_train_fout = os.path.join(canonical_data_root, "rqe_train.tsv")
        rqe_dev_fout = os.path.join(canonical_data_root, "rqe_dev.tsv")
        rqe_test_fout = os.path.join(canonical_data_root, "rqe_test.tsv")
        dump_rows(rqe_train_data, rqe_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rqe_dev_data, rqe_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rqe_test_data, rqe_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with rqe")

        rqe_shuff_train_fout = os.path.join(canonical_data_root, "rqe_shuff_train.tsv")
        rqe_shuff_dev_fout = os.path.join(canonical_data_root, "rqe_shuff_dev.tsv")
        rqe_shuff_test_fout = os.path.join(canonical_data_root, "rqe_shuff_test.tsv")
        dump_rows(rqe_shuff_train_data, rqe_shuff_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rqe_shuff_dev_data, rqe_shuff_dev_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(rqe_shuff_test_data, rqe_shuff_test_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with rqe_shuff")

        extra_features = ["score", "rank"]
        mediqa_train_fout = os.path.join(canonical_data_root, "mediqa_train.tsv")
        mediqa_dev_fout = os.path.join(canonical_data_root, "mediqa_dev.tsv")
        mediqa_test_fout = os.path.join(canonical_data_root, "mediqa_test.tsv")
        dump_rows(mediqa_train_data, mediqa_train_fout, DataFormat.PremiseAndOneHypothesis, extra_features=extra_features)
        dump_rows(mediqa_dev_data, mediqa_dev_fout, DataFormat.PremiseAndOneHypothesis, extra_features=extra_features)
        dump_rows(mediqa_test_data, mediqa_test_fout, DataFormat.PremiseAndOneHypothesis, extra_features=extra_features)
        for sidx, (train_data, dev_data) in enumerate(mediqa_split_data):
            mediqa_train_fout = os.path.join(
                canonical_data_root, "mediqa_{}_train.tsv".format(sidx)
            )
            mediqa_dev_fout = os.path.join(canonical_data_root, "mediqa_{}_dev.tsv".format(sidx))
            dump_rows(train_data, mediqa_train_fout, DataFormat.PremiseAndOneHypothesis, extra_features=extra_features)
            dump_rows(dev_data, mediqa_dev_fout, DataFormat.PremiseAndOneHypothesis, extra_features=extra_features)
        logger.info("done with mediqa")

        medquad_train_fout = os.path.join(canonical_data_root, "medquad_train.tsv")
        medquad_dev_fout = os.path.join(canonical_data_root, "medquad_dev.tsv")
        dump_rows(medquad_train_data, medquad_train_fout, DataFormat.PremiseAndOneHypothesis)
        dump_rows(medquad_dev_data, medquad_dev_fout, DataFormat.PremiseAndOneHypothesis)
        logger.info("done with medquad")


if __name__ == "__main__":
    args = parse_args()
    main(args)
