import json
import unittest
from unittest.mock import patch
from image_routing import analyze, CAPS, tier_for_score
import server as s
from test_server import Contracts


class Routing(unittest.TestCase):
    def test_required_cases(self):
        cases=[('简单图标/小装饰','TEST_ICON',None,'simple'),
               ('普通角色','TEST_CHARACTER',None,'medium'),
               ('复杂角色 + 复杂场景','TEST_OFFICE',None,'complex'),
               ('简单图标','B01',None,'medium'),
               ('简单装饰','TEST_QUALITY','最高质量','medium'),
               ('简单图标','TEST_SAVE','节约额度','simple')]
        for task,asset,hint,tier in cases:
            r=analyze(task,asset,hint)
            self.assertEqual(r['selected_tier'],tier,r)
            self.assertEqual(r['complexity_score'],sum(r['complexity_breakdown'].values()))
            for key,score in r['complexity_breakdown'].items():self.assertLessEqual(score,CAPS[key])

    def test_boundaries_and_importance(self):
        for score,tier in [(0,'simple'),(30,'simple'),(31,'medium'),(65,'medium'),(66,'complex'),(100,'complex')]:
            self.assertEqual(tier_for_score(score),tier)
        for task,asset,hint in [('简单图标','B04',None),('保持B01风格的小装饰','TEST',None),('首次建立资产风格','TEST',None)]:
            self.assertEqual(analyze(task,asset,hint)['selected_tier'],'medium')
        for task in ['最高质量的小图标','使用最强模型','多角色互动场景','复杂光影和材质','主角色正式立绘']:
            self.assertIn(analyze(task,'TEST')['difficulty'], ('medium','complex'))
        self.assertEqual(analyze('简单图标，不要角色，不要文字','TEST')['selected_tier'],'simple')


class ProjectImage(Contracts):
    def setUp(self):
        super().setUp()
        self.here_patch = patch.object(s, 'HERE', self.root)
        self.here_patch.start()

    def tearDown(self):
        self.here_patch.stop()
        super().tearDown()

    def pool(self,verified=True):
        return ({'simple':'fixture-image','medium':'fixture-standard','complex':'fixture-pro'},
                {'fixture-image':{'origin':self.config.base,'generation_verified':verified,'source':'mock only'}})

    async def test_quota_one_post_one_image(self):
        with patch.object(s,'load_pool',return_value=self.pool()):
            r=await s.dispatch('xingai_generate_project_image',{'task':'简单图标，节约额度','asset_id':'TEST','output_path':'one.png'},self.api())
        self.assertTrue(r['success'],r)
        self.assertEqual(r['generated_count'],1)
        posts=[x for x in self.calls if x.method=='POST']
        self.assertEqual(len(posts),1)
        self.assertEqual(json.loads(posts[0].content)['n'],1)
        with patch.object(s,'load_pool',return_value=self.pool()):
            again=await s.dispatch('xingai_generate_project_image',{'task':'简单图标','asset_id':'TEST','output_path':'two.png'},self.api())
        self.assertEqual(again['error_type'],'asset_already_attempted')
        self.assertEqual(len([x for x in self.calls if x.method=='POST']),1)

    async def test_unverified_no_post_no_downgrade(self):
        with patch.object(s,'load_pool',return_value=self.pool(False)):
            r=await s.dispatch('xingai_generate_project_image',{'task':'简单图标','asset_id':'TEST','output_path':'one.png'},self.api())
        self.assertEqual(r['error_type'],'model_not_verified')
        self.assertEqual(r['generated_count'],0)
        self.assertFalse(self.calls)

    async def test_caller_cannot_override_tier(self):
        r=await s.dispatch('xingai_generate_project_image',{'task':'简单图标','asset_id':'B01','output_path':'one.png','selected_tier':'simple'},self.api())
        self.assertEqual(r['error_type'],'invalid_arguments')

    async def test_failure_does_not_retry(self):
        import httpx
        def fail(req):
            if req.method=='POST':
                self.calls.append(req)
                return httpx.Response(500)
            return self.handler(req)
        with patch.object(s,'load_pool',return_value=self.pool()):
            r=await s.dispatch('xingai_generate_project_image',{'task':'简单图标','asset_id':'TEST','output_path':'one.png'},self.api(fail))
        self.assertFalse(r['success'])
        self.assertEqual(len([x for x in self.calls if x.method=='POST']),1)
