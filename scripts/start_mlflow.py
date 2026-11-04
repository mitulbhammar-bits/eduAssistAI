"""Show local experiment evidence after dependencies and measured data exist."""
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import ROOT, tracking_uri

if not (ROOT / 'mlflow.db').exists():
    raise SystemExit('No local MLflow database yet. Run the assignment after supplying your model.')
environment = dict(os.environ, MLFLOW_ENABLE_TELEMETRY='false')
environment['MLFLOW_TRACKING_URI'] = tracking_uri()
environment['MLFLOW_REGISTRY_URI'] = tracking_uri()
subprocess.run([sys.executable, '-m', 'mlflow', 'server', '--backend-store-uri', tracking_uri(),
                '--host', '127.0.0.1', '--port', '5000'], cwd=ROOT, env=environment, check=True)
