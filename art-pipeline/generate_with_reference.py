from pathlib import Path
import argparse,os,base64
from openai import OpenAI
ROOT=Path(__file__).resolve().parents[1]; PROMPTS=ROOT/'art-work'/'prompts'; OUT=ROOT/'art-work'/'generated'
def main():
    p=argparse.ArgumentParser(); p.add_argument('--id',required=True); p.add_argument('--reference',required=True); p.add_argument('--size',default='1536x1024'); p.add_argument('--quality',default='high'); p.add_argument('--model',default=os.getenv('OPENAI_IMAGE_MODEL','gpt-image-2')); a=p.parse_args()
    if not os.getenv('OPENAI_API_KEY'): raise SystemExit('OPENAI_API_KEY is not set')
    prompt=next(PROMPTS.glob(f'{a.id}_*.txt'),None)
    if not prompt: raise SystemExit(f'No prompt found for {a.id}; run prompt_builder.py first.')
    ref=ROOT/a.reference
    if not ref.exists(): raise SystemExit(f'Reference not found: {ref}')
    OUT.mkdir(parents=True,exist_ok=True); client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],base_url=os.getenv('OPENAI_BASE_URL') or None)
    with ref.open('rb') as image_file:
        result=client.images.edit(model=a.model,image=image_file,prompt=prompt.read_text(encoding='utf-8'),size=a.size,quality=a.quality)
    item=result.data[0]
    if not getattr(item,'b64_json',None): raise RuntimeError('Image edit returned no b64_json')
    target=OUT/f'{a.id}.png'; target.write_bytes(base64.b64decode(item.b64_json)); print(f'OK {a.id}: {target}')
if __name__=='__main__': main()
