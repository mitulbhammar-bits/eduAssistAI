"""Local configuration. This project cannot send inference to a paid provider."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = 'eduassist_llmops_assignment'
PROMPT_NAME = 'eduassist_academic_assistant'


def local_api_url(value=None):
    """Allow literal loopback only; no DNS, credentials, query or redirects."""
    url = value or os.getenv('LOCAL_LLM_URL', 'http://127.0.0.1:8081/v1/chat/completions')
    parts = urlsplit(url)
    if (parts.scheme != 'http' or parts.hostname not in {'127.0.0.1', '::1'}
            or parts.username or parts.password or parts.query or parts.fragment
            or parts.path != '/v1/chat/completions'):
        raise ValueError('LOCAL_LLM_URL must be a loopback HTTP chat-completions URL.')
    return url


def tracking_uri():
    """Always use this project's SQLite store, ignoring enterprise MLflow settings."""
    return 'sqlite:///' + str(ROOT / 'mlflow.db')


def load_settings(path=None):
    """Read ordinary, editable JSON. No secrets belong in the settings file."""
    path = Path(path) if path else ROOT / 'settings.json'
    settings = json.loads(path.read_text(encoding='utf-8'))
    settings['endpoint_url'] = local_api_url(os.getenv('LOCAL_LLM_URL') or settings['endpoint_url'])
    if not settings.get('model') or not isinstance(settings['model'], str):
        raise ValueError('Set a local model name in settings.json.')
    for key in ('max_output_tokens', 'timeout_seconds'):
        if not isinstance(settings[key], int) or settings[key] <= 0:
            raise ValueError(key + ' must be a positive integer.')
    price = settings['hosting']['usd_per_hour']
    if not isinstance(price, (int, float)) or not 0 <= price < float('inf'):
        raise ValueError('hosting.usd_per_hour must be finite and non-negative.')
    if settings['temperature'] != 0:
        raise ValueError('Use temperature 0 for this controlled comparison.')
    if settings['hosting']['currency'] != 'USD':
        raise ValueError('Use USD for the supplied cost formulas and report.')
    return settings
