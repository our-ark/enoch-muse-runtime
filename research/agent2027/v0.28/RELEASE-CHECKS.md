# What was checked for v0.28

- Local comparison: all 114 other included frozen source files and the original 20-episode coding retain their bytes. The historical receipt is preserved under an explicitly historical filename; the active receipt is derived metadata. The three export objects differ only at the 31 path fields and two marked preference fields. Public ledger metadata is updated separately.
- Public-copy consistency: file hashes, ledger anchors, eight JSON pointers, original episode counts, preserved request/reply identifiers and texts, selected two-turn delivery links, and empty pilot forms.
- Distribution check: the ZIP and browsable directory contain identical artifact files; the coordinator and both nested stage ZIPs retain their manifests. No unredacted host-export bytes or original sensitive strings are included.
- Privacy screening: checked for the removed strings, common credential patterns, email addresses, IPv4 addresses and signed-URL parameters. Screening does not guarantee absence of all potentially sensitive information.

These are copy-integrity and selected linkage checks, not authentication of the original hosts, exhaustive coverage, model replay, independent annotation review or evidence that the research protocol is more accurate than transcript-only interpretation. The nine historical exporter tests remain software tests; the independent-review pilot is unrun.
