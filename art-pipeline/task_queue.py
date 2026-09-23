from pathlib import Path
from collections import Counter
import json
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'art-production-spec'/'ART_ASSET_MANIFEST.json'
OUT=ROOT/'art-work'/'reports'/'production-queue.json'
ANCHORS={'B01','B02','B03','B04','B07','B11','C01','C02','C03','E01'}
ORDER={'P0':0,'P1':1,'P2':2,'P3':3}
def main():
    assets=json.loads(MANIFEST.read_text(encoding='utf-8'))['assets']
    assets=sorted(assets,key=lambda a:(0 if a['id'] in ANCHORS else 1,ORDER.get(a['priority'],9),a['id']))
    queue=[]
    for a in assets:
        queue.append({'asset_id':a['id'],'key':a['key'],'priority':a['priority'],'status':a['status'],'phase':'STYLE_ANCHOR' if a['id'] in ANCHORS else 'BATCH','dependencies':['B01'] if a['category']=='character' and a['id']!='B01' else []})
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({'total':len(queue),'by_priority':dict(Counter(x['priority'] for x in queue)),'queue':queue,'gating':{'style_anchor_required':True,'p0_p1_human_review_required':True,'do_not_integrate_unapproved':True}},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'queue: {len(queue)} assets'); print(f'report: {OUT}')
if __name__=='__main__': main()
