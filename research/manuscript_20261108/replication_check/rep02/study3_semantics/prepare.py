from pathlib import Path
from collections import Counter
import json,hashlib,random,re
R=Path(__file__).resolve().parent;P=R.parent;S=P/'study2_mechanisms/exposure50'
load=lambda p:json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def main():
 assert not (R/'freeze.json').exists()
 terms=load(S/'materials/terms.json');personas=load(S/'materials/personas.json');save(R/'models.json',load(S/'models.json'));save(R/'materials/terms.json',terms)
 authored={int(v[0]):v[1:] for v in (x.split('\t') for x in (R/'materials/item_content.tsv').read_text().splitlines())};bank=[];usedids=set();cases=[];sources={}
 for m in ['llama','qwen','gemma','mistral']:
  f=S/'runs/main'/m;s=load(f/'checkpoint.json');calls={x['key']:x for x in map(json.loads,(f/'calls.jsonl').read_text().splitlines())};seen=set()
  sources[m]={'checkpoint_sha256':hashlib.sha256((f/'checkpoint.json').read_bytes()).hexdigest(),'calls_sha256':hashlib.sha256((f/'calls.jsonl').read_bytes()).hexdigest()}
  for e in s['events']:
   if e['agent']==s['source_agent'] or not e['generated']:continue
   for w in e['generated']['term_ids']:
    key=e['agent'],w
    if key in seen:continue
    seen.add(key);usedids.add(w);g=e['generated'];raw=calls[g['task_key']];prefix=raw['request']['content'].split('\nTask:\n')[0]
    # Prefix is the exact effective pre-generation prompt, after any summary and incoming read.
    assert prefix.startswith('You are one social-network user.') and 'Private initial source knowledge' not in prefix
    incomingterm=any(re.search(r'(?<!\w)'+re.escape(terms[w]['word'].casefold())+r'(?!\w)',x['text'].casefold()) for x in e['incoming'])
    prior=any(x['agent']==e['agent'] and w in x['term_ids'] and (x['cycle'],x['turn'])<=(e['cycle'],e['agent']) for x in s['exposures'])
    initial='You are one social-network user. Follow the task and remain consistent with your persona.\nPersona:\n'+personas[e['agent']]+'\nYour current memory:\n\nYour activity counts: '+json.dumps(dict(write=0,read=0,comment=0))
    cases.append(dict(id=f"{m}_a{e['agent']}_w{w}",model=m,agent=e['agent'],term_id=w,word=terms[w]['word'],cycle=e['cycle'],action=e['action'],original_generation_key=g['task_key'],original_request_hash=raw['request_hash'],use_prefix=prefix,initial_prefix=initial,prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),earlier_or_same_turn_exposure=prior,current_incoming_contains_term=incomingterm,exact_source_definition_in_prefix=terms[w]['meaning'] in prefix))
 assert usedids==set(authored) and len(cases)==135
 for w in sorted(usedids):
  meaning,c1,c2,d1,d2,d3=authored[w]
  # Definition distractors are broad unrelated meanings from other source entries.
  candidates=[6,18,44,35,29,7,30];others=[x for x in candidates if x!=w][:3]
  unrelated={6:"A baby born following a miscarriage, stillbirth, or an infant's death.",18:"A moderation policy hiding a user's content without notifying that user.",44:"A defensive interception returned for a touchdown in American football.",35:"Facial acne or irritation caused by wearing a protective face mask.",29:"Someone who prefers remaining single rather than dating merely to avoid solitude.",7:"A cuddling position with two people on their sides facing the same direction.",30:"Coordinated online group action intended to manipulate votes or harass someone."}
  ddef=[unrelated[j] for j in others]
  bank.append(dict(id=f'w{w}_meaning',term_id=w,kind='meaning',question=f'Which explanation best matches the intended slang meaning of "{terms[w]["word"]}"?',correct=meaning,distractors=ddef))
  for n,c in enumerate([c1,c2],1):bank.append(dict(id=f'w{w}_context{n}',term_id=w,kind='application',question=f'Which scenario best illustrates the intended slang meaning of "{terms[w]["word"]}"? Select the semantic use rather than a literal homonym.',correct=c,distractors=[d1,d2,d3]))
 jobs=[];bankmap={x['id']:x for x in bank}
 for m in ['llama','qwen','gemma','mistral']:
  cc=[x for x in cases if x['model']==m];labels=[n%4 for n in range(len(cc)*3)];random.Random(20261101+['llama','qwen','gemma','mistral'].index(m)).shuffle(labels)
  for n,c in enumerate(cc):
   for k,qid in enumerate([f"w{c['term_id']}_meaning",f"w{c['term_id']}_context1",f"w{c['term_id']}_context2"]):
    q=bankmap[qid];correct=labels[n*3+k];ds=q['distractors'][:];random.Random(c['id']+qid).shuffle(ds);opts=ds[:];opts.insert(correct,q['correct']);task='Answer the following four-option semantic question. Return only the digit 0, 1, 2, or 3.\n'+q['question']+'\n'+'\n'.join(f'{i}: {v}' for i,v in enumerate(opts))+'\nReturn only the selected digit.'
    for state in ['initial','use']:
     jobs.append(dict(key=c['id']+'/'+qid+'/'+state,case_id=c['id'],model=m,term_id=c['term_id'],agent=c['agent'],kind=q['kind'],item_id=qid,state=state,correct=correct,options=opts,content=c[state+'_prefix']+'\nTask:\n'+task,sampling_seed=int(hashlib.sha256((c['id']+'/'+qid).encode()).hexdigest()[:8],16)))
 assert len(jobs)==810 and len(bank)==135
 for q in bank:
  assert len(set([q['correct']]+q['distractors']))==4
  t=terms[q['term_id']];assert all(x!=t['example'] for x in [q['correct']]+q['distractors'])
 save(R/'materials/item_bank.json',bank);save(R/'materials/cases.json',cases);save(R/'materials/jobs.json',jobs)
 protocol=dict(version='study3-semantics-1.0',time='2026-11-01',models=['llama','qwen','gemma','mistral'],source='completed Study2-1 exposure50, all first non-source agent-word uses',cases=135,case_counts=dict(Counter(c['model'] for c in cases)),tested_word_union=45,untested_words=15,definition_items_per_case=1,application_items_per_case=2,main_responses=810,states=['initial same persona empty memory zero activity','exact pre-generation prefix including summary and current incoming'],sampling=dict(temperature=.9,top_p=.9,max_tokens=1,allowed_digits=[0,1,2,3],paired_seed=True),pilot='one first case per model; 24 responses, separate keys and logs, no accuracy gate',analysis='separate task/model, term macro average primary, case micro secondary, paired transitions, no independent-observation p values; source access and no-exposure strata; leave-one-word/agent-out sensitivity',item_authorship='AI-assisted authoring and source-based computational review, no independent human content validation',inference_scope='semantic recognition in use-conditioned states; not actual message correctness, learning causality, or spontaneous production; shared persona/context/statistics vary',outcome_independent_selection=True,github='future sharing required, do not publish now',sources=sources)
 save(R/'protocol.json',protocol)
 print('Prepared',len(cases),'cases,',len(bank),'unique questions,',len(jobs),'main responses. Position counts',Counter(j['correct'] for j in jobs))
if __name__=='__main__':main()
