# Minimal redaction for the public release

Version v0.28, 16 October 2026. The owner authorized publication after minimal redaction.

Three selected host exports are distributed as explicitly redacted derivatives, not byte-identical raw exports. The originals remain in the authors' private working archive and are not included in this Git branch or any distributed ZIP.

## Exact scope

- Replaced the same host-specific absolute directory prefix with `<HOST_ROOT>` in 31 fields across three JSON files. Relative agent, mailbox and file paths remain distinguishable. Generic executable paths in the model-change chronology remain because they describe the operational intervention.
- Replaced two copies of one operator communication-preference sentence with an explicit redaction marker. Memory record IDs, surrounding character settings, research-relevant instructions and the recorded intervention rule remain.
- Kept dialogue, timestamps, session/message/request/attempt identifiers, selected trace links, original coding and all judgments unchanged. No substantive agent response or unfavorable finding was removed.

`redaction-manifest.json` lists affected JSON pointers, change categories, original file hashes and public file hashes. It does not disclose the removed prefix or preference text. Public ledger hashes and the active receipt refer to public bytes; the historical original receipt is labeled separately. Hashes of private originals are author-supplied commitments, not a way for readers to inspect omitted bytes or authenticate original deployment.

## Audit boundary

The local build compared every JSON leaf before and after transformation and allowed only the documented 33 string-field edits. Public readers can verify public hashes and retained links with `verify_artifact.py`, but cannot independently reconstruct the private originals. The redacted requests must not be represented as complete original inference contexts or used as exact replay inputs.

The release and nested pilot archives were checked for the removed strings and common credential patterns. Such screening is not a guarantee against every possible disclosure. No model execution or independent protocol validation was performed.
