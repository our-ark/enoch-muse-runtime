"""Read-only local artifact integrity checks, not independent protocol validation."""
from pathlib import Path, PurePosixPath
from collections import Counter
from hashlib import sha256
from zipfile import ZipFile
from io import BytesIO
import csv
import json

ROOT = Path(__file__).resolve().parent


def read_path(name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe manifest path: ' + name)
    path = (ROOT / Path(*rel.parts)).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Path escapes artifact: ' + name)
    return path


def check(condition, description):
    if not condition:
        raise ValueError(description)


def main():
    manifest = json.loads((ROOT / 'bundle-manifest.json').read_text())
    names = []
    for entry in manifest['files']:
        name = entry['path']
        data = read_path(name).read_bytes()
        check(len(data) == entry['bytes'], 'Size mismatch: ' + name)
        check(sha256(data).hexdigest() == entry['sha256'], 'Hash mismatch: ' + name)
        names.append(name)
    check(len(names) == len(set(names)), 'Duplicate manifest paths')
    ledger = json.loads((ROOT / 'protocol-case-ledger.json').read_text())
    anchors = pointers = 0
    for case in ledger['cases']:
        for entry in case['evidence']:
            data = read_path(entry['path']).read_bytes()
            check(sha256(data).hexdigest() == entry['sha256'], 'Ledger source mismatch')
            if 'anchor' in entry:
                check(entry['anchor'] in data.decode().splitlines()[entry['line'] - 1], 'Missing literal anchor')
                anchors += 1
            if 'json_pointer' in entry:
                obj = json.loads(data)
                for part in entry['json_pointer'].split('/')[1:]:
                    key = part.replace('~1', '/').replace('~0', '~')
                    obj = obj[int(key)] if isinstance(obj, list) else obj[key]
                pointers += 1
    redaction_path = ROOT / 'redaction-manifest.json'
    redacted_files = 0
    if redaction_path.exists():
        redactions = json.loads(redaction_path.read_text())
        original_hashes = set()
        for entry in redactions['files']:
            data = read_path(entry['path']).read_bytes()
            check(sha256(data).hexdigest() == entry['public_sha256'], 'Public-copy hash mismatch')
            check(len(data) == entry['public_bytes'], 'Public-copy size mismatch')
            original_hashes.add(entry['original_sha256'])
            obj = json.loads(data)
            for change in entry['changes']:
                value = obj
                for part in change['json_pointer'].split('/')[1:]:
                    key = part.replace('~1', '/').replace('~0', '~')
                    value = value[int(key)] if isinstance(value, list) else value[key]
                if change['kind'] == 'host_path_prefix':
                    check(value.startswith('<HOST_ROOT>'), 'Missing public path marker')
                elif change['kind'] == 'operator_preference':
                    check(change['replacement_text'] in value, 'Missing preference redaction marker')
                else:
                    raise ValueError('Unknown redaction category')
            redacted_files += 1
        check(redacted_files == 3, 'Unexpected redacted-file count')
        check(all(sha256(read_path(n).read_bytes()).hexdigest() not in original_hashes for n in names),
              'Private original included in public artifact')
        # Selected surviving links remain inspectable after path/preference redaction.
        base = ROOT / 'sources/host-exports-2026-10-04'
        bj = json.loads((base / 'item1-baijingjing.json').read_text())
        for key in ['a508f481', 'c50ab6b7']:
            req = bj[key]['runtime_request']['object']
            reply = bj[key]['runtime_reply_as_surviving']['object']
            check(req['request_id'] == reply['request_id'] and req['attempt'] == reply['attempt'],
                  'Runtime request/reply link mismatch')
            check(bj[key]['chat_request_received']['object']['text'] in req['message'], 'Missing chat request in runtime input')
        stage = json.loads((base / 'item2-s2-s4.json').read_text())
        sample = stage['s2_confirmation_ask_full_text_sample']['object']['text']
        check(sha256(sample.encode()).hexdigest() == stage['s2_text_sha256'], 'S2 sample hash mismatch')
        peach = json.loads((base / 'item3-peach.json').read_text())
        req = peach['tang_runtime_request']['object']; reply = peach['tang_runtime_reply']['object']
        check(req['request_id'] == reply['request_id'] and req['attempt'] == reply['attempt'], 'Peach request/reply mismatch')
        check(peach['tang_chat_inbox_133']['object']['text'] in req['message'], 'Peach seed missing from runtime input')
        turns = peach['private_json_session_d77f040177f7_entries']
        check(len(turns) == 2, 'Unexpected selected transcript length')
        check(reply['text'] == peach['tang_chat_reply_staged']['object']['text'] == turns[1]['text'], 'Delivered-text mismatch')
        check(reply['text'] in peach['baijingjing_received_tang_reply_as']['object']['text'], 'Reciprocal inbox mismatch')
    rows = list(csv.DictReader((ROOT / 'followup-coding.csv').open()))
    check([r['episode_id'] for r in rows] == [f'F{i:02}' for i in range(2, 22)], 'Unexpected episode IDs')
    summary = json.loads((ROOT / 'followup-coding-summary.json').read_text())
    fields = ['contingent_peer_response', 'prospective_pledge_or_norm', 'multi_turn_peer_exchange',
              'matched_earlier_seed', 'fresh_autonomous_initiation']
    for row in rows:
        data = read_path(row['source_path']).read_bytes()
        check(sha256(data).hexdigest() == row['source_sha256'], 'Coding source mismatch')
        for kind in ['pledge', 'response']:
            anchor = row[kind + '_anchor']
            if anchor:
                for line in row[kind + '_lines'].split(';'):
                    check(anchor in data.decode().splitlines()[int(line) - 1], 'Coding anchor mismatch')
    for surface in ['group', 'peer-private', 'host-private']:
        subset = [r for r in rows if r['surface'] == surface]
        actual = {'episodes': len(subset), **{f: dict(Counter(r[f] for r in subset)) for f in fields}}
        check(actual == summary['counts'][surface], 'Saved count mismatch: ' + surface)
    pilot = ROOT / 'protocol-pilot-8-episodes-2026-10-16.zip'
    with ZipFile(pilot) as z:
        check(z.testzip() is None, 'Pilot ZIP integrity failure')
        pm = json.loads(z.read('manifest.json'))
        check(pm['status'] == 'not_run' and pm['completed_judgments'] == 0, 'Unexpected pilot status')
        for entry in pm['files']:
            check(sha256(z.read(entry['path'])).hexdigest() == entry['sha256'], 'Pilot manifest mismatch')
        forms = [n for n in z.namelist() if '/forms/' in n and n.endswith('.json')]
        blank = 0
        for name in forms:
            values = json.loads(z.read(name))
            check(all(r['judgment'] == '' for r in values), 'Pilot contains judgments')
            blank += len(values)
        check(blank == 160, 'Unexpected blank form size')
        for stage in ['T', 'P']:
            with ZipFile(BytesIO(z.read('stage-' + stage + '.zip'))) as stage_zip:
                check(stage_zip.testzip() is None, 'Stage ZIP integrity failure')
                for name in stage_zip.namelist():
                    check(stage_zip.read(name) == z.read('stage-' + stage + '/' + name), 'Stage package mismatch')
    print(json.dumps({'status': 'integrity_checks_passed', 'manifest_files': len(names),
                      'ledger_anchors': anchors, 'ledger_json_pointers': pointers, 'coded_episodes': len(rows),
                      'public_redacted_exports': redacted_files,
                      'pilot_blank_judgments': blank, 'independent_protocol_validation': False}, indent=2))


if __name__ == '__main__':
    main()
