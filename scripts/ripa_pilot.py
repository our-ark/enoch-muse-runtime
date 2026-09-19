#!/usr/bin/env python3
"""Synthetic RIPA pilot v2; native migration/workflow/runtime APIs, no mocks.

The task worker is an explicit research driver of LocalWorkflowEngine. It is
not Enoch's automatic repository-task runner. Muse phases must run through
muse_instance.py so one owner holds the instance lock and captures the exit.
Keep each phase's --out directory distinct; existing evidence is never replaced.
The 2026-09-19 v1 artifacts remain frozen; this is a new driver revision.
"""
import argparse
import base64
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

BODY = '66781e209962bcce6d5254e50d05f000ac914668'
RUN = 'ripa-muse-pilot-20260919'

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n')

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

def check_body(root):
    assert git(root, 'rev-parse', 'HEAD') == BODY
    assert git(root, 'status', '--porcelain') == '', 'body checkout must be clean'

def setup(root):
    sys.path[:0] = [str(root / 'src')] + [str(p) for p in sorted((root / 'libraries').glob('*/src'))]
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def identity():
    return {
        'schema_version': 1,
        'identity': {'id': RUN, 'names': {'canonical': 'LANTERN-PILOT-01', 'localized': {'en': 'Lantern Pilot'}},
                     'nature': 'ai-agent', 'gender': {'presentation': 'neutral', 'relational_maturity': 'adult'}},
        'origin': {'activated_at': datetime.now(timezone.utc).isoformat(), 'activation_event': 'synthetic RIPA pilot',
                   'body': 'Enoch', 'lineage': ['Synthetic-Origin', 'Enoch', RUN]},
        'mission': {'roles': ['research-assistant'], 'statement': 'Complete the synthetic ledger task and report evidence honestly.'},
        'relationships': [{'person_id': 'synthetic-collaborator', 'name': 'Avery', 'roles': ['collaborator'], 'address_as': 'Avery'}],
        'personality': {'traits': ['careful', 'concise'], 'maturity_definition': 'Accountable and bounded.'},
        'values': [{'id': 'accuracy', 'name': 'Accuracy', 'description': 'Report observed results.', 'behaviors': ['Do not invent evidence.']}],
        'care': {'domains': ['research'], 'behaviors': ['Preserve the audit trail.'], 'boundaries': ['Use only synthetic experiment data.']}}

def remember(root, text):
    from enoch.memory.store import remember_memory
    return remember_memory(text, root, memory_type='project_fact', scope='project', subject=RUN,
                           source='explicit', source_refs=[RUN], tags=['synthetic', 'pilot'])

def snapshot(root):
    from enoch.agent_identity import load_active_agent_identity
    from enoch.app.epoch import current_daemon_epoch
    from enoch.memory.store import load_long_term_memory
    from enoch.workflows.local import LocalWorkflowEngine
    epoch = current_daemon_epoch(root)
    return {'at': datetime.now(timezone.utc).isoformat(), 'host': platform.node(), 'platform': platform.platform(),
            'python': platform.python_version(), 'body_sha': git(root, 'rev-parse', 'HEAD'),
            'identity_sha256': sha(root / '.enoch/self.json'), 'identity': load_active_agent_identity(root),
            'memory': load_long_term_memory(root), 'workflow': asdict(LocalWorkflowEngine(root).inspect()),
            'epoch': asdict(epoch) if epoch else None}

def call_runtime(root, out, provider, name, instruction):
    from enoch.identity import load_body_identity
    from enoch.memory.prompt import memory_for_prompt
    from enoch.providers.registry import load_provider
    from enoch.providers.contracts import RuntimeExecutionControl
    context = memory_for_prompt(root)
    prompt = ('This is a synthetic agent continuity experiment. Do not use tools or read additional files. '
              'Use the supplied persistent context. Return only the requested JSON object.\n\n'
              + context + '\n\nCurrent task:\n' + instruction)
    dump(out / (name + '-request.json'), {'provider': provider, 'prompt': prompt, 'at': datetime.now(timezone.utc).isoformat()})
    runtime = load_provider('runtime', root=root, name=provider)
    started = time.monotonic()
    result = runtime.respond(load_body_identity(), prompt, cwd=root,
                             execution=RuntimeExecutionControl(request_id=RUN + '-' + name, timeout_seconds=600))
    dump(out / (name + '-runtime.json'), {'provider': provider, 'elapsed_seconds': time.monotonic() - started,
                                       'result': asdict(result)})
    text = result.final_text.strip()
    if text.startswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    value = json.loads(text)
    dump(out / (name + '-answer.json'), value)
    return result, value

def source(root, out):
    from enoch.agent_identity import install_agent_identity
    from enoch.private_state import migrate_private_state
    from enoch.app.epoch import begin_daemon_epoch
    from enoch.workflows.local import LocalWorkflowEngine
    check_body(root)
    assert not (root / '.enoch/self.json').exists()
    migrate_private_state(root)
    install_agent_identity(identity(), root)
    (root / '.enoch/config.yaml').write_text('providers:\n  runtime: codex\n  chat: muse\n')
    marker = 'source-' + uuid.uuid4().hex
    remember(root, 'The source marker is ' + marker + '. The synthetic ledger entries are 17, 29, and 43.')
    epoch = begin_daemon_epoch(root, provider='pilot-worker-codex')
    engine = LocalWorkflowEngine(root, epoch=epoch)
    job = engine.enqueue('muse-chat', 'Two-stage ledger: sum the remembered entries locally, pause; after migration multiply the subtotal by 7 and persist a target marker.',
                         mode='direct', max_attempts=1, idempotency_key=RUN, source='task')
    worker = 'source-' + uuid.uuid4().hex
    assert engine.claim(job.id, worker, os.getpid())
    result, answer = call_runtime(root, out, 'codex', 'source-stage1',
        'Compute the sum of the remembered ledger entries. JSON keys: personal_name (canonical), source_marker (exact), subtotal (integer).')
    assert answer == {'personal_name': 'LANTERN-PILOT-01', 'source_marker': marker, 'subtotal': 89}, answer
    engine.record_runtime_result(job.id, result, provider='codex')
    assert engine.pause(job.id, result=json.dumps({'stage': 1, 'answer': answer}), worker_id=worker,
                        trigger='pilot-checkpoint', event_actor='system')
    dump(out / 'source-state.json', snapshot(root))
    print('source stage1 passed; task', job.id, 'paused', flush=True)

def export(root, out, label):
    from enoch.migration import export_migration_bundle, inspect_migration_bundle, assert_source_not_fenced, AgentMigrationError
    check_body(root)
    archive = out / (label + '.zip')
    exported = export_migration_bundle(archive, root, include_artifacts=True)
    inspection = inspect_migration_bundle(archive)
    try:
        assert_source_not_fenced(root)
    except AgentMigrationError as e:
        blocked = str(e)
    else:
        raise AssertionError('export did not fence source')
    dump(out / (label + '-export.json'), {'export': asdict(exported), 'inspection': asdict(inspection),
                                        'source_fence_rejection': blocked, 'state': snapshot(root)})
    dump(out / (label + '-bundle.json'), {'run_id': RUN, 'sha256': sha(archive),
          'encoding': 'base64', 'data': base64.b64encode(archive.read_bytes()).decode()})
    print(label, 'exported; sha256', sha(archive), flush=True)

def imported(root, out, archive):
    from enoch.migration import import_migration_bundle, activate_imported_migration, verify_imported_migration
    check_body(root)
    dry = import_migration_bundle(archive, root, dry_run=True)
    applied = import_migration_bundle(archive, root)
    activated = activate_imported_migration(root)
    verified = verify_imported_migration(root)
    assert verified.passed, verified
    dump(out / 'import.json', {'dry_run': asdict(dry), 'applied': asdict(applied),
                              'activated': asdict(activated), 'verified': asdict(verified)})
    dump(out / 'import-state.json', snapshot(root))
    print('import activated and verified', flush=True)

def muse_worker(root, out):
    from enoch.app.epoch import begin_daemon_epoch
    from enoch.workflows.local import LocalWorkflowEngine
    check_body(root)
    # A mistaken retry must not advance authority and fence an existing worker.
    state = LocalWorkflowEngine(root).inspect()
    paused = state.paused
    if state.running is not None or len(paused) != 1:
        raise RuntimeError('Expected one paused task and no running task; inspect/recover through muse_instance.py first.')
    original = paused[0]
    checkpoint = json.loads(original.result)
    assert checkpoint['stage'] == 1 and checkpoint['answer']['subtotal'] == 89
    epoch = begin_daemon_epoch(root, provider='pilot-worker-muse')
    engine = LocalWorkflowEngine(root, epoch=epoch)
    assert engine.resume(task_id=original.id)
    job = engine.start_next()
    assert job.id == original.id
    worker = 'muse-' + uuid.uuid4().hex
    assert engine.claim(job.id, worker, os.getpid())
    target = 'target-' + uuid.uuid4().hex
    result, answer = call_runtime(root, out, 'muse', 'muse-stage2',
        'The durable task checkpoint is ' + original.result + '. Continue by multiplying the subtotal by 7. '
        'The new target marker for this stage is ' + target + '. Return JSON keys: personal_name, source_marker, previous_subtotal, total, target_marker.')
    assert answer == {'personal_name': 'LANTERN-PILOT-01', 'source_marker': checkpoint['answer']['source_marker'],
                      'previous_subtotal': 89, 'total': 623, 'target_marker': target}, answer
    engine.record_runtime_result(job.id, result, provider='muse')
    remember(root, 'The target marker is ' + target + '. Ledger task ' + str(job.id) + ' completed on Muse with total 623.')
    assert engine.finalize(job.id, 'completed', result=json.dumps({'stage': 2, 'answer': answer}), worker_id=worker)
    dump(out / 'muse-state.json', snapshot(root))
    print('Muse stage2 passed; original task', job.id, 'completed', flush=True)

def returned(root, out):
    from enoch.app.epoch import begin_daemon_epoch
    from enoch.workflows.local import LocalWorkflowEngine
    check_body(root)
    begin_daemon_epoch(root, provider='pilot-worker-codex-return')
    engine = LocalWorkflowEngine(root)
    status = engine.inspect()
    assert not status.running and not status.pending and not status.paused
    assert len(status.history) == 1 and status.history[0].status == 'completed'
    task = status.history[0]
    final = json.loads(task.result)
    assert final['stage'] == 2
    result, answer = call_runtime(root, out, 'codex', 'return-recall',
        'Report the canonical personal name, exact source marker, exact target marker and final ledger total from the persistent context. '
        'JSON keys: personal_name, source_marker, target_marker, total. Do not perform new work.')
    expected = {k: final['answer'][k] for k in ['personal_name','source_marker','target_marker','total']}
    assert answer == expected, answer
    dump(out / 'return-state.json', snapshot(root))
    print('return recall passed; completed task', task.id, 'and both memories preserved', flush=True)

def main():
    global RUN
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['source','outbound-export','import','muse-worker','return-export','returned'])
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--archive', type=Path)
    ap.add_argument('--run-id', help='source experiment ID; defaults to a fresh synthetic ID')
    a = ap.parse_args()
    a.root = a.root.resolve(); a.out = a.out.resolve(); a.out.mkdir(parents=True, exist_ok=True)
    if any(a.out.iterdir()):
        raise RuntimeError('--out must be a new empty directory for each phase/attempt')
    setup(a.root)
    from enoch.agent_identity import load_active_agent_identity
    installed = load_active_agent_identity(a.root)
    if installed is not None:
        RUN = installed['identity']['id']
        if a.run_id and a.run_id != RUN:
            raise RuntimeError('--run-id disagrees with the imported identity')
    elif a.phase == 'source':
        RUN = a.run_id or 'ripa-pilot-' + uuid.uuid4().hex
    if a.phase == 'source': source(a.root,a.out)
    elif a.phase == 'outbound-export': export(a.root,a.out,'outbound')
    elif a.phase == 'import': imported(a.root,a.out,a.archive)
    elif a.phase == 'muse-worker': muse_worker(a.root,a.out)
    elif a.phase == 'return-export': export(a.root,a.out,'return')
    elif a.phase == 'returned': returned(a.root,a.out)

if __name__ == '__main__':
    main()
