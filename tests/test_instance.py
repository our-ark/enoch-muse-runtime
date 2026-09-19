"""Process-level regressions for the failures observed in the live RIPA pilot.

Uses the real Enoch migration/workflow APIs and daemon, with deterministic
mailbox responses for the daemon probe. Set ENOCH_SRC to an Enoch checkout.
"""
from __future__ import annotations
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
ENOCH = Path(os.environ.get('ENOCH_SRC', REPO.parent / 'enoch')).resolve()
LAUNCHER = REPO / 'scripts/muse_instance.py'

FIXTURE = '''import os, sys, time
from pathlib import Path
from enoch.app.epoch import begin_daemon_epoch
from enoch.workflows.local import LocalWorkflowEngine
root = Path(sys.argv[1]); mode = sys.argv[2]
if mode == "crash":
    raise RuntimeError("deliberate fixture error")
epoch = begin_daemon_epoch(root, provider="test-worker")
engine = LocalWorkflowEngine(root, epoch=epoch)
if mode == "block":
    job = engine.enqueue("muse-chat", "synthetic continuation", mode="direct")
    engine.claim(job.id, "fixture-owner", os.getpid())
    print("waiting")
    (root / ".enoch/ready").write_text(str(os.getpid()))
    time.sleep(60)
else:
    engine.resume(task_id=1)
    job = engine.start_next()
    engine.claim(job.id, "fixture-return", os.getpid())
    engine.finalize(job.id, "completed", result="continued", worker_id="fixture-return")
    print("completed", flush=True)
'''


def wait_for(fn, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = fn()
        if result:
            return result
        time.sleep(.05)
    raise AssertionError('timed out waiting for process evidence')


@unittest.skipUnless((ENOCH / 'src/enoch/agent.py').exists(), 'set ENOCH_SRC for host integration tests')
class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'agent'
        self.root.mkdir()
        self.mailbox = self.base / 'mailbox'
        self.fixture = self.base / 'worker.py'
        self.fixture.write_text(FIXTURE)
        self.env = {k:v for k,v in os.environ.items() if not k.startswith('ENOCH_')}
        self.env.update(PYTHONDONTWRITEBYTECODE='1', ENOCH_MUSE_POLL_SECONDS='.05')
        self.pids = []
        self.addCleanup(self.cleanup_processes)
        self.cli('--mailbox', str(self.mailbox), 'configure')

    def cleanup_processes(self):
        for pid in reversed(self.pids):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(LAUNCHER), '--root', str(self.root),
                                 '--enoch-src', str(ENOCH), *args], env=env or self.env,
                                capture_output=True, text=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def native(self, code, *args):
        env = dict(self.env)
        env['PYTHONPATH'] = os.pathsep.join([str(ENOCH / 'src')] + [str(x) for x in (ENOCH / 'libraries').glob('*/src')])
        result = subprocess.run([sys.executable, '-c', code, str(self.root), *args],
                                env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def start_worker(self):
        record = json.loads(self.cli('--detach', 'run', str(self.fixture), str(self.root), 'block').stdout)
        self.pids.extend([record['supervisor_pid'], record['child_pid']])
        wait_for(lambda: (self.root / '.enoch/ready').exists())
        return Path(record['attempt']), record

    def completed(self, attempt):
        def done():
            record = json.loads((attempt / 'status.json').read_text())
            return record if record['status'] in ('failed', 'completed') else None
        return wait_for(done)

    def test_fresh_source_registration_without_site_metadata(self):
        result = subprocess.run([sys.executable, '-S', str(LAUNCHER), '--root', str(self.root),
                                 '--enoch-src', str(ENOCH), 'check'], env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record['registry'], {'runtime':'our_ark_muse.core','chat':'our_ark_muse.chat'})

    def test_binding_survives_a_separate_export_process(self):
        self.root.joinpath('.gitignore').write_text('.enoch/\n')
        self.root.joinpath('body.txt').write_text('synthetic versioned body\n')
        for args in [('init',), ('add','.'), ('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','fixture')]:
            subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
        output = self.native('''import json,sys
from pathlib import Path
from enoch.private_state import migrate_private_state
from enoch.migration import export_migration_bundle, inspect_migration_bundle
r=Path(sys.argv[1]); migrate_private_state(r)
z=Path(sys.argv[2]); export_migration_bundle(z,r)
print(json.dumps(inspect_migration_bundle(z).provider_bindings))
''', str(self.base / 'export.zip'))
        bindings = json.loads(output)
        self.assertEqual(bindings['runtime'], 'muse')
        self.assertEqual(bindings['chat'], 'muse')

    def test_rejects_conflicting_environment_and_shared_mailbox(self):
        result = self.cli('check', ok=False, env={**self.env, 'ENOCH_RUNTIME_PROVIDER':'codex'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('disagrees', result.stderr)
        other = self.base / 'other'; other.mkdir()
        result = subprocess.run([sys.executable,str(LAUNCHER),'--root',str(other),'--enoch-src',str(ENOCH),
                                 '--mailbox',str(self.mailbox),'configure'],env=self.env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((other / '.enoch/config.yaml').exists())

    def test_duplicate_start_cannot_fence_worker_and_crash_can_be_recovered(self):
        attempt, record = self.start_worker()
        epoch = (self.root / '.enoch/daemon_epoch.json').read_bytes()
        duplicate = self.cli('run', str(self.fixture), str(self.root), 'block', ok=False)
        self.assertNotEqual(duplicate.returncode,0)
        self.assertIn('Another managed process', duplicate.stdout)
        self.assertEqual((self.root / '.enoch/daemon_epoch.json').read_bytes(),epoch)
        live_recovery = self.cli('recover','1',ok=False)
        self.assertNotEqual(live_recovery.returncode,0)
        os.kill(record['child_pid'],signal.SIGKILL)
        failed = self.completed(attempt)
        self.assertEqual(failed['returncode'],-signal.SIGKILL)
        self.assertEqual(failed['signal'],signal.SIGKILL)
        self.assertEqual((attempt/'stdout.log').read_text(),'waiting\n')
        self.assertEqual(failed['driver_sha256'], hashlib.sha256(self.fixture.read_bytes()).hexdigest())
        recovery = json.loads(self.cli('recover','1').stdout)
        self.assertEqual(recovery['status'],'completed')
        details=json.loads((Path(recovery['attempt'])/'recovery.json').read_text())
        self.assertEqual(details['after']['id'],1)
        self.assertEqual(details['after']['status'],'paused')
        resumed=json.loads(self.cli('run',str(self.fixture),str(self.root),'continue').stdout)
        self.assertEqual(resumed['status'],'completed')
        self.assertNotEqual(resumed['attempt'],str(attempt))
        self.assertEqual(json.loads((attempt/'status.json').read_text())['returncode'],-signal.SIGKILL)
        self.assertEqual(json.loads((self.root/'.enoch/task_queue.json').read_text())['history'][0]['id'],1)

    def test_supervisor_crash_leaves_child_lock_and_unknown_exit(self):
        attempt, record = self.start_worker()
        os.kill(record['supervisor_pid'],signal.SIGKILL)
        time.sleep(.3)
        duplicate = self.cli('run',str(self.fixture),str(self.root),'block',ok=False)
        self.assertNotEqual(duplicate.returncode,0)
        self.assertIn('Another managed process',duplicate.stdout)
        # The original on-disk evidence never manufactures an exit or signal.
        status=json.loads((attempt/'status.json').read_text())
        self.assertNotIn('returncode',status)
        self.assertNotIn('signal',status)
        os.kill(record['child_pid'],signal.SIGKILL)

    def test_signal_forwarding_and_nonzero_logs_are_preserved(self):
        attempt, record=self.start_worker()
        os.kill(record['supervisor_pid'],signal.SIGTERM)
        status=self.completed(attempt)
        self.assertEqual(status['forwarded_signal'],signal.SIGTERM)
        self.assertEqual(status['returncode'],-signal.SIGTERM)
        failure=json.loads(self.cli('run',str(self.fixture),str(self.root),'crash',ok=False).stdout)
        self.assertIn('deliberate fixture error',(Path(failure['attempt'])/'stderr.log').read_text())
        self.assertEqual(failure['returncode'],1)
        self.assertEqual(json.loads((attempt/'status.json').read_text())['returncode'],-signal.SIGTERM)

    def test_unknown_worker_owner_cannot_be_recovered(self):
        self.native('''import sys
from pathlib import Path
from enoch.workflows.local import LocalWorkflowEngine
LocalWorkflowEngine(Path(sys.argv[1])).enqueue("muse-chat","unclaimed",mode="direct")
''')
        before=(self.root/'.enoch/task_queue.json').read_bytes()
        result=self.cli('recover','1',ok=False)
        self.assertNotEqual(result.returncode,0)
        status=json.loads(result.stdout)
        self.assertIn('Worker PID is unknown',(Path(status['attempt'])/'stderr.log').read_text())
        self.assertEqual((self.root/'.enoch/task_queue.json').read_bytes(),before)

    def test_managed_pilot_phase_and_export_keep_muse_bindings(self):
        # Real clean body and real workflow/provider, deterministic model reply.
        clone=self.base/'body'
        subprocess.run(['git','clone','--local',str(ENOCH),str(clone)],check=True,capture_output=True)
        self.root=clone
        self.mailbox=self.base/'pilot-mailbox'
        self.cli('--mailbox',str(self.mailbox),'configure')
        self.native('''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[2])
import ripa_pilot as p
from enoch.private_state import migrate_private_state
from enoch.agent_identity import install_agent_identity
from enoch.workflows.local import LocalWorkflowEngine
r=Path(sys.argv[1]);migrate_private_state(r);install_agent_identity(p.identity(),r)
p.remember(r,"The source marker is source-fixture. The synthetic ledger entries are 17, 29, and 43.")
engine=LocalWorkflowEngine(r);job=engine.enqueue("muse-chat","portable task",mode="direct")
engine.pause(job.id,result=json.dumps({"stage":1,"answer":{"personal_name":"LANTERN-PILOT-01","source_marker":"source-fixture","subtotal":89}}))
''',str(REPO/'scripts'))
        out=self.base/'worker-evidence'
        launched=json.loads(self.cli('--detach','run',str(REPO/'scripts/ripa_pilot.py'),
                                    'muse-worker','--root',str(self.root),'--out',str(out)).stdout)
        self.pids.extend([launched['supervisor_pid'],launched['child_pid']])
        req_path=self.mailbox/'inbox/ripa-muse-pilot-20260919-muse-stage2.json'
        wait_for(req_path.exists)
        req=json.loads(req_path.read_text())
        import re
        target=re.search(r'The new target marker for this stage is (target-[a-f0-9]+)',req['message']).group(1)
        answer={'personal_name':'LANTERN-PILOT-01','source_marker':'source-fixture',
                'previous_subtotal':89,'total':623,'target_marker':target}
        subprocess.run([sys.executable,str(REPO/'scripts/mailbox_reply.py'),req['request_id'],'--attempt',req['attempt'],
                        '--mailbox',str(self.mailbox),'--text',json.dumps(answer)],check=True,capture_output=True)
        completed=self.completed(Path(launched['attempt']))
        self.assertEqual(completed['returncode'],0,(Path(launched['attempt'])/'stderr.log').read_text())
        export=self.base/'export-evidence'
        result=self.cli('run',str(REPO/'scripts/ripa_pilot.py'),'return-export','--root',str(self.root),'--out',str(export))
        self.assertEqual(json.loads(result.stdout)['returncode'],0)
        inspection=json.loads((export/'return-export.json').read_text())['inspection']
        self.assertEqual(inspection['provider_bindings']['runtime'],'muse')
        self.assertEqual(inspection['provider_bindings']['chat'],'muse')
        self.assertEqual(json.loads((out/'muse-state.json').read_text())['workflow']['history'][0]['id'],1)
        duplicate=self.cli('run',str(REPO/'scripts/ripa_pilot.py'),'muse-worker','--root',str(self.root),'--out',str(self.base/'retry'),ok=False)
        self.assertNotEqual(duplicate.returncode,0)

    def test_real_daemon_conversation_and_shutdown(self):
        record=json.loads(self.cli('--detach','daemon').stdout)
        self.pids.extend([record['supervisor_pid'],record['child_pid']])
        attempt=Path(record['attempt'])
        inbox=self.mailbox/'chat_inbox'; inbox.mkdir(exist_ok=True)
        (inbox/'1.json').write_text(json.dumps({'seq':1,'text':'Reply with PROBE-OK and no actions.','created_at':time.time()}))
        def request():
            files=list((self.mailbox/'inbox').glob('*.json'))
            return json.loads(files[0].read_text()) if files else None
        req=wait_for(request)
        subprocess.run([sys.executable,str(REPO/'scripts/mailbox_reply.py'),req['request_id'],
                        '--attempt',req['attempt'],'--mailbox',str(self.mailbox),'--text','PROBE-OK'],
                        check=True,capture_output=True,env=self.env)
        wait_for(lambda:any(json.loads(x.read_text()).get('text')=='PROBE-OK' for x in (self.mailbox/'chat_outbox').glob('*.json')))
        os.kill(record['supervisor_pid'],signal.SIGTERM)
        status=self.completed(attempt)
        self.assertEqual(status['status'],'completed')
        self.assertEqual(status['returncode'],0)
        self.assertIn('Enoch is listening on muse.',(attempt/'stdout.log').read_text())
        self.assertFalse((self.mailbox/'enoch-daemon.pid').exists())


class PilotDriverTests(unittest.TestCase):
    def test_duplicate_worker_precondition_does_not_advance_epoch(self):
        if not (ENOCH/'src/enoch/agent.py').exists(): self.skipTest('set ENOCH_SRC')
        spec=importlib.util.spec_from_file_location('pilot_v2',REPO/'scripts/ripa_pilot.py')
        pilot=importlib.util.module_from_spec(spec); spec.loader.exec_module(pilot)
        pilot.setup(ENOCH)
        from enoch.app.epoch import begin_daemon_epoch
        from enoch.workflows.local import LocalWorkflowEngine
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); begin_daemon_epoch(root)
            LocalWorkflowEngine(root).enqueue('muse-chat','already running',mode='direct')
            before=(root/'.enoch/daemon_epoch.json').read_bytes()
            with patch.object(pilot,'check_body'), self.assertRaisesRegex(RuntimeError,'Expected one paused'):
                pilot.muse_worker(root,root/'out')
            self.assertEqual((root/'.enoch/daemon_epoch.json').read_bytes(),before)


if __name__=='__main__': unittest.main()
