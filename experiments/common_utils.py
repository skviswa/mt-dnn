# coding=utf-8
# Copyright (c) Microsoft. All rights reserved.
from data_utils import DataFormat


def dump_rows(rows, out_path, data_format, extra_features=[]):
    """
    output files should have following format
    :param rows:
    :param out_path:
    :return:
    """
    with open(out_path, "w", encoding="utf-8") as out_f:
        row0 = rows[0]
        # data_format = detect_format(row0)
        for row in rows:
            # assert data_format == detect_format(row), row
            if data_format == DataFormat.PremiseOnly:
                for col in ["uid", "label", "premise"]:
                    if "\t" in str(row[col]):
                        # import pdb
                        import re
                        row[col] = re.sub(r"[\n\t]*", "", row[col])
                        # pdb.set_trace()
                out_f.write("%s\t%s\t%s\n" % (row["uid"], row["label"], row["premise"]))
            elif data_format == DataFormat.PremiseAndOneHypothesis:
                for col in ["uid", "label", "premise", "hypothesis"]:
                    if "\t" in str(row[col]):
                        # import pdb
                        import re
                        row[col] = re.sub(r"[\n\t]*", "", row[col])
                        # pdb.set_trace()
                if extra_features:
                    features_cols = ["uid", "label", "premise", "hypothesis"] + extra_features
                    features = tuple([row[col] for col in features_cols])
                    format_str = ''.join(["%s\t"]*(len(features)-1))+"%s\n"
                    out_f.write(format_str % features)
                else:
                    out_f.write(
                        "%s\t%s\t%s\t%s\n"
                        % (row["uid"], row["label"], row["premise"], row["hypothesis"])
                    )
            elif data_format == DataFormat.PremiseAndMultiHypothesis:
                for col in ["uid", "label", "premise"]:
                    if "\t" in str(row[col]):
                        # import pdb
                        import re
                        row[col] = re.sub(r"[\n\t]*", "", row[col])
                        # pdb.set_trace()
                hypothesis = row["hypothesis"]
                for one_hypo in hypothesis:
                    if "\t" in str(one_hypo):
                        # import pdb
                        import re
                        row[col] = re.sub(r"[\n\t]*", "", row[col])
                        # pdb.set_trace()
                hypothesis = "\t".join(hypothesis)
                out_f.write(
                    "%s\t%s\t%s\t%s\t%s\n"
                    % (
                        row["uid"],
                        row["ruid"],
                        row["label"],
                        row["premise"],
                        hypothesis,
                    )
                )
            elif data_format == DataFormat.Seqence:
                for col in ["uid", "label", "premise"]:
                    if "\t" in str(row[col]):
                        # import pdb
                        import re
                        row[col] = re.sub(r"[\n\t]*", "", row[col])
                        # pdb.set_trace()
                out_f.write("%s\t%s\t%s\n" % (row["uid"], row["label"], row["premise"]))
            else:
                raise ValueError(data_format)
