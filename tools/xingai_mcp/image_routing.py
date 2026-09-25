"""Deterministic, conservative bilingual rubric. No API calls or model IDs."""
import re
import tomllib
from pathlib import Path

CAPS = dict(composition=20, character=20, scene=15, multi_object=15,
            material_lighting=10, text_ui=10, style_consistency=10)
TIERS = ('simple', 'medium', 'complex')


def tier_for_score(score):
    return 'simple' if score <= 30 else 'medium' if score <= 65 else 'complex'


def analyze(task, asset_id, quality_hint=None, has_reference=False):
    text = (task + ' ' + (quality_hint or '')).lower()
    # Ignore explicit negative clauses; use punctuation to bound their scope.
    text = re.sub(r'(?:不要|无需|不需要|禁止|without\b|no\b)[^，。；,;.\n]*', '', text)
    def has(pattern):
        return bool(re.search(pattern, text))
    character = has(r'角色|人物|鹈鹕|character|person|pelican|portrait')
    scene = has(r'场景|办公室|环境|scene|office|environment|landscape')
    multi = has(r'多对象|多个|多角色|互动|multiple|multi.object|interaction|interacting')
    complex_scene = scene and has(r'复杂|完整|全景|complex|complete|panoram')
    complex_light = has(r'复杂光影|复杂.*材质|complex lighting|complex.*material')
    style = has_reference or has(r'风格一致|保持.*风格|b01|style consist|identity|match.*style')
    b = dict(composition=4, character=0, scene=0, multi_object=0,
             material_lighting=0, text_ui=0, style_consistency=0)
    if character:
        b.update(composition=10, character=16, material_lighting=5)
    if scene:
        b.update(composition=max(b['composition'],12), scene=10, multi_object=5,
                 material_lighting=max(b['material_lighting'],5))
    if complex_scene:
        b.update(composition=20,scene=15,multi_object=15,material_lighting=8)
    if multi:
        b['multi_object']=15
        b['composition']=max(16,b['composition'])
        if character: b['character']=20
    if has(r'透视|前景|中景|背景层|perspective|foreground|layered composition'):
        b['composition']=max(16,b['composition'])
    if has(r'材质|光影|lighting|texture|material'):
        b['material_lighting']=max(6,b['material_lighting'])
    if complex_light: b['material_lighting']=10
    if has(r'文字|排版|\bui\b|typography|lettering|text layout'):
        b['text_ui']=10
    if style: b['style_consistency']=10
    reasons=[]
    importance='normal'
    asset=asset_id.upper()
    # Manifest IDs impose a floor, even if the caller describes them as cheap/simple.
    if re.fullmatch(r'[ABCEM]\d{2}',asset) or style or has(r'正式.*美术|核心角色|核心场景|宣传图|主要视觉资产|首次.*风格|promotional|main visual|production.*art|core character|core scene|first.*style'):
        importance='important';reasons.append('正式/核心资产或严格风格一致性：至少 MEDIUM')
    if asset in {'B01','C01','E01','M01'} or complex_scene or complex_light or (multi and character) or has(r'风格锚点|主角色.*立绘|核心宣传|最重要.*视觉|最高质量|最强模型|style anchor|main character.*(sheet|portrait)|key promotional|most important.*visual|highest quality|strongest model'):
        importance='critical';reasons.append('关键视觉资产/复杂场景或最高质量要求：至少 MEDIUM')
    if not any((character,scene,multi,style,has(r'图标|装饰|icon|decoration|leaf|叶|圆|circle|simple|简单'))):
        # Unknown wording is not silently interpreted as easy.
        importance=max(importance,'important',key=lambda x: {'normal':0,'important':1,'critical':2}[x])
        reasons.append('描述缺乏可识别难度信息：保守使用至少 MEDIUM')
    score=sum(b.values());base=tier_for_score(score)
    floor={'normal':'simple','important':'medium','critical':'medium'}[importance]
    tier=TIERS[max(TIERS.index(base),TIERS.index(floor))]
    reasons.insert(0,f'规则评分 {score}/100，基础档位 {base.upper()}')
    return dict(asset_id=asset_id,complexity_score=score,complexity_breakdown=b,
                importance=importance,difficulty=tier,selected_tier=tier,selection_reason='；'.join(reasons),
                routing_version='2.0',scoring_method='deterministic bilingual rubric',
                quota_policy='one image, one POST, no retry or fallback')


def load_pool(path: Path):
    if path.stat().st_size > 65536:
        raise ValueError('Pool configuration too large')
    data=tomllib.loads(path.read_text(encoding='utf-8-sig'))
    pool=data.get('image_models',{})
    if set(pool)!=set(TIERS) or any(not isinstance(v,dict) or set(v)!={'id'} or not isinstance(v['id'],str) or not v['id'].strip() for v in pool.values()):
        raise ValueError('Pool needs simple/medium/complex tables containing model IDs')
    pool={tier: row['id'] for tier,row in pool.items()}
    evidence=data.get('verification',{})
    if not isinstance(evidence,dict): raise ValueError('Invalid verification mapping')
    return pool,evidence
