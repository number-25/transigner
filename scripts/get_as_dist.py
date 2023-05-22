#!/usr/bin/env python

import pysam
import sys
from time import strftime

primary = dict()
secondary = dict()
score_dist = dict()


def load_aln(aln_fn):
    unmapped = 0
    unique = 0
    global primary
    global secondary
    qname_prev = ""
    with pysam.AlignmentFile(aln_fn, 'rb') as fh:
        for brec in fh:
            if brec.is_unmapped:
                unmapped += 1
            else:
                qname_curr = brec.query_name
                if qname_prev != qname_curr:
                    if qname_prev != "":
                        if len(secondary_l) == 0:
                            unique += 1
                        secondary[qname_prev] = secondary_l
                    secondary_l = list()
                    score = int(brec.get_tag("AS"))
                    if not brec.is_secondary:
                        primary[qname_curr] = score
                    else:
                        secondary_l.append(score)
                    qname_prev = qname_curr
                else:
                    score = int(brec.get_tag("AS"))
                    if not brec.is_secondary:
                        primary[qname_curr] = score
                    else:
                        secondary_l.append(score)
    if len(secondary_l) == 0:
        unique += 1
    secondary[qname_prev] = secondary_l
    return unmapped, unique


def get_score_dist(out_fh, out_raw_fh):
    global primary
    global secondary
    for qname in primary.keys():
        pri_score = primary[qname]
        sec_l = secondary[qname]
        sec_l.sort()
        # focus on multi-mapped reads for now
        sec_frac_l = list()
        if pri_score == 0:
            print("primary alignment score equals 0; skipping read: " + qname)
            continue
        if len(sec_l) > 0:
            for sec in sec_l:
                sec_frac = (sec - pri_score) / pri_score
                sec_frac_l.append(sec_frac)
            sec_min = min(sec_frac_l)
            sec_max = max(sec_frac_l)
            sec_mean = sum(sec_frac_l) / len(sec_frac_l)
            out_fh.write(qname + "\t" + str(pri_score) + "\t" + str(sec_min) + "\t" + str(sec_max)
                         + "\t" + str(sec_mean) + "\t(")
            for frac in sec_frac_l:
                out_fh.write(str(frac) + ",")
                # if frac == -1566:
                #     print("hello")
                out_raw_fh.write(str(frac) + "\n")
            out_fh.write(")\n")


def main(aln_fn, out_fn, out_raw_fn):
    print(strftime("%Y-%m-%d %H:%M:%S | ") + "Loading alignment file")
    unmapped, unique = load_aln(aln_fn)
    print("# of unmapped reads: " + str(unmapped))
    print("# of uniquely-mapped reads: " + str(unique))
    out_fh = open(out_fn, 'w')
    out_fh.write("read_id\tpri\tsec_min\tsec_max\tsec_mean\tsec_raw\n")
    out_raw_fh = open(out_raw_fn, 'w')
    out_raw_fh.write("secondary_frac\n")
    print(strftime("%Y-%m-%d %H:%M:%S | ") + "Obtaining score distribution")
    get_score_dist(out_fh, out_raw_fh)
    out_fh.close()
    out_raw_fh.close()
    print(strftime("%Y-%m-%d %H:%M:%S | ") + "Finished writing distributions to the output file")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
