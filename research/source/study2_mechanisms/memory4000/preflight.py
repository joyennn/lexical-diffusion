"""Read-only native-tokenizer stress check; no model generation or outcome data."""
from pathlib import Path
import json,os
from transformers import AutoTokenizer
ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def main():
 plan=read(ROOT/'protocol.json');terms=read(ROOT/'materials/terms.json');people=read(ROOT/'materials/personas.json');models=read(ROOT/'models.json');store=Path(os.environ.get('MODEL_STORE',ROOT.parents[1]/'local_gpu_check/models'))
 glossary='\n'.join(x['word']+': '+x['meaning'] for x in terms)
 entries=[x['word']+'\n'+(x['example']+'\n' if isinstance(x['example'],str) else '')+x['meaning']+('\n'+x['origin_usage'] if isinstance(x.get('origin_usage'),str) else '') for x in terms]
 longest=max(entries,key=len);corpus='\n'.join(entries);budget=4000+len(longest)+400;memory=(corpus*((budget//len(corpus))+1))[:budget]
 person=max(people,key=len);content='You are one social-network user. Follow the task and remain consistent with your persona.\nPersona:\n'+person+'\nPrivate initial source knowledge (available only to you):\n'+glossary+'\nYour current memory:\n'+memory+'\nYour activity counts: {"write":100,"read":100,"comment":100}\nTask:\nSummarize the important information in your current memory in at most 500 characters. Return only the summary.'
 checks=[]
 for model,info in models.items():
  tok=AutoTokenizer.from_pretrained(str(store/info['folder']),local_files_only=True)
  text=tok.apply_chat_template([dict(role='user',content=content)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  count=len(tok.encode(text,add_special_tokens=False));assert count<=7680,(model,count)
  checks.append(dict(model=model,conservative_context_chars=len(content),prompt_tokens=count,common_token_ceiling=7680,passed=True))
 result=dict(kind='Synthetic context stress test only; no inference, no pilot/main observations.',memory_chars_tested=len(memory),includes_longest_persona_and_private_source_glossary=True,checks=checks)
 (ROOT/'preflight_context.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
