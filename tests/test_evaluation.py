"""Checks that protect the assignment's measurements and promotion decision."""
import importlib
import json
import unittest


def module(case, name):
    try:
        return importlib.import_module('eduassist.' + name)
    except ModuleNotFoundError:
        case.fail(f'The required eduassist.{name} module has not been implemented')


class EvaluationTests(unittest.TestCase):
    def test_cost_formula_keeps_input_and_output_rates_separate(self):
        economics = module(self, 'economics')
        costs = economics.token_costs(1000, 500, 2.0, 8.0)
        self.assertAlmostEqual(costs['input_cost_usd'], 0.002)
        self.assertAlmostEqual(costs['output_cost_usd'], 0.004)
        self.assertAlmostEqual(costs['total_cost_usd'], 0.006)
        with self.assertRaises(ValueError):
            economics.token_costs(-1, 10, 2.0, 8.0)

    def test_hosting_rates_reconcile_with_measured_compute_time(self):
        economics = module(self, 'economics')
        rates = economics.hosting_token_rates([
            {'input_tokens': 100, 'output_tokens': 50,
             'prompt_eval_seconds': 2.0, 'generation_seconds': 8.0}
        ], hourly_rate=0.134)
        costs = economics.token_costs(100, 50, *rates)
        self.assertAlmostEqual(costs['total_cost_usd'], 0.134 * 10 / 3600)

    def test_json_syntax_is_distinct_from_schema(self):
        evaluation = module(self, 'evaluation')
        cases = [
            ('{"answer":"Yes","confidence":"high","key_points":["One"]}', (1, 1)),
            ('{"answer":"Yes"}', (1, 0)),
            ('[]', (1, 0)),
            ('```json\n{}\n```', (0, 0)),
            ('{"answer":"Yes","confidence":"certain","key_points":["One"]}', (1, 0)),
            ('{"answer":"Yes","confidence":"high","key_points":["One"],"extra":0}', (1, 0)),
            ('{"answer":"a","answer":"b","confidence":"high","key_points":["One"]}', (0, 0)),
            ('NaN', (0, 0)),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(evaluation.json_checks(text), expected)

    def test_local_api_rejects_paid_remote_urls_and_credentials(self):
        config = module(self, 'config')
        self.assertEqual(config.local_api_url('http://127.0.0.1:8081/v1/chat/completions'),
                         'http://127.0.0.1:8081/v1/chat/completions')
        for url in ['https://api.openai.com/v1/chat/completions',
                    'http://example.com', 'http://user:pass@127.0.0.1:8081/v1/chat/completions',
                    'http://127.0.0.1:8081/other', 'http://127.0.0.1:8081/v1/chat/completions?x=1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                config.local_api_url(url)

    def test_promotion_requires_five_successes_and_full_schema_validity(self):
        evaluation = module(self, 'evaluation')
        base = {'request_count': 5, 'success_count': 5, 'valid_json': 1.0,
                'schema_valid_rate': 1.0, 'quality_score': 1.0,
                'avg_cost_per_request': 0.001, 'avg_latency_seconds': 1.0}
        good = dict(base, prompt_version='v3')
        incomplete = dict(base, prompt_version='v1', request_count=4)
        invalid = dict(base, prompt_version='v2', schema_valid_rate=0.8)
        self.assertEqual(evaluation.choose_prompt([incomplete, invalid, good]), 'v3')
        self.assertIsNone(evaluation.choose_prompt([incomplete, invalid]))

    def test_failed_request_is_counted_in_json_denominator(self):
        evaluation = module(self, 'evaluation')
        rows = [{'response_status': 'success', 'valid_json': 1, 'schema_valid': 1,
                 'quality_score': 1, 'latency_seconds': 1, 'input_tokens': 20,
                 'output_tokens': 10, 'total_cost_usd': 0.01} for _ in range(4)]
        rows.append(dict(rows[0], response_status='error', valid_json=0, schema_valid=0,
                         input_tokens=None, output_tokens=None, total_cost_usd=None))
        summary = evaluation.summarize('v3', rows)
        self.assertEqual(summary['request_count'], 5)
        self.assertEqual(summary['success_count'], 4)
        self.assertEqual(summary['valid_json'], 0.8)
        self.assertAlmostEqual(summary['avg_input_tokens'], 20)


if __name__ == '__main__':
    unittest.main()
