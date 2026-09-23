# muse-account-migration

Export/import Muse-side Enoch agents between accounts/hosts.
Wraps the official `enoch.migration` API; adds CLI handling,
a production guard, and bridge-mailbox handling. No new bundle format.

## Scripts

- `export_agent.py <agent_root> <out.zip>` — export an agent to a
  verified migration bundle. The agent's daemon must be stopped first.
  Refuses live production roots unless `--force`.
- `inspect_bundle.py <bundle.zip> [--root <agent_root>]` — verify
  manifest integrity and per-file hashes. Exit 0 means all hashes pass.

## Notes

- The bundle contains the agent's portable private state only.
  The bridge `mailbox/` (runtime queues) is stashed aside during export
  and restored afterwards; it is not part of the bundle.
- Chat history (group/private/zixia-drops) is exported separately;
  see `export_history.py` (planned).
- Import side (`import_agent.py`: inspect → import → verify → activate,
  then provider/mailbox setup) is planned.

## Testing

Test on copies only, never on the live roots. A copied root carries the
production daemon lock (`.enoch/daemon_epoch.json`); neutralize it in the
copy before export. Verified 2026-09-23: export of a 白晶晶 copy →
54 files, `inspect_bundle.py` reports "Migration bundle validation passed".
