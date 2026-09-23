from pathlib import Path
import argparse, json
ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'art-production-spec'/'REFERENCE_ASSET_MAP.json'
REFS=ROOT/'art-work'/'references'
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    data=json.loads(MAP.read_text(encoding='utf-8')); total=0
    for group,cfg in data['groups'].items():
        folder=REFS/cfg['folder']; files=sorted(folder.glob('*')) if folder.exists() else []
        files=[p for p in files if p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}]
        print(f'{group}: {len(files)} reference(s)')
        for p in files: print(' ',p.relative_to(ROOT))
        total+=len(files)
    if args.check and total==0: raise SystemExit('No reference images found under art-work/references/.')
if __name__=='__main__': main()
