"""One measured request to an existing localhost model server; no downloads."""
import json
import math
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from .config import local_api_url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Inference redirects are disabled; use the local server URL.')


def parse_reply(reply):
    """Use server-reported counts from the actual model tokenizer, not characters."""
    usage = reply.get('usage', {})
    counts = [usage.get(key) for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')]
    if any(type(x) is not int or x < 0 for x in counts) or counts[0] + counts[1] != counts[2]:
        raise ValueError('Local server must provide consistent, non-negative tokenizer usage.')
    choice = reply['choices'][0]
    text = choice['message']['content']
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Local server returned no answer text.')
    finish = choice.get('finish_reason')
    timings = reply.get('timings', {})
    def seconds(key):
        value = timings.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            return None
        return value / 1000
    return {'response_text': text, 'response_status': 'success' if finish == 'stop' else 'incomplete',
            'finish_reason': finish, 'model_returned': reply.get('model', 'not reported'),
            'input_tokens': counts[0], 'output_tokens': counts[1], 'total_tokens': counts[2],
            'prompt_eval_seconds': seconds('prompt_ms'),
            'generation_seconds': seconds('predicted_ms')}


def call_llm(prompt, settings):
    """No retries: one measurement equals one HTTP request, including failures."""
    url = local_api_url(settings['endpoint_url'])
    payload = {'model': settings['model'], 'messages': [{'role': 'user', 'content': prompt}],
               'temperature': settings['temperature'], 'seed': settings['seed'],
               'max_tokens': settings['max_output_tokens'], 'stream': False,
               'cache_prompt': False}
    headers = {'Content-Type': 'application/json'}
    key = os.getenv(settings['local_api_key_env'], '')
    if key:
        headers['Authorization'] = 'Bearer ' + key
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    result = {'response_status': 'error', 'response_text': '', 'finish_reason': None,
              'input_tokens': None, 'output_tokens': None, 'total_tokens': None,
              'prompt_eval_seconds': None, 'generation_seconds': None,
              'http_status': None, 'error_type': '', 'model_returned': ''}
    started = datetime.now(timezone.utc).isoformat()
    clock_start = time.perf_counter()
    raw = None
    try:
        with opener.open(request, timeout=settings['timeout_seconds']) as response:
            result['http_status'] = response.status
            raw = json.load(response)
        result.update(parse_reply(raw))
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError) as error:
        # Record type only: error strings can contain server details or sensitive values.
        result['error_type'] = type(error).__name__
        if isinstance(error, urllib.error.HTTPError):
            result['http_status'] = error.code
    finally:
        result['latency_seconds'] = time.perf_counter() - clock_start
        result['start_time_utc'] = started
        result['end_time_utc'] = datetime.now(timezone.utc).isoformat()
    return result, raw
