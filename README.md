# enoch-muse-runtime

**Run a persistent [Enoch](https://github.com/our-ark/enoch) agent inside Muse,
and talk to it with `@Enoch`.** Enoch has its own identity, memory and executable
body; Muse supplies the reasoning and chat environment.

Based on **RIPA — [Runtime-Independent Persistent Agents](https://arxiv.org/abs/2609.00546)**:
the agent persists while its runtime can change.

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
@Enoch 你是谁？
@Enoch 请记住：我们把这个项目叫作「青舟」。
@Enoch 我们给这个项目起了什么名字？
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
