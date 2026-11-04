"""Malformed local replies must never appear as successful, free requests."""
import copy
import unittest
from test_evaluation import module


class ReplyTests(unittest.TestCase):
    def reply(self):
        return {'model':'local-test','choices':[{'message':{'content':'An answer.'},
                'finish_reason':'stop'}],
                'usage':{'prompt_tokens':12,'completion_tokens':5,'total_tokens':17}}

    def test_provider_tokenizer_usage_is_required(self):
        api = module(self, 'api')
        self.assertEqual(api.parse_reply(self.reply())['total_tokens'], 17)
        for patch in [{}, {'prompt_tokens':-1,'completion_tokens':5,'total_tokens':4},
                      {'prompt_tokens':12,'completion_tokens':5,'total_tokens':99}]:
            reply = self.reply()
            reply['usage'] = patch
            with self.assertRaises(ValueError):
                api.parse_reply(reply)

    def test_truncation_is_not_a_success(self):
        api = module(self, 'api')
        reply = self.reply()
        reply['choices'][0]['finish_reason'] = 'length'
        self.assertEqual(api.parse_reply(reply)['response_status'], 'incomplete')

    def test_missing_timings_use_explicit_fallback(self):
        api = module(self, 'api')
        self.assertIsNone(api.parse_reply(self.reply())['prompt_eval_seconds'])
        reply = self.reply()
        reply['timings'] = {'prompt_ms': 20, 'predicted_ms': 120}
        self.assertEqual(api.parse_reply(reply)['generation_seconds'], 0.12)


if __name__ == '__main__':
    unittest.main()
