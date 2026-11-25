#!/usr/bin/env python3
import argparse, subprocess, sys
from pathlib import Path

def run(cmd):
    print('+',' '.join(map(str,cmd))); subprocess.run(cmd,check=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True,type=Path); ap.add_argument('--out',type=Path,default=Path('outputs')); ap.add_argument('--skip-hash-check',action='store_true'); args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]; py=sys.executable
    cmd=[py,str(root/'scripts'/'reproduce.py'),'--manifest',str(args.manifest),'--out',str(args.out)]
    if args.skip_hash_check: cmd.append('--skip-hash-check')
    run(cmd)
    run([py,str(root/'scripts'/'verify_expected.py'),'--actual',str(args.out/'results_v23.json'),'--expected',str(root/'expected'/'expected_results_v23.json')])
    run([py,str(root/'scripts'/'generate_figures.py'),'--outputs',str(args.out),'--out',str(args.out/'figures')])
if __name__=='__main__': main()
