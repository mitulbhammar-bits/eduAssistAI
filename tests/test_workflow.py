"""Offline checks use temporary fixtures, never submission measurements."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eduassist.config import ROOT, load_settings
from eduassist.economics import token_costs
from eduassist.experiment import assign_costs
from eduassist.reporting import report_sections, word_count


class WorkflowTests(unittest.TestCase):
    def test_missing_server_phase_timings_have_a_reconcilable_fallback(self):
        rows = [{'input_tokens':100, 'output_tokens':50, 'total_tokens':150,
                 'prompt_eval_seconds':None, 'generation_seconds':None,
                 'latency_seconds':10.0}]
        settings = load_settings()
        pricing = assign_costs(rows, settings)
        self.assertEqual(pricing['method'], 'pooled_wall_clock_hosting_estimate')
        self.assertAlmostEqual(rows[0]['total_cost_usd'], settings['hosting']['usd_per_hour'] * 10 / 3600)

    def test_draft_and_measured_report_lengths_and_configuration(self):
        draft, measured = report_sections()
        self.assertFalse(measured)
        self.assertTrue(500 <= word_count(draft) <= 700)
        settings = load_settings()
        settings['model'] = 'my-local-model'
        settings['hosting']['usd_per_hour'] = 0.25
        summaries = [dict(prompt_version=v, valid_json=1.0 if v=='v3' else 0.0,
            schema_valid_rate=1.0 if v=='v3' else 0.0, avg_cost_per_request=0.0001,
            projected_monthly_cost_usd=1.0, avg_latency_seconds=2.0,
            avg_input_tokens=100, avg_output_tokens=50, quality_score=1.0) for v in ('v1','v2','v3')]
        rows=[dict(prompt_version='v1', response_status='success', question_id='Q1',
                   latency_seconds=2.0,output_tokens=50)]
        metadata={'production_candidate':'v3','settings':settings,
                  'effective_pricing':{'input_rate':0.1,'output_rate':0.2}}
        sections, measured = report_sections(rows,summaries,metadata)
        text=' '.join(p for _,p in sections)
        self.assertTrue(measured)
        self.assertTrue(500 <= word_count(sections) <= 700)
        self.assertGreaterEqual(word_count([sections[4]]),150)
        self.assertIn('my-local-model',text)
        self.assertIn('0.25/hour',text)

    def test_offline_schedule_contains_each_prompt_question_pair_once(self):
        from eduassist import experiment
        templates, questions = experiment.read_inputs()
        registry={v:{'version':i+1,'uri':f'prompts:/test/{i+1}'}
                  for i,v in enumerate(templates)}
        calls=[]
        def fixture_call(prompt, settings):
            calls.append(prompt)
            text=json.dumps({'answer':'training unseen regularization true positive false positive false negative redundancy integrity tables gradient learning rate opposite labeled classification clustering',
                             'confidence':'high','key_points':['Offline unit-test fixture']})
            return dict(response_status='success',response_text=text,finish_reason='stop',
                input_tokens=100,output_tokens=50,total_tokens=150,prompt_eval_seconds=0.1,
                generation_seconds=0.9,latency_seconds=1.0,start_time_utc='test',
                end_time_utc='test',http_status=200,model_returned='fixture',error_type=''), {'fixture':True}
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            (target/'reports').mkdir()
            with patch.object(experiment,'ROOT',target), \
                 patch.object(experiment,'read_inputs',return_value=(templates,questions)), \
                 patch.object(experiment.tracking,'register_prompts',return_value=registry), \
                 patch.object(experiment.tracking,'log_results',return_value={}), \
                 patch.object(experiment.tracking,'promote',return_value={'verified':True}), \
                 patch.object(experiment,'call_llm',side_effect=fixture_call), \
                 patch('builtins.print'):
                from eduassist.files import save_json
                save_json(target/'reports/prompt_registry.json', registry)
                rows,summaries,metadata=experiment.run_experiment()
            self.assertEqual(len(calls),15)
            self.assertEqual(len({(r['question_id'],r['prompt_version']) for r in rows}),15)
            self.assertTrue(all(s['request_count']==5 for s in summaries))
            self.assertTrue(all(s['valid_json']==1 for s in summaries))
            self.assertTrue((target/'latency_tokens_cost.csv').exists())


if __name__ == '__main__':
    unittest.main()
