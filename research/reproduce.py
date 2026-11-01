"""Rebuild numerical results and independent audits from retained data. No model calls."""
from pathlib import Path
import argparse,csv,json,subprocess,sys
from tools.materialize import materialize
ROOT=Path(__file__).resolve().parent
STUDIES=['fresh_study1','study2_mechanisms/exposure50','study2_mechanisms/time200','study2_mechanisms/memory4000']
def run(work,study,*args):
    print('RUN',study,*args,flush=True)
    subprocess.run([sys.executable,*args],cwd=work/study,check=True,stdout=subprocess.DEVNULL)
def same_csv(a,b):
    def read(p):return list(csv.DictReader(p.open()))
    assert read(a)==read(b),str(a)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',required=True);a=p.parse_args()
    work=materialize(a.workspace)
    for study in STUDIES:
        run(work,study,'-m','unittest','discover','-p','test_*.py')
        run(work,study,'analyze.py')
        if study!='fresh_study1':run(work,study,'independent_review.py')
    run(work,'study3_semantics','validate.py');run(work,'study3_semantics','analyze.py');run(work,'study3_semantics','independent_review.py')
    checks=[]
    for study,files in {
        'fresh_study1':['analysis/model_summary.csv','analysis/term_metrics.csv','analysis/agent_term_first_events.csv','analysis/channel_metrics.csv'],
        'study2_mechanisms/exposure50':['analysis/summary.csv','analysis/final_review/verified_summary.csv'],
        'study2_mechanisms/time200':['analysis/window_metrics.csv','analysis/final_review/verified_window_metrics.csv'],
        'study2_mechanisms/memory4000':['analysis/summary.csv','analysis/final_review/verified_metrics.csv','analysis/final_review/verified_memory.csv'],
        'study3_semantics':['analysis/accuracy_summary.csv','analysis/paired_transitions.csv','analysis/stratified_accuracy.csv','analysis/sensitivity.csv']
    }.items():
        for rel in files:
            same_csv(work/study/rel,ROOT/'source'/study/rel);checks.append(study+'/'+rel)
    from tools.paper_tables import generate
    generate(work,work/'paper_results')
    report=dict(passed=True,no_model_calls=True,numeric_csvs_identical=checks,independent_audits_reexecuted=True,original_release_unmodified=True)
    (work/'reproduction_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
