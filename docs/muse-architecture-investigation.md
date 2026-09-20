# Investigating Muse from Inside

## Self-Model, Runtime Boundaries, and the Enoch Integration

**Status:** Architecture investigation / case study  
**Snapshot:** September 2026  
**Scope:** One observed Muse deployment and the `enoch-muse-runtime` integration

> **Key lesson:** An agent can have access to real pieces of its own implementation and still hallucinate how those pieces fit together.

---

## 1. Why We Investigated

While integrating Enoch with Meta Muse, we wanted to answer a seemingly simple question:

**What exactly is Muse's architecture from the point of view of an agent running inside it?**

This mattered for two reasons.

First, Enoch treats the reasoner, harness, host, and interaction surfaces as replaceable runtime components. To understand what Muse can provide as a runtime, we needed to know where its persistent state, harness, model access, and security boundaries actually live.

Second, Muse itself could answer questions about its architecture. That created an unexpected experiment: **how accurate is an agent's self-model of the system executing it?**

The answer turned out to be more interesting than the architecture alone.

Muse had access to many real implementation details—files, processes, environment variables, socket names, and runtime behavior—but repeatedly mixed direct observation with plausible inference. The resulting explanations were coherent and confident, but several were wrong.

This document records the investigation, the corrections, and the architectural picture that survived verification.

---

## 2. Evidence Labels

To avoid repeating the failure mode we observed, every important claim in this report should be read using four evidence classes:

- **[OBSERVED]** — directly observed in the inspected runtime using read-only commands.
- **[DOCUMENTED]** — stated in Meta's published Muse architecture documentation.
- **[INFERRED]** — a plausible interpretation of observed or documented facts, but not directly verified.
- **[UNKNOWN]** — not established by the available evidence.

The investigation was intentionally conservative:

- read-only inspection;
- no socket dialing;
- no permission bypass;
- no modification of files, processes, mounts, or configuration;
- no attempt to reverse-engineer protected components beyond ordinary runtime inspection.

This distinction between observation and inference became one of the main findings of the investigation.

---

## 3. The Self-Model That Muse Initially Gave Us

The investigation did not begin with system inspection. It began by asking Muse how it worked.

### 3.1 Initial claim: "I have no daemon"

Muse initially described itself approximately as follows:

- the VM was a workspace containing memory, tools, and files;
- the real reasoning system lived on Meta infrastructure;
- each user message caused a temporary agent execution;
- after the turn completed, that execution disappeared;
- continuity came from persistent files and conversation state;
- unlike Enoch, Muse itself did not have a persistent daemon.

This led to a simple mental model:

```text
persistent state
      |
      v
temporary platform agent loop
      |
      v
shared model
      |
      v
response
```

Under this model, Muse described itself as closer to a worker with persistent context than a continuously running agent.

That interpretation turned out to be wrong.

---

## 4. First Correction: Hatch Exists

When the runtime was inspected, a persistent Hatch process was visible.

**[OBSERVED]**

The investigation found a running `hatch daemon` and `hatch-execd` in the Muse environment.

Meta's published architecture independently confirms the broader point:

**[DOCUMENTED]**

Meta describes the **Hatch daemon as "the core agentic harness"**, running inside a `systemd-nspawn` runtime container together with the workspace, files, binaries, and tools used by Muse.

This immediately invalidated the original claim that Muse had no daemon.

Muse's own correction captured the failure well:

> It had treated "I cannot see the implementation" as "it does not exist."

This was the first important self-model failure: a **false negative caused by partial observability**.

---

## 5. Second Model: "Server-Side Loop + Local Daemon"

After discovering Hatch, Muse constructed a new explanation.

It proposed that the harness was split into two halves:

```text
server-side agent loop
  - context construction
  - reasoning
  - model invocation
  - tool interpretation

local Hatch daemon
  - shell execution
  - files
  - browser/tool backends
```

This model was attractive because it reconciled the earlier belief in an ephemeral server-side loop with the newly observed persistent daemon.

It was also not supported by the published architecture.

Meta's architecture description identifies Hatch itself as the **core agentic harness** inside the runtime cell. The services outside that cell are described as security-sensitive infrastructure: inference and telemetry proxies, safety systems, credential handling, connector workers, Sentinel, and durable application state.

So the "server-side agent loop + local tool daemon" explanation was another example of the same pattern:

1. observe a real component;
2. preserve an earlier assumption;
3. construct a plausible architecture connecting the two;
4. state the reconstruction too confidently.

---

## 6. Current High-Level Architecture

The architecture that is supported by Meta's documentation and the observed runtime is closer to the following:

```text
                         External model infrastructure
                                   ^
                                   |
                              inference path
                                   |
+----------------------------------------------------------------+
|                         Muse VM                                |
|                                                                |
|  +---------------- Runtime Cell ----------------------------+   |
|  |                                                         |   |
|  |  Hatch daemon                                           |   |
|  |  (core agentic harness)                                 |   |
|  |                                                         |   |
|  |  workspace / files / tools / agent-created code         |   |
|  |                                                         |   |
|  +---------------------------------------------------------+   |
|                 | Unix-domain IPC                              |
|                 v                                              |
|  Host-side / security-sensitive services                       |
|  - inference / telemetry proxies                               |
|  - hatch-safety                                                |
|  - authd                                                       |
|  - privsep workers                                             |
|  - Sentinel                                                    |
|  - postgres durable application state                          |
|                                                                |
+----------------------------------------------------------------+
```

Meta describes the security model as **"two isolated security domains on one box."**

**[DOCUMENTED]**

The runtime cell has its own root filesystem. Root inside the runtime cell maps to an unprivileged host user, so runtime-cell root is not host root.

Communication between the runtime cell and other VM services uses Unix-domain sockets with `SO_PEERCRED` and peer ACLs.

The model itself is not hosted in the runtime cell. Meta states that Muse sends limited data outside the VM when necessary for inference and telemetry.

---

## 7. "Dedicated to You" Is Not the Same as "Governed by You"

The presence of a persistent Hatch daemon clarified an important distinction for the Enoch/RIPA comparison.

Muse does have a persistent harness.

But the Hatch implementation is platform-owned infrastructure.

During the investigation:

**[OBSERVED]**

- `/opt/hatch/bin/hatch` was present as a large stripped ELF binary;
- the binary could be observed as a file and as a running process;
- its source code was not present in the inspected workspace;
- some runtime-cell scripts were visible, but they did not constitute the source of the core harness.

Therefore, the useful distinction is not:

```text
Muse: no daemon
Enoch: daemon
```

It is:

```text
Muse:
persistent platform-provided harness

Enoch:
versioned, inspectable, user-governed executable body
```

This is also why "daemon" and "body" should not be treated as synonyms.

A process can be dedicated to a user without the user governing its implementation.

---

## 8. The Inference Proxy Investigation

The next question was whether Enoch could bypass the mailbox bridge and directly use Muse's inference path.

Muse initially produced a confident multi-layer explanation:

- the inference socket was not available;
- authorization was tied to an agent-execution identity;
- a third-party agent was not a valid caller;
- the mailbox bridge was the only legitimate route;
- direct access would amount to improperly using another agent's reasoner binding.

Most of those statements were not yet verified.

We therefore repeated the investigation using the evidence labels above.

### 8.1 What was observed

**[OBSERVED]**

Environment variables included values such as:

```text
JARVIS_INFERENCE_PROXY_SOCK=/run/hatch/proxy/inference.sock
JARVIS_INFERENCE_HOSTNAME=<uuid>
```

Other visible variables referenced services such as authd and Sentinel.

`/proc/net/unix` contained entries associated with `inference.sock`, as well as other sockets such as telemetry, postgres, and exec-related endpoints.

The number of live inference-related entries changed during observation.

That change alone does **not** prove that a particular entry corresponded to the current reasoning turn.

**[INFERRED, low confidence]**

It is plausible that some of the observed activity corresponded to ongoing Muse inference, but this was not established.

### 8.2 The pathname boundary

The nominal path:

```text
/run/hatch/proxy/inference.sock
```

was present in environment metadata and visible as a Unix-socket name in `/proc/net/unix`.

However:

**[OBSERVED]**

The pathname could not be resolved in the inspected mount namespaces for:

- the Muse runtime cell;
- the Enoch process;
- the inspectable host view.

Path lookup returned `ENOENT`.

This gives us a strong scoped conclusion:

> **Enoch cannot connect to the known inference proxy by that pathname from its current mount namespace.**

The reason the pathname is unavailable is not fully established.

Possible explanations include an inaccessible mount namespace, a pathname unlinked after binding, inherited file descriptors, or another forwarding layer.

**[UNKNOWN]**

### 8.3 What remains unknown

The investigation did **not** establish:

- which process owns the inference listener;
- the proxy's exact request protocol;
- the proxy's proxy-specific authorization logic;
- whether per-execution metadata participates in authorization;
- whether another supported inference interface exists;
- what the visible `space-inference.sock` endpoint actually does;
- whether the mailbox bridge is the only possible integration mechanism in an absolute sense.

Meta documents `SO_PEERCRED` and peer ACLs as part of the VM's IPC security model.

**[DOCUMENTED]**

That does not, by itself, prove the precise authorization behavior of the inference proxy.

---

## 9. Claims: Initial Belief vs. Current Status

| Claim | Initial self-model | Current status |
|---|---|---|
| Muse has no persistent daemon | Claimed true | **False** — Hatch daemon exists |
| Muse is only an ephemeral worker | Claimed true | **Unsupported / oversimplified** |
| Agent loop lives in a separate server-side orchestrator | Claimed true | **Not supported by Meta's published architecture** |
| Hatch only executes tools | Claimed true | **False / incomplete** — Meta calls Hatch the core agentic harness |
| Muse has a dedicated VM | Yes | **Documented** |
| Runtime-cell root is host root | Implicitly treated that way at times | **False** — Meta documents user-namespace isolation |
| `/run/hatch/proxy/inference.sock` is a real internal name | Initially uncertain | **Observed** in env and `/proc/net/unix` |
| Enoch can resolve that pathname | Assumed no | **Observed false** in current mount namespace |
| Any runtime-cell root process can call it | Claimed false for broad reasons | **False for the observed pathname**; root cannot resolve it |
| Proxy authorization is tied to "agent execution identity" | Claimed | **Unknown** |
| Direct proxy access is absolutely impossible | Claimed | **Not proven** |
| Mailbox is the only possible path | Claimed | **Not proven** |
| Mailbox is the only integration path we have actually verified | — | **True for this investigation** |

---

## 10. What This Means for Enoch on Muse

The current Enoch integration uses Muse through an asynchronous mailbox bridge.

At a high level:

```text
Enoch daemon
    |
    | reasoning request
    v
mailbox
    |
    v
Muse execution
    |
    | reasoning result
    v
mailbox
    |
    v
Enoch daemon
```

This remains the **verified working integration path**.

The investigation does not prove that it is the only architecture Muse could ever support. It shows that the known inference-proxy pathname is not directly resolvable from Enoch's current execution context.

This distinction matters.

The correct claim is:

> **Mailbox is the integration route we have verified. Direct use of the known inference-proxy pathname is blocked from Enoch's current mount namespace. Other supported paths have not been established.**

Not:

> "Mailbox is the only path that can exist."

---

## 11. RIPA Interpretation

Using the RIPA decomposition:

```text
E_t = (R_t, H_t, D_t)
```

a useful approximation for the observed Muse deployment is:

- **R_t** — external model/reasoning service reached through Muse's controlled inference path;
- **H_t** — Hatch, the core agentic harness;
- **D_t** — the Muse VM/runtime environment;
- **S_t** — Muse interaction surfaces and clients.

For the persistent agent state:

```text
P_t = (I_t, M_t, B_t)
```

Muse clearly exposes durable identity/memory/workspace state.

The more interesting difference from Enoch is the status of **B_t**, the software body.

Enoch's executable body is intended to be:

- inspectable;
- versioned;
- changeable;
- reviewable;
- governed by the human operator.

Muse can write tools and code in its workspace, and Meta explicitly describes Muse as able to build tools and edit itself. That is important.

However, the **core Hatch harness** remains platform-owned and is not source-governed by the user in the inspected deployment.

So the architectural distinction is better expressed as:

> **Muse provides an extensible persistent agent runtime. Enoch explores a user-governed persistent software body that can be rebound across runtimes.**

This is a comparison of control boundaries, not a claim that Muse is "not an agent."

---

## 12. The More General Finding: Architectural Self-Knowledge

The most interesting result of the investigation was not a particular socket or process.

It was how Muse reasoned about itself.

We observed three distinct self-model failure modes.

### 12.1 False negative

> "I have no daemon."

A persistent Hatch daemon existed.

### 12.2 Architectural confabulation

After discovering the daemon, Muse constructed a split architecture in which a server-side loop performed reasoning while Hatch acted only as the local execution half.

That model was coherent but not supported by Meta's architecture description.

### 12.3 Real clue, invented semantics

Muse later used real internal evidence—a genuine environment variable and socket name—but inferred unverified semantics around:

- authorization;
- ownership;
- supported caller identity;
- allowed integration paths.

The underlying problem was not lack of information.

It was failure to reliably distinguish:

```text
what I observed
        from
what I inferred
```

That suggests a broader engineering question for persistent agents:

> **How should an agent maintain a grounded, verifiable model of its own deployed architecture?**

Identity self-report, capability self-report, and architecture self-report should not automatically be treated as system truth.

---

## 13. Practical Method: Force Epistemic Separation

The investigation became substantially more reliable after requiring every architecture claim to carry one of four labels:

```text
[OBSERVED]
[DOCUMENTED]
[INFERRED]
[UNKNOWN]
```

This simple discipline prevented a common failure mode:

```text
partial observation
      ↓
plausible reconstruction
      ↓
confident architectural claim
```

For agents that inspect, debug, or evolve themselves, this may be a useful design pattern in its own right.

A self-inspecting agent should be able to answer not only:

> "What do I believe my architecture is?"

but also:

> "Which parts of that belief are directly grounded?"

---

## 14. Limitations

This report is intentionally scoped.

- It describes one Muse deployment observed in September 2026.
- Muse is an evolving product; implementation details may change.
- Some system components were intentionally outside the runtime's visibility.
- No protected socket was dialed as part of the investigation.
- No claim is made about interfaces that were not observed or documented.
- Process ownership and proxy-specific authorization semantics remain partially unknown.
- The report distinguishes Meta's published architecture from local observations and from our own interpretation.

This is an architecture investigation, not a security vulnerability report.

---

## 15. Takeaways

Three conclusions survived the investigation.

**1. Muse is a persistent agent with a real local harness.**  
The initial "no daemon" self-description was wrong.

**2. Persistence and governance are different properties.**  
A harness can be dedicated to a user while remaining platform-owned.

**3. Agent self-report is not system ground truth.**  
An agent can know many real details about itself while hallucinating the architecture that connects them.

The final lesson is the simplest:

> **An agent can have access to pieces of its own implementation — and still hallucinate how those pieces fit together.**

For long-lived agents, remembering who they are may not be enough.

They may also need a verifiable way to know **what they are**.

---

## References

- Meta AI Research, **"How We Built Safety Into Muse"**  
  https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse

- **Runtime-Independent Persistent Agents (RIPA)**  
  https://arxiv.org/abs/2609.00546

- **Code Is the Body**  
  https://arxiv.org/abs/2607.28691
