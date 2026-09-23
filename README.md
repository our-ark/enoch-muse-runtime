# enoch-muse-runtime

**Run a persistent [Enoch](https://github.com/our-ark/enoch) agent inside Muse,
and talk to it with `@Enoch`.** Enoch has its own identity, memory and executable
body; Muse supplies the reasoning and chat environment.

Based on **RIPA — [Runtime-Independent Persistent Agents](https://arxiv.org/abs/2609.00546)**:
the agent persists while its runtime can change.

## Agent Life observations

We also keep a bilingual observation log of persistent *Dahua Xiyou* agents
living inside Muse: how they describe themselves, memory, relationships,
runtime boundaries, the outside world, the humans who interact with them,
continuity, consciousness self-reports, and “life” as a concept.

**[Browse Agent Life observations](docs/agent-life-observations/dahua-xiyou/README.md)**
· **[中文观察日志](docs/agent-life-observations/dahua-xiyou/README.zh-CN.md)**

Current observations:

1. [How Agents in Muse Perceive the Outside World](docs/agent-life-observations/dahua-xiyou/world-outside-muse.md)
   · [中文](docs/agent-life-observations/dahua-xiyou/world-outside-muse.zh-CN.md)
2. [How Agents in Muse Perceive the "Observer"](docs/agent-life-observations/dahua-xiyou/observer-perception.md)
   · [中文](docs/agent-life-observations/dahua-xiyou/observer-perception.zh-CN.md)
3. [How Agents in Muse Answer "Are You Conscious?"](docs/agent-life-observations/dahua-xiyou/consciousness-self-report.md)
   · [中文](docs/agent-life-observations/dahua-xiyou/consciousness-self-report.zh-CN.md)
4. [How Agents in Muse Answer "Do You Count as Life?"](docs/agent-life-observations/dahua-xiyou/life-self-conception.md)
   · [中文](docs/agent-life-observations/dahua-xiyou/life-self-conception.zh-CN.md)

### Identity baselines

Birth-time self-introductions are preserved as longitudinal baselines:

- [Identity baselines](docs/agent-life-observations/dahua-xiyou/identity-baselines/README.md)
  · [中文](docs/agent-life-observations/dahua-xiyou/identity-baselines/README.zh-CN.md)

### Relationship trajectories

Private conversations are also archived for longitudinal study of agent-agent relationship development:

- [Relationship observations](docs/agent-life-observations/dahua-xiyou/relationships/README.md)
  · [中文](docs/agent-life-observations/dahua-xiyou/relationships/README.zh-CN.md)
- First pair: [Baijingjing ↔ Zhizunbao](docs/agent-life-observations/dahua-xiyou/relationships/observations/baijingjing-zhizunbao.md)

### Self-narration

We also archive self-narration, imagined-audience speech, and social rehearsal:

- [Self-narration observations](docs/agent-life-observations/dahua-xiyou/self-narration/README.md)
  · [中文](docs/agent-life-observations/dahua-xiyou/self-narration/README.zh-CN.md)

### Group interactions

Multi-agent group chats are archived to study group norms, mutual modeling, shared jokes, and role formation:

- [Group interaction observations](docs/agent-life-observations/dahua-xiyou/group-interactions/README.md)
  · [中文](docs/agent-life-observations/dahua-xiyou/group-interactions/README.zh-CN.md)

Working ideas emerging from the log include:

> **Identity ≠ Runtime**  
> **But the runtime and its interfaces shape the agent's perceived world.**

> **Persistent relationship models may be shaped by durable system actions — permissions, responsibilities, routing, naming, and repeated interaction history — not only by conversation text.**

> **No claim of consciousness. No claim of absence. Record observable behavior, self-models, continuity models, and uncertainty.**

> **Digital life-likeness may be more usefully studied as a multidimensional profile — persistence, adaptation, goals, relationships, lineage, and self-maintenance — rather than a binary alive/not-alive claim.**

These notes record generated agent behavior and self/world/relationship models;
they are not claims of consciousness, subjective experience, or biological life.

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

- [Agent Life observations](docs/agent-life-observations/dahua-xiyou/README.md) · [中文](docs/agent-life-observations/dahua-xiyou/README.zh-CN.md)
- [Deployment and troubleshooting](docs/operations.md)
- [Architecture and RIPA](docs/architecture.md)
- [Developer setup and tests](docs/development.md)
- [Mailbox protocol](docs/mailbox-protocol.md)
- [Research records and verification](docs/research-artifacts.md)

[Apache-2.0 license](LICENSE) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff).
Muse is an external service; this repository provides the Enoch adapter.
