# enoch-muse-runtime

**Run a persistent [Enoch](https://github.com/our-ark/enoch) agent inside Muse,
and talk to it with `@Enoch`.** Enoch has its own identity, memory and executable
body; Muse supplies the reasoning and chat environment.

Based on **RIPA — [Runtime-Independent Persistent Agents](https://arxiv.org/abs/2609.00546)**:
the agent persists while its runtime can change.

## Video overview

[![Same Agents. New Runtime. — Watch the 90-second overview](https://img.youtube.com/vi/yKhXH5fG51Y/hqdefault.jpg)](https://www.youtube.com/watch?v=yKhXH5fG51Y)

**[Watch the 90-second overview — Same Agents. New Runtime. (Chinese)](https://www.youtube.com/watch?v=yKhXH5fG51Y)**

Meet two persistent agents running inside Muse, with their own identity,
memory, and mailbox-based interaction. For evaluated migration workflows and
reproducibility, see the [research records](docs/research-artifacts.md).

## Install in Muse

Paste this into Muse:

```text
Install https://github.com/our-ark/enoch-muse-runtime in your cloud workspace.
Follow https://github.com/our-ark/enoch-muse-runtime/blob/main/prompts/deploy-enoch.md.

Deploy an instance named Enoch as my persistent assistant.
I prefer replies in Chinese.
If Enoch already exists, preserve its state and report the existing instance.

Set up @Enoch message routing and keep the message bridge running.
Verify setup with a real reply from Enoch before reporting success.
```

You can change the name, mission and language preference. **Enoch runs in
Muse's cloud environment**; no local installation is required. Muse needs
workspace execution and background scheduling capabilities to complete setup.

## Talk to Enoch

After Muse confirms setup, send:

```text
@Enoch Who are you?
@Enoch Please remember: we named this project "Qingzhou" (BlueBoat).
@Enoch What did we name this project?
```

For another instance name, use its configured `@<name>` instead.

| Message | What it does |
|---|---|
| `@Enoch /help` | Show available commands |
| `@Enoch /status` | Check the agent's status |
| `@Enoch /do <task>` | Start a task through Enoch |

Replies may take a little time because they pass through Muse's message
bridge. If Enoch stops responding, ask Muse to check the existing instance
and its message bridge while preserving its memory and state.

## More documentation

- [Deployment and troubleshooting](docs/operations.md)
- [Architecture and RIPA](docs/architecture.md)
- [Developer setup and tests](docs/development.md)
- [Mailbox protocol](docs/mailbox-protocol.md)
- [Research records and verification](docs/research-artifacts.md)

[Apache-2.0 license](LICENSE) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff).
Muse is an external service; this repository provides the Enoch adapter.
