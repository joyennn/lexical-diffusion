"""Prepare one Study 2 condition without running model inference.

Shares run-folder preparation with Study 1; continuation uses its baseline runner.
"""
from pathlib import Path
import runpy

def main():
 shared = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'study1/prepare.py'))
 shared['main'](conditions=['source_access', 'memory4000', 'continuation'], default_condition=None)

if __name__ == '__main__':
 main()
