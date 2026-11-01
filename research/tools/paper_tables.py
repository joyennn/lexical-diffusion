"""Recreate the manuscript's circulation and recognition tables from audited CSVs."""
from pathlib import Path
import csv,json,argparse
MODELS=['llama','qwen','gemma','mistral']
def rows(p):return list(csv.DictReader(p.open()))
def save(p,data):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def generate(work,out):
    work=Path(work);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    mem=rows(work/'study2_mechanisms/memory4000/analysis/final_review/verified_metrics.csv')
    expo=rows(work/'study2_mechanisms/exposure50/analysis/final_review/verified_summary.csv')
    time=rows(work/'study2_mechanisms/time200/analysis/final_review/verified_window_metrics.csv')
    sem=rows(work/'study3_semantics/analysis/accuracy_summary.csv')
    rates=[];recognition=[]
    for m in MODELS:
        b=next(x for x in mem if x['model']==m and x['study']=='baseline' and x['group']=='nonseed')
        a=next(x for x in mem if x['model']==m and x['study']=='memory4000' and x['group']=='nonseed')
        e=next(x for x in expo if x['model']==m and x['study']=='exposure50' and x['group']=='nonseed');t=next(x for x in time if x['model']==m and x['group']=='nonseed' and x['start_cycle']=='101' and x['end_cycle']=='200')
        rates.append(dict(model=m,baseline_1_100_per100messages=float(b['occurrences_per100messages']),source_access_1_100_per100messages=float(e['occurrences_per100messages']),continuation_101_200_per100messages=float(t['occurrences_per100messages']),memory4000_1_100_per100messages=float(a['occurrences_per100messages'])))
        r={'model':m}
        for k in ['meaning','application']:
            for state in ['initial','use']:
                x=next(x for x in sem if x['model']==m and x['kind']==k and x['state']==state)
                r[k+'_'+state+'_word_macro_percent']=100*float(x['macro_word_accuracy'])
                r['cases']=int(x['cases']);r['words']=int(x['words'])
        recognition.append(r)
    save(out/'table1_circulation.csv',rates);save(out/'table2_recognition.csv',recognition)
    (out/'scope.json').write_text(json.dumps(dict(non_source_agents=9,expressions=60,simulation_trajectories_per_model_per_fresh_condition=1,continuation_is_same_baseline_trajectory=True,semantic_cases=135,semantic_retained_responses=810,semantic_tested_word_union=45,no_human_item_validation=True),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.workspace,a.output)
