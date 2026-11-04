"""Run only after you have supplied the local model, server and dependencies."""
import argparse
import importlib.util
from eduassist.config import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=str, default=None, help='Alternative settings JSON path')
    args = parser.parse_args()
    missing = [name for name in ('mlflow', 'pandas', 'matplotlib', 'reportlab')
               if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit('Missing libraries: ' + ', '.join(missing)
                         + '. See README. Nothing will be installed automatically.')
    from eduassist.experiment import run_experiment
    from eduassist.reporting import write_report, create_charts
    rows, summaries, metadata = run_experiment(args.settings)
    create_charts(summaries)
    print('Report:', write_report(rows, summaries, metadata))
    print('Next: review responses, export the notebook, capture the MLflow UI, then verify_submission.py.')


if __name__ == '__main__':
    main()
