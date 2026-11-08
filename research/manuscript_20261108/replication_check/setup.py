"""Prepare one additional, isolated replication. No inference and no old-file writes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,shutil

R=Path(__file__).resolve().parent
W=R.parent
NEW=R/'rep02'
SEED=2026110300  # Keep seed % 10 == 0 so source identity does not change.
MODELS=['llama','qwen','gemma','mistral']
PATHS={'baseline':'fresh_study1','exposure50':'study2_mechanisms/exposure50','memory4000':'study2_mechanisms/memory4000','time200':'study2_mechanisms/time200','semantics':'study3_semantics'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
def load(p):return json.loads(p.read_text())
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2));tmp.replace(p)

# Additional items are authored before any rep02 model responses or case selection.
# The 135 retained questions for the original 45 expressions remain unchanged.
ADDITIONS={
4:("Something flawless, ideal, or exceptionally attractive in appearance or character.","A beautifully arranged garden has every flowerbed and pathway looking ideal.","A family portrait looks flawless, with everyone perfectly posed and the lighting just right.","A photograph is so blurred that none of its subjects can be recognized.","Someone counts the number of frames hanging on an office wall.","A cook measures salt before adding it to a boiling pot."),
6:("A baby born after an earlier miscarriage, stillbirth, or infant death.","After losing an earlier pregnancy, a couple welcomes a healthy newborn.","Parents who experienced their infant's death later celebrate the birth of another child.","A child paints a multicolored arch during an art lesson.","A couple announces their first pregnancy without any previous pregnancy loss.","A photographer takes a picture of sunlight passing through a prism."),
7:("Cuddling side by side, with one person's back against the other's chest.","Two partners rest on their sides, with the front person's back nestled against the other's chest.","A couple falls asleep facing the same direction, their bodies curled together from behind.","Two friends hug while standing face to face at a station.","A chef arranges metal utensils beside a serving bowl.","Two people sit on opposite sides of a table to play chess."),
9:("An informal expression of agreement, approval, or excitement.","A friend enthusiastically endorses a proposed plan with a brief approving reply.","Someone hears an opinion they strongly agree with and responds with enthusiastic approval.","A student asks a teacher to define an unfamiliar technical term.","A worker raises a printed sign above a doorway.","A visitor quietly objects to an idea and requests its rejection."),
13:("Someone who pretends to be concerned while deliberately undermining a group or cause.","A campaign opponent joins its forum and feigns helpful worry to sow distrust among supporters.","Someone disguises attacks on a movement as anxious advice intended to weaken members' confidence.","A genuine supporter reports a verified safety problem and helps the group solve it.","A fantasy creature guards a stone bridge in a children's story.","An accountant adds receipts to calculate a monthly total."),
17:("Posting emotional problems online to obtain attention or personal advantage.","Someone shares a dramatic account of personal troubles online mainly to attract sympathetic attention.","An influencer strategically posts distressing personal complaints to gain engagement and favors.","A person privately tells a therapist about a painful experience to seek treatment.","An angler feels disappointed after catching no fish at a lake.","An archivist labels photographs by the year they were taken."),
18:("Covertly limiting a user's content visibility without informing that user.","A platform quietly hides an account's posts from other users while its owner believes they remain visible.","Moderators secretly stop a user's comments appearing publicly without sending any notification.","A moderator openly notifies someone that their account has been permanently suspended.","An artist shades part of a drawing with a charcoal pencil.","A user voluntarily deletes an old photograph from their own profile."),
19:("Subtly expressing disrespect or ridicule through words or nonverbal behavior.","At an awards event, a performer makes a veiled mocking remark about a rival's talent.","Someone gives a dismissive look and a sly backhanded compliment to ridicule a colleague.","A gardener installs a canopy to protect seedlings from direct sunlight.","A visitor gives a sincere, straightforward compliment on a friend's achievement.","A student calculates the distance between two cities on a map."),
20:("Endearing or attractive partly because of awkwardness or unusual interests.","A shy science enthusiast's clumsy excitement makes their date find them especially charming.","Friends affectionately admire someone's awkward but lovable enthusiasm for obscure board games.","A confident host is admired solely for polished professional manners.","A worker enters a door code to unlock an empty warehouse.","A reviewer criticizes a speaker's behavior as unpleasant and unlikeable."),
28:("Smiling expressively with the eyes, often in a playful or flirtatious way.","A model keeps their mouth still while giving the camera a playful smiling expression through their eyes.","During a portrait session, a photographer asks for warmth and flirtation conveyed by the eyes alone.","A driver closes both eyes because bright sunlight is uncomfortable.","A chef tastes a spoonful of soup before serving dinner.","A tired passenger yawns while waiting for the train."),
30:("Coordinated online group action, especially to manipulate voting or harass others.","An online group organizes its members to flood a rival forum with hostile replies.","People coordinate mass votes in an internet poll to distort its outcome.","A single reader independently posts a polite disagreement on a discussion page.","Firefighters assemble vehicles before a scheduled rescue exercise.","A librarian sorts returned books into alphabetical order."),
39:("A white person condescendingly explaining race or injustice issues to people of color.","A white colleague patronizingly lectures a Black coworker about how racism affects Black people.","A white visitor dismisses Indigenous participants' concerns and condescendingly explains which injustices should matter to them.","A person of color explains their own experience while a white colleague listens respectfully.","A decorator explains how to mix pale paint for a bedroom wall.","A mechanic describes an engine repair to another mechanic."),
47:("An expression conveying love, affection, and good wishes.","A grandmother closes a message to her grandchildren by sending affectionate love and warm wishes.","Someone ends a note to their partner with a loving expression of affection and well wishes.","A manager closes a disciplinary notice with a formal demand for compliance.","A researcher counts two categories of gestures without expressing affection.","A shopper compares the prices printed on three packages."),
55:("An insulting label for someone perceived as excessively sensitive, often in political arguments.","During a political dispute, a speaker mocks an opponent as too easily offended by criticism.","Someone dismissively labels young political activists as fragile and unable to tolerate disagreement.","A scientist examines the symmetrical structure of an ice crystal.","A campaigner respectfully praises an opponent's calm response to harsh criticism.","A baker measures flour for a large batch of bread."),
58:("An excessive display of designer fashion, or the overconfidence associated with it.","Someone wears many conspicuous designer accessories at once and boasts about their extravagant style.","A partygoer piles on luxury labels and struts around with confidence fueled by the outfit.","A diner pours so much dressing onto a meal that the plate overflows.","A person wears plain practical clothing and avoids drawing attention to themselves.","A student checks whether the library will open on a holiday.")
}

def main():
 assert not (R/'freeze.json').exists(),'Already prepared; use controller.py to resume.'
 assert SEED!=load(W/'fresh_study1/protocol.json')['main_seed'] and SEED%10==0
 originals={}
 for name,rel in PATHS.items():
  src=W/rel;dest=NEW/rel;dest.mkdir(parents=True,exist_ok=True)
  for f in src.glob('*.py'):shutil.copy2(f,dest/f.name)
  for n in ['models.json','protocol.json']:shutil.copy2(src/n,dest/n)
  shutil.copytree(src/'materials',dest/'materials',dirs_exist_ok=True)
  # No prior checkpoints, calls, completion markers, or analysis outcomes are copied.
  plan=load(dest/'protocol.json');plan.update(main_seed=SEED,pilot_seed=2026110390,main_trajectories_per_model=1,replication_id='rep02',main_scope='One additional independent seed per fixed model and condition; combine with original exploratory trajectory only for two-run descriptive comparison.',artifacts='Raw data, audit and two-run statistical description only. No automatic manuscript edits or publication.')
  put(dest/'protocol.json',plan)
  for m in MODELS:
   folder=src/'runs/main'/m
   for n in ['checkpoint.json','calls.jsonl']:
    if (folder/n).exists():originals[str((folder/n).relative_to(W))]=sha(folder/n)
  for f in src.glob('*.py'):originals[str(f.relative_to(W))]=sha(f)
  originals[str((src/'protocol.json').relative_to(W))]=sha(src/'protocol.json')
  for f in (src/'materials').glob('*'):
   if f.is_file():originals[str(f.relative_to(W))]=sha(f)
 (NEW/'local_gpu_check').mkdir(exist_ok=True)
 (NEW/'local_gpu_check/models').symlink_to(W/'local_gpu_check/models',target_is_directory=True)
 bank=load(W/'study3_semantics/materials/item_bank.json');terms=load(W/'fresh_study1/materials/terms.json')
 assert len(bank)==135
 existing=set(q['term_id'] for q in bank);assert set(ADDITIONS)==set(range(60))-existing
 correct_def={w:v[0] for w,v in ADDITIONS.items()}
 candidates=[6,18,44,35,29,7,30]
 unrelated={6:"A baby born following a miscarriage, stillbirth, or an infant's death.",18:"A moderation policy hiding a user's content without notifying that user.",44:"A defensive interception returned for a touchdown in American football.",35:"Facial acne or irritation caused by wearing a protective face mask.",29:"Someone who prefers remaining single rather than dating merely to avoid solitude.",7:"A cuddling position with two people on their sides facing the same direction.",30:"Coordinated online group action intended to manipulate votes or harass someone."}
 for w,(meaning,c1,c2,d1,d2,d3) in sorted(ADDITIONS.items()):
  bank.append(dict(id=f'w{w}_meaning',term_id=w,kind='meaning',question=f'Which explanation best matches the intended slang meaning of "{terms[w]["word"]}"?',correct=meaning,distractors=[unrelated[j] for j in candidates if j!=w][:3]))
  for n,correct in enumerate([c1,c2],1):bank.append(dict(id=f'w{w}_context{n}',term_id=w,kind='application',question=f'Which scenario best illustrates the intended slang meaning of "{terms[w]["word"]}"? Select the semantic use rather than a literal homonym.',correct=correct,distractors=[d1,d2,d3]))
 assert len(bank)==180 and len({q['id'] for q in bank})==180
 for q in bank:
  assert len(set([q['correct']]+q['distractors']))==4
  if q['kind']=='meaning':assert all(5<=len(d.split())<=25 for d in q['distractors'])
  else:assert q['correct']!=terms[q['term_id']]['example']
 for q in load(W/'study3_semantics/materials/item_bank.json'):assert q==next(x for x in bank if x['id']==q['id'])
 sem=NEW/PATHS['semantics']
 # Case/job files from rep01 are not valid inputs for the new trajectory.
 for n in ['cases.json','jobs.json']:(sem/'materials'/n).unlink(missing_ok=True)
 put(sem/'materials/item_bank.json',bank)
 put(R/'original_manifest.json',originals)
 put(R/'protocol.json',dict(created_at=now(),original_seed=2026103000,additional_seed=SEED,models=MODELS,additional_runs_per_model_condition=1,total_runs_per_model_condition_after_completion=2,sequence=['baseline fresh100','exposure50 fresh100','memory4000 fresh100','continue copied rep02 baseline101–200','semantic probes from all rep02 exposure50 first-use cases','raw independent audit and two-run comparison'],source_identity=0,materials='Same sixty expressions and ten persona strings; hashes must match rep01.',inference_rules='Frozen inference runners copied byte-identically. Only main seed changes. Source-agent assignment held at zero. No outcome gate.',technical_preflight='Existing synthetic control-flow tests, runner/input hashes and environment check; no additional LLM pilot needed for already validated unchanged inference code.',stopping='Exactly one additional trajectory per model and fresh condition; stop at100/200 regardless of outcome. Do not expand to5/10/20 repeats.',analysis=dict(primary='All60 literal occurrences per100 non-source messages; per1000characters sensitivity.',secondary=['target-bearing messages','expression coverage','agent-expression coverage','exposure and recommendation realization','source vs non-source','20cycle trajectories','memory timing and concentration','semantic word-macro and case-weighted accuracy, paired transitions and definition availability'],summary='Display rep01 and rep02 separately, within-seed condition contrasts, equal-weight two-run mean, sample SD and min/max where defined, direction concordance. No treating words/messages as independent trajectories. No n=2 bootstrap CI, GLMM, t-test or confirmatory p-values. No population-level robustness claim.',time='Compare1–100 with101–200 within each baseline trajectory; do not count phases as independent replications.',semantics='All first non-source agent-word uses in each exposure run, including pre-exposure events. Cases and word sets can differ. Equal-run summary and common-word sensitivity; no automatic causal learning or production-correctness claim.'),semantic_item_amendment=dict(reason='Rep02 may produce first uses for expressions unused in rep01. Avoid dropping these cases after observing outcomes.',original_questions_unchanged=135,additional_questions=45,total_questions=180,authorship='AI-assisted source-based authoring, structural/source review; no independent human validation.',freeze='Full60 inventory completed before any rep02 inference. Fresh case selection never depends on semantic accuracy.'),budget_hours=96,no_manuscript_changes=True,no_automatic_github_publication=True))
 print('Prepared isolated rep02 inputs and all180 semantic items. No inference started.')
if __name__=='__main__':main()
