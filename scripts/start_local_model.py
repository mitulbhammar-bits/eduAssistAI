"""Launch an EXISTING llama-server binary with an EXISTING model; never download."""
import os
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import load_settings


def main():
    paths = {}
    for variable in ('LLAMA_SERVER_PATH', 'LOCAL_MODEL_PATH'):
        value = os.getenv(variable)
        if not value or not Path(value).is_file():
            raise SystemExit(f'Set {variable} to an existing file. Nothing will be downloaded.')
        paths[variable] = str(Path(value).resolve())
    if not os.access(paths['LLAMA_SERVER_PATH'], os.X_OK):
        raise SystemExit('LLAMA_SERVER_PATH must be executable.')
    settings = load_settings()
    parsed = urlsplit(settings['endpoint_url'])
    command = [paths['LLAMA_SERVER_PATH'], '--model', paths['LOCAL_MODEL_PATH'],
        '--alias', settings['model'], '--host', parsed.hostname, '--port', str(parsed.port or 80),
        '--ctx-size', '4096', '--parallel', '1', '--n-gpu-layers', '0']
    print('Starting supplied software only:', shlex.join(command), flush=True)
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
