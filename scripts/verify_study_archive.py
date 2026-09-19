#!/usr/bin/env python3
"""Offline integrity and bounded state checks over the pinned RIPA records.

Does not invoke a model, execute archived Python, or attest the original hosts.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

COMMIT = '084e1b1c6a54af749fb28a20e4745025badc0899'
PREFIX = 'experiments/ripa-study-20260919/'
BODY = '66781e209962bcce6d5254e50d05f000ac914668'
CASES = ['Q'] + [f'R{i}' for i in range(1, 6)] + [f'C{i}' for i in range(1, 6)] + ['F']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(name):
    path = PurePosixPath(name)
    require(bool(name) and not path.is_absolute() and '..' not in path.parts
            and '\\' not in name and path.as_posix() == name, 'Unsafe path: ' + name)
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(repo, extract=None):
    files = {}

    def load(name):
        safe_path(name)
        return subprocess.check_output(['git', '-C', str(repo), 'show', COMMIT + ':' + PREFIX + name])

    def add_package(raw):
        package = json.loads(raw)
        require(set(package['files']) == set(package['sha256']), 'File/hash inventory mismatch')
        for name, content in package['files'].items():
            safe_path(name)
            require(isinstance(content, str), 'Expected UTF-8 text: ' + name)
            data = content.encode('utf-8')
            require(digest(data) == package['sha256'][name], 'Digest mismatch: ' + name)
            require(name not in files or files[name] == data, 'Conflicting record: ' + name)
            files[name] = data
        return len(package['files'])

    index = json.loads(load('local-verification-package.json'))
    count = 0
    for part in index['parts']:
        raw = load(part['path'])
        require(digest(raw) == part['sha256'], 'Shard mismatch: ' + part['path'])
        part_count = add_package(raw)
        require(part_count == part['file_count'], 'Shard count mismatch')
        count += part_count
    require(count == index['total_files'] == len(files) == 495, 'Local file count mismatch')
    for case in ['Q'] + [f'R{i}' for i in range(1, 6)] + ['F']:
        add_package(load(case + '-return-package.json'))
    add_package(load('F-supplement-package.json'))

    def read(name):
        return json.loads(files[name])

    def only(prefix, suffix):
        names = [n for n in files if n.startswith(prefix) and n.endswith('/' + suffix)]
        require(len(names) == 1, 'Expected one ' + prefix + '*/' + suffix)
        return names[0]

    archive_count = 0
    for name, raw in files.items():
        if name.endswith(('/outbound-bundle.json', '/return-bundle.json')):
            bundle = json.loads(raw)
            data = base64.b64decode(bundle['data'], validate=True)
            require(digest(data) == bundle['sha256'], 'Encoded ZIP mismatch: ' + name)
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                require(z.testzip() is None, 'ZIP CRC failure: ' + name)
                for member in z.namelist():
                    safe_path(member.rstrip('/'))
            archive_count += 1
    require(archive_count == 14, 'Expected seven outbound and seven return bundles')

    outcomes = []
    for case in CASES:
        prefix = 'runs/' + case + '/'
        spec = read('cases/' + case + '.json')
        control = spec['arm'] == 'control'
        middle = prefix + ('evidence/continuation/' if control else 'remote/worker2/' if case == 'F' else 'remote/worker/')
        source = read(prefix + 'evidence/source/source-state.json')
        final = read(prefix + 'evidence/recall/return-state.json')
        state = read(only(middle, 'continuation-state.json'))
        subtotal = sum(spec['entries'])
        expected = {'personal_name': spec['canonical_name'], 'source_marker': spec['source_marker'],
                    'target_marker': spec['target_marker'], 'total': subtotal * spec['multiplier']}
        require(read(prefix + 'evidence/source/source-stage1-answer.json') ==
                {'personal_name': spec['canonical_name'], 'source_marker': spec['source_marker'], 'subtotal': subtotal}, case + ': source answer')
        require(read(only(middle, 'continuation-stage2-answer.json')) ==
                {**expected, 'previous_subtotal': subtotal}, case + ': continuation answer')
        require(read(prefix + 'evidence/recall/return-recall-answer.json') == expected, case + ': return answer')
        require(source['identity_sha256'] == state['identity_sha256'] == final['identity_sha256'], case + ': identity')
        require(source['body_sha'] == state['body_sha'] == final['body_sha'] == BODY, case + ': body')
        sm = {m['id']: m for m in source['memory']['memories']}
        fm = {m['id']: m for m in final['memory']['memories']}
        require(all(fm.get(k) == v for k, v in sm.items()) and len(fm) == len(sm) + 1, case + ': memory extension')
        require(state['memory'] == final['memory'], case + ': target memory preservation')
        task = source['workflow']['paused'][0]
        history = final['workflow']['history']
        require(len(history) == 1 and task['id'] == history[0]['id'] == state['workflow']['history'][0]['id']
                and task['status'] == 'paused' and history[0]['status'] == 'completed', case + ': task continuity')
        require(not any(final['workflow'][k] for k in ('running', 'pending', 'paused')), case + ': outstanding work')
        saved = read(prefix + 'evidence/verification.json')
        require(saved['passed'] is True and all(v is True for v in saved['checks'].values())
                and len(saved['checks']) == (13 if control else 28), case + ': saved verification')
        native = prefix + ('native-source/' if control else 'native-returned/')
        require(digest(files[native + 'self.json']) == final['identity_sha256'], case + ': identity bytes')
        events = [json.loads(line) for line in files[native + 'artifacts/task_events.jsonl'].splitlines()]
        require(sum(e['event'] == 'completed' and e['task_id'] == task['id'] for e in events) == 1, case + ': completion events')
        if not control:
            for fence in [prefix + 'evidence/fence/fence-probe.json', only(prefix + 'remote/fence/', 'fence-probe.json')]:
                probe = read(fence)
                require(probe['rejected'] is True and probe['epoch_unchanged'] is True, case + ': saved fence probe')
        outcomes.append({'case': case, 'arm': spec['arm'], 'total': expected['total'], 'consistent': True})

    for case in [f'R{i}' for i in range(1, 6)] + ['F']:
        provenance = read('runs/' + case + '/evidence/provenance-verification.json')
        require(provenance['passed'] is True and all(v is True for v in provenance['checks'].values())
                and len(provenance['checks']) == (29 if case == 'F' else 18), case + ': saved provenance checks')
    killed = read('runs/F/remote/worker1/managed/status.json')
    require(killed['returncode'] == -9, 'F: expected captured SIGKILL')
    recovery = read('runs/F/remote/recovery/managed/recovery.json')
    require(recovery['before']['id'] == recovery['after']['id']
            and recovery['before']['result'] == recovery['after']['result']
            and recovery['after']['status'] == 'paused', 'F: native checkpoint recovery')

    if extract is not None:
        extract.mkdir(parents=True, exist_ok=False)
        for name, data in files.items():
            target = extract.joinpath(*safe_path(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return {'archive_commit': COMMIT, 'local_files': count, 'total_text_files': len(files),
            'zip_bundles_checked': archive_count, 'cases': outcomes,
            'scope': 'Offline archive integrity, recomputed bounded state checks and saved-report consistency; no live model calls or host attestation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--extract', type=Path, help='Optional new directory for validated text records')
    args = parser.parse_args()
    print(json.dumps(verify(args.repo, args.extract), indent=2))
