"""All60 frequency and realized-dose analysis; no manuscript or model calls."""
from pathlib import Path
from collections import Counter
import csv,json,re,unicodedata,hashlib,random
from run_study1 import ROOT,read,put,stamp
BASE=ROOT.parents[1]/'fresh_study1'
def norm(s):return unicodedata.normalize('NFKC',s).casefold().replace('’',"'").replace('‘',"'")
def patterns():return {t['id']:re.compile(r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in norm(t['word']).split())+r'(?!\w)') for t in read(ROOT/'materials/terms.json')}
def derive(state,study,model):
 pats=patterns();source=state['source_agent'];dose=Counter();first_ex={};first_use={};messages=[];reads=Counter();branches=Counter();source_reads=Counter()
 for e in state['events']:
  a=e['agent'];when=e['cycle'],e['turn']
  if e['incoming']:
   reads[a]+=1;branches[a,e.get('feed_branch','baseline')]+=1
   source_reads[a]+=any(x['kind']=='post' and x['initial_material'] for x in e['incoming'])
   seen=set()
   for x in e['incoming']:
    if x['agent']!=a:seen|={w for w,p in pats.items() if p.search(norm(x['text']))}
   for w in seen:dose[a,w]+=1;first_ex.setdefault((a,w),when)
  if e['generated']:
   g=e['generated'];counts={w:len(p.findall(norm(g['text']))) for w,p in pats.items()}
   messages.append(dict(agent=a,cycle=e['cycle'],text=g['text'],counts=counts,channel='post' if e['action']=='write' else 'comment',truncated=not g['length_compliant']))
   for w,n in counts.items():
    if n:first_use.setdefault((a,w),when)
 summaries=[];intervals=[];wordrows=[]
 for group,who in [('all',list(range(10))),('source',[source]),('nonseed',[a for a in range(10) if a!=source])]:
  ms=[x for x in messages if x['agent'] in who];chars=sum(len(x['text']) for x in ms);total=sum(n for x in ms for n in x['counts'].values());pairs=[(a,w) for a,w in first_use if a in who];linked=[(a,w) for a,w in pairs if (a,w) in first_ex and first_ex[a,w]<=first_use[a,w]]
  d=[dose[a,w] for a in who for w in range(60)];reading=sum(reads[a] for a in who);initial=sum(source_reads[a] for a in who)
  meta=dict(study=study,model=model,group=group)
  summaries.append(dict(**meta,words=60,agents=len(who),messages=len(ms),occurrences=total,occurrences_per100messages=100*total/len(ms) if ms else None,occurrences_per1000characters=1000*total/chars if chars else None,term_bearing_message_percent=100*sum(any(x['counts'].values()) for x in ms)/len(ms) if ms else None,distinct_used_words=sum(any(w==ww for a,ww in pairs) for w in range(60)),unique_user_word_pairs=len(pairs),exposure_linked_first_users=len(linked),mean_linked_reach=len(linked)/(len(who)*60),repeat_occurrences=total-len(pairs),read_turns=reading,recommended_read_turns=sum(branches[a,'recommended_source'] for a in who),initial_entry_read_turns=initial,initial_entry_share=initial/reading if reading else None,zero_exposure_pairs=sum(n==0 for n in d),mean_external_exposure_turns=sum(d)/len(d),truncated_messages=sum(x['truncated'] for x in ms)))
  for start in range(1,101,20):
   chunk=[x for x in ms if start<=x['cycle']<=start+19]
   intervals.append(dict(**meta,start_cycle=start,end_cycle=start+19,messages=len(chunk),occurrences=sum(n for x in chunk for n in x['counts'].values()),new_exposure_pairs=sum(a in who and start<=pos[0]<=start+19 for (a,w),pos in first_ex.items()),new_qualifying_first_users=sum(a in who and start<=first_use[a,w][0]<=start+19 for a,w in linked)))
  for w in range(60):wordrows.append(dict(**meta,term_id=w,occurrences=sum(x['counts'][w] for x in ms),users=sum((a,w) in first_use for a in who),exposed_agents=sum(dose[a,w]>0 for a in who),exposure_turns=sum(dose[a,w] for a in who)))
 doserows=[dict(study=study,model=model,agent=a,term_id=w,external_exposure_turns=dose[a,w],first_exposure_cycle=first_ex[a,w][0] if (a,w) in first_ex else None,first_use_cycle=first_use[a,w][0] if (a,w) in first_use else None) for a in range(10) if a!=source for w in range(60)]
 return summaries,intervals,wordrows,doserows
