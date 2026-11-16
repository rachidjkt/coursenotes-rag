"""Launch the real Streamlit app with the original synthetic Meridian corpus."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent
os.environ['COURSENOTES_HOME'] = str(PROJECT/'.demo_runtime')
os.environ['COURSENOTES_DOCUMENTS_DIR'] = str(PROJECT/'.demo_runtime'/'documents')
os.environ['COURSENOTES_DEMO'] = '1'
os.environ['COURSENOTES_TOP_K'] = '3'


def prepare():
    from evaluation.build_synthetic import BASE, build
    from core import index_pdfs
    if not (BASE/'meridian.pdf').is_file():
        build()
    directory = PROJECT/'.demo_runtime'/'documents'
    directory.mkdir(parents=True, exist_ok=True)
    if any(path.name != 'meridian.pdf' for path in directory.glob('*.pdf')):
        raise ValueError('Demo runtime contains other PDFs; use a clean synthetic-only demo directory.')
    shutil.copy2(BASE/'meridian.pdf', directory/'meridian.pdf')
    print(index_pdfs(), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--port', type=int, default=8501)
    args = parser.parse_args()
    prepare()
    if not args.prepare_only:
        from core import discover
        # Resolve the same local endpoint once before entering Streamlit's runner.
        os.environ['LM_STUDIO_URL'] = discover()
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', str(PROJECT/'app.py'),
                        '--server.address', '127.0.0.1', '--server.port', str(args.port),
                        '--server.headless', 'true', '--server.fileWatcherType', 'none'], check=True, cwd=PROJECT)
