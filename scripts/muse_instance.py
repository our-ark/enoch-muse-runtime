#!/usr/bin/env python3
"""Enoch source-checkout launcher with persistent bindings and per-run evidence.

No package installation or copied egg-info is needed for this entry point.
Other Enoch entry points still require a normal provider installation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time
import uuid

REPO = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        with temporary.open('x') as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream, indent=2, default=str)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    return json.loads(path.read_text())


def bootstrap(source):
    if not (source / 'src/enoch/agent.py').is_file():
        raise ValueError('--enoch-src must identify an Enoch source checkout')
    sys.path[:0] = [str(REPO / 'src'), str(source / 'src')] + [
        str(p) for p in sorted((source / 'libraries').glob('*/src'))]
    from enoch.providers.registry import register_provider
    from our_ark_muse import create_provider, create_chat_provider
    # Public registry API: deterministic source registration, not fabricated metadata.
    register_provider('runtime', 'muse', create_provider, replace=True)
    register_provider('chat', 'muse', create_chat_provider, replace=True)


@contextmanager
def instance_lock(root):
    path = root / '.enoch/muse-instance.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+') as lock:
        os.chmod(path, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another managed process owns this instance; no new epoch was started.') from None
        # Do not explicitly LOCK_UN: a surviving child inherits this open file
        # description and must keep the lock if the supervisor is killed.
        yield lock.fileno()


def claim_mailbox(mailbox, root):
    mailbox.mkdir(parents=True, exist_ok=True)
    marker = mailbox / '.enoch-instance.json'
    with (mailbox / '.enoch-instance.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if marker.exists():
            if read_json(marker).get('root') != str(root):
                raise RuntimeError('Mailbox belongs to another instance; choose a separate mailbox.')
        else:
            write_json(marker, {'root': str(root), 'created_at': now()})


def configure(args):
    from enoch.config import write_section_value
    from enoch.migration import assert_source_not_fenced
    from enoch.private_state import require_daemon_stopped
    if args.mailbox is None:
        raise ValueError('configure requires --mailbox')
    with instance_lock(args.root):
        assert_source_not_fenced(args.root)
        require_daemon_stopped(args.root)
        claim_mailbox(args.mailbox, args.root)
        write_section_value('providers', 'runtime', 'muse', args.root)
        write_section_value('providers', 'chat', 'muse', args.root)
        write_section_value('muse', 'mailbox', str(args.mailbox), args.root)
    return {'configured': True, 'root': str(args.root), 'mailbox': str(args.mailbox)}


def environment(root, requested_mailbox=None):
    from enoch.config import read_section
    from enoch.providers.registry import load_provider
    configured = read_section('providers', root)
    if any(configured.get(k) != 'muse' for k in ('runtime', 'chat')):
        raise RuntimeError('Persistent Muse bindings are missing; run configure first.')
    value = read_section('muse', root).get('mailbox')
    if not value:
        raise RuntimeError('Persistent mailbox is missing; run configure first.')
    mailbox = Path(value).expanduser().resolve()
    if requested_mailbox is not None and requested_mailbox != mailbox:
        raise RuntimeError('--mailbox disagrees with the configured instance mailbox.')
    selected = {'ENOCH_CHAT_PROVIDER': 'muse', 'ENOCH_RUNTIME_PROVIDER': 'muse',
                'ENOCH_MUSE_MAILBOX': str(mailbox)}
    for key, expected in selected.items():
        supplied = os.environ.get(key, '').strip()
        if supplied and (str(Path(supplied).expanduser().resolve()) if key.endswith('MAILBOX') else supplied) != expected:
            raise RuntimeError(f'{key} disagrees with the persistent binding; clear the override.')
        os.environ[key] = expected
    claim_mailbox(mailbox, root)
    # Importability alone is insufficient. Check the actual host registry.
    providers = {k: type(load_provider(k, root, name='muse')).__module__ for k in ('runtime', 'chat')}
    return {'providers': configured, 'mailbox': str(mailbox), 'registry': providers,
            'registration': 'explicit Enoch registry API from source checkout'}


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def recover(root, task_id):
    from enoch.private_state import require_daemon_stopped
    from enoch.migration import assert_source_not_fenced
    from enoch.tasks.queue import pause_task, task_queue_status
    assert_source_not_fenced(root)
    require_daemon_stopped(root)
    queue = task_queue_status(root)
    job = queue.running
    if job is None or job.id != task_id:
        raise RuntimeError('The requested task is not the running task; no recovery applied.')
    if not job.worker_pid:
        raise RuntimeError('Worker PID is unknown; cannot establish that the owner exited.')
    if alive(job.worker_pid):
        raise RuntimeError('Worker PID is still alive; no recovery applied.')
    result = pause_task(task_id, root, result=job.result, worker_id=job.worker_id,
                        event_actor='system', trigger='muse-worker-recovery')
    if result is None:
        raise RuntimeError('Task ownership changed; no recovery applied.')
    return {'before': asdict(job), 'after': asdict(result), 'action': 'paused through native API; not resumed'}


def revision(path):
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def child(args):
    environment(args.root, args.mailbox)
    os.chdir(args.root)
    if args.action in ('daemon', 'run'):
        from enoch.migration import assert_runtime_start_allowed
        assert_runtime_start_allowed(args.root)
    if args.action == 'daemon':
        runpy.run_module('enoch.agent', run_name='__main__')
    elif args.action == 'run':
        sys.argv = [str(args.script), *args.arguments]
        runpy.run_path(str(args.script), run_name='__main__')
    elif args.action == 'recover':
        result = recover(args.root, args.task_id)
        write_json(args._attempt / 'recovery.json', result)
        print(json.dumps(result, default=str))


def command(args, internal):
    values = [sys.executable, '-u', str(Path(__file__).resolve()), '--root', str(args.root),
              '--enoch-src', str(args.enoch_src), '--_attempt', str(args._attempt), internal]
    if args.mailbox is not None:
        values += ['--mailbox', str(args.mailbox)]
    values += [args.action]
    if args.action == 'run':
        values += [str(args.script), *args.arguments]
    elif args.action == 'recover':
        values += [str(args.task_id)]
    return values


def supervise(args):
    record = {'schema_version': 1, 'started_at': now(), 'status': 'starting',
              'supervisor_pid': os.getpid(), 'root': str(args.root),
              'body_source_sha': revision(args.enoch_src), 'root_revision': revision(args.root),
              'adapter_sha': revision(REPO),
              'python': sys.version, 'command': command(args, '--_child'),
              'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'adapter_source_sha256': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((REPO / 'src/our_ark_muse').glob('*.py'))}}
    status_path = args._attempt / 'status.json'
    code = 1
    try:
        if args.action == 'run':
            record['driver_sha256'] = hashlib.sha256(args.script.read_bytes()).hexdigest()
        with instance_lock(args.root) as lock_fd:
            from enoch.private_state import require_daemon_stopped
            require_daemon_stopped(args.root)
            record['binding'] = environment(args.root, args.mailbox)
            with (args._attempt / 'stdout.log').open('xb') as stdout, (args._attempt / 'stderr.log').open('xb') as stderr:
                proc = subprocess.Popen(command(args, '--_child'), stdin=subprocess.DEVNULL,
                                        stdout=stdout, stderr=stderr, start_new_session=True,
                                        pass_fds=(lock_fd,))
                record.update(status='running', child_pid=proc.pid)
                write_json(status_path, record)
                # PID compatibility for existing daemon supervisors. The lock,
                # not PID liveness alone, is the authority for duplicate starts.
                pidfile = Path(record['binding']['mailbox']) / 'enoch-daemon.pid'
                if args.action == 'daemon':
                    pidfile.write_text(str(os.getpid()) + '\n')
                    write_json(pidfile.with_name('enoch-daemon-run.json'), {'attempt': str(args._attempt)})
                previous = {}
                def forward(signum, _frame):
                    record['forwarded_signal'] = signum
                    write_json(status_path, record)
                    try:
                        os.killpg(proc.pid, signum)
                    except ProcessLookupError:
                        pass
                for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                    previous[sig] = signal.signal(sig, forward)
                try:
                    code = proc.wait()
                finally:
                    for sig, handler in previous.items():
                        signal.signal(sig, handler)
                    if args.action == 'daemon' and pidfile.exists() and pidfile.read_text().strip() == str(os.getpid()):
                        pidfile.unlink()
                record.update(status='completed' if code == 0 else 'failed', returncode=code,
                              signal=-code if code < 0 else None)
    except Exception as error:
        record.update(status='failed', error=f'{type(error).__name__}: {error}')
    record['finished_at'] = now()
    record['sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in args._attempt.iterdir() if p.name in ('stdout.log', 'stderr.log', 'recovery.json')}
    write_json(status_path, record)
    return code if code >= 0 else 128 - code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--enoch-src', type=Path, required=True)
    parser.add_argument('--mailbox', type=Path)
    parser.add_argument('--detach', action='store_true', help='start a new session and return the evidence directory')
    parser.add_argument('--_attempt', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--_child', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--_supervise', action='store_true', help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest='action', required=True)
    for action in ('configure', 'check', 'daemon'):
        commands.add_parser(action)
    runner = commands.add_parser('run')
    runner.add_argument('script', type=Path)
    runner.add_argument('arguments', nargs=argparse.REMAINDER)
    recovery = commands.add_parser('recover')
    recovery.add_argument('task_id', type=int)
    status = commands.add_parser('status')
    status.add_argument('attempt', type=Path)
    args = parser.parse_args()
    for key in ('root', 'enoch_src', 'mailbox', 'script', '_attempt'):
        value = getattr(args, key, None)
        if value is not None:
            setattr(args, key, value.expanduser().resolve())
    if hasattr(args, 'arguments') and args.arguments[:1] == ['--']:
        args.arguments = args.arguments[1:]
    if not args.root.is_dir():
        raise ValueError('--root must be an existing agent directory')
    if args.action == 'status':
        record = read_json(args.attempt / 'status.json')
        if record['status'] in ('starting', 'running') and not alive(record.get('supervisor_pid')):
            record['status'] = 'unknown'
            record['note'] = 'Supervisor exited without a captured result; do not infer success or a signal.'
        print(json.dumps(record, default=str))
        return 0
    bootstrap(args.enoch_src)
    if args.action == 'configure':
        print(json.dumps(configure(args)))
        return 0
    if args.action == 'check':
        print(json.dumps(environment(args.root, args.mailbox)))
        return 0
    if args._child:
        child(args)
        return 0
    if args._supervise:
        return supervise(args)
    directory = args.root / '.enoch/artifacts/muse-runs'
    args._attempt = directory / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex)
    args._attempt.mkdir(parents=True, mode=0o700)
    if not args.detach:
        code = supervise(args)
        print(json.dumps({'attempt': str(args._attempt), **read_json(args._attempt / 'status.json')}))
        return code
    with (args._attempt / 'supervisor.log').open('xb') as stream:
        proc = subprocess.Popen(command(args, '--_supervise'), stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=stream, start_new_session=True)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        path = args._attempt / 'status.json'
        if path.exists():
            record = read_json(path)
            print(json.dumps({'attempt': str(args._attempt), **record}))
            return 0 if record['status'] in ('running', 'completed') else 1
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    print(json.dumps({'attempt': str(args._attempt), 'status': 'unknown', 'supervisor_pid': proc.pid}))
    return 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
