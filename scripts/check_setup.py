"""Read-only setup check. No installation, downloads, API calls or server start."""
import importlib.util
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import load_settings

settings = load_settings()
print('Endpoint:', settings['endpoint_url'])
print('Model:', settings['model'])
print('Local authentication:', 'configured' if os.getenv(settings['local_api_key_env']) else 'not required/configured')
for name in ('mlflow', 'pandas', 'matplotlib', 'reportlab', 'nbformat', 'nbconvert', 'ipykernel'):
    print(f'{name}:', 'available' if importlib.util.find_spec(name) else 'not installed')
for name in ('LLAMA_SERVER_PATH', 'LOCAL_MODEL_PATH'):
    value = os.getenv(name)
    print(name + ':', 'file exists' if value and Path(value).is_file() else 'not supplied (only needed for launcher)')
for name in ('model_revision', 'runtime_version'):
    if settings[name].startswith('SET_'):
        print('Before your final run, update:', name)
print('No packages or model files were downloaded.')
