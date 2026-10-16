"""Validate the supplied text anchors and summarize retrospective episode annotations.

This script aggregates analyst labels; it does not infer novelty or identity.
"""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re
ROOT=Path(__file__).resolve().parent

def main():
    rows=list(csv.DictReader((ROOT/'followup-coding.csv').open()))
    assert [r['episode_id'] for r in rows]==[f'F{i:02}' for i in range(2,22)]
    by_id={r['episode_id']:r for r in rows}
    bodies={}
    for row in rows:
        b=(ROOT/row['source_path']).read_bytes()
        assert hashlib.sha256(b).hexdigest()==row['source_sha256'],row['episode_id']
        bodies[row['episode_id']]=b.decode()
        for stem in ['pledge','response']:
            q=row[stem+'_anchor']
            if q:
                lines=row[stem+'_lines'].split(';')
                assert all(q in b.decode().splitlines()[int(n)-1] for n in lines),(row['episode_id'],stem)
        if row['prospective_pledge_or_norm']=='O':assert row['pledge_anchor']
    def seed(text):return re.search(r'^\*\*[^*]+→[^*]+：\*\* (.+)$',text,re.M)[1]
    for row in rows:
        if row['matched_earlier_seed']=='O':
            text=seed(bodies[row['episode_id']]);match=row['seed_match']
            if match in by_id:assert text==seed(bodies[match])
            else:
                earlier=ROOT/'sources/docs/agent-life-observations/dahua-xiyou/relationships/conversations/2026-10-03-baijingjing-tangsanzang-peach-reciprocity.zh-CN.md'
                assert text in earlier.read_text().splitlines()
    fields=['contingent_peer_response','prospective_pledge_or_norm','multi_turn_peer_exchange','matched_earlier_seed','fresh_autonomous_initiation']
    counts={}
    for surface in ['group','peer-private','host-private']:
        subset=[r for r in rows if r['surface']==surface]
        counts[surface]={'episodes':len(subset),**{key:dict(Counter(r[key] for r in subset)) for key in fields}}
    report={'version':'v0.16','prepared_on':'2026-10-13','annotation_status':'single retrospective Codex-produced pass; not independently validated','episodes':len(rows),'counts':counts,'checks':'20 source hashes, literal anchors and line locators, four repeated-seed matches','fulfillment_rate':'not estimated; no comparable opportunity denominator','thematic_novelty_rate':'not estimated; memos only'}
    (ROOT/'followup-coding-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
