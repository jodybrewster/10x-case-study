import argparse
import os
import sys

sys.dont_write_bytecode = True
from . import pipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser(prog="identity", description="Resolve one identity per real person.")
    ap.add_argument("--data", required=True, help="folder with the eight CSV files")
    ap.add_argument("--out", default=".", help="folder for identities.csv and review_queue.csv")
    ap.add_argument("--label-sample", help="also write a pairs-to-label CSV to this path")
    ap.add_argument("--label-auto", type=int, default=100, help="how many auto links to sample at random")
    a = ap.parse_args()
    res = pipeline.run(a.data)
    pipeline.write(res, a.out)
    if a.label_sample:
        from . import sample
        sample.write_sample(res, a.label_sample, n_auto=a.label_auto)
    print("\n".join(pipeline.summary(res)))
    print(f"wrote {os.path.join(a.out, 'identities.csv')} and {os.path.join(a.out, 'review_queue.csv')}")


main()
