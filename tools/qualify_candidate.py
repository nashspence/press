"""Inspect candidate objects as data using installed core; never import candidate code."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from guavajam_core.publication_protocol import oid, run
from guavajam_core.qualify_assets import qualify
from guavajam_core.check_publications import check


def qualify_candidate(repo, revision):
    oid(revision)
    if run(repo,'rev-parse','HEAD').decode().strip()!=revision:
        raise ValueError('Candidate HEAD differs')
    check(repo,'',online=False,all_history=True)
    paths=run(repo,'ls-tree','-r','--name-only','-z',revision).decode('utf-8').split('\0')
    works=sorted({match[1] for path in paths if (match:=re.fullmatch(r'works/([a-z0-9]+(?:-[a-z0-9]+)*)/manuscript\.md',path))})
    for work in works:
        qualify(repo,revision,work,require_retention=True)
    return {'revision':revision,'works':len(works),'privately_verified':True,'public_release':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(qualify_candidate(args.repo,args.revision),sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):
        print('Private candidate qualification failed; details omitted.',file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
