"""Package an explicit allowlist; exclude credentials, model weights and software."""
import argparse
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import ROOT
from verify_submission import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-incomplete', action='store_true', help='Create clearly labeled starter ZIP')
    args = parser.parse_args()
    status = verify()
    if not status['ready_for_submission'] and not args.allow_incomplete:
        raise SystemExit('Submission is incomplete. Run verify_submission.py and complete the pending evidence.')
    stem = 'mlops_submission' if status['ready_for_submission'] else 'mlops_starter'
    destination = ROOT.parent / (stem + '.zip')
    root_files = {'README.md','SUBMISSION_CHECKLIST.md','OFFLINE_VERIFICATION.md','requirements.txt','settings.json',
        'environment.example','run_assignment.py','eduassist_assignment.ipynb',
        'eduassist_assignment.html','latency_tokens_cost.csv','prompt_evaluation_results.csv',
        'submission_status.json','mlflow.db'}
    folders = {'eduassist','scripts','tests','data','prompts','reports','screenshots','evidence','mlartifacts'}
    extensions = {'.py','.md','.txt','.json','.csv','.ipynb','.html','.pdf','.png','.diff'}
    included = []
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(ROOT)
            if '__pycache__' in relative.parts or any(p.startswith('.') for p in relative.parts):
                continue
            allowed = (len(relative.parts) == 1 and relative.name in root_files) or (
                relative.parts[0] in folders and path.suffix in extensions)
            if not allowed:
                continue
            if status['ready_for_submission'] and '_DRAFT' in path.name:
                continue
            archive.write(path, Path('mlops') / relative)
            included.append(str(relative))
    print(destination)
    print(f'{len(included)} files. Readiness: {status["ready_for_submission"]}.')


if __name__ == '__main__':
    main()
