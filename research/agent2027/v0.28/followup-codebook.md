# Follow-up episode coding, v0.16

Prepared 13 October 2026 for Table I and Section IV.C. [followup-coding.csv](followup-coding.csv) contains all 20 supplied follow-up sessions, F02-F21. F01 (3 October) is contextual and excluded from the denominator. [summarize_followup.py](summarize_followup.py) checks source hashes and literal anchors and regenerates [followup-coding-summary.json](followup-coding-summary.json).

## Status and units

This is one retrospective, Codex-produced coding pass after reading the archive and the observer's concern about stagnation. It is not preregistered, independent coding, a validated scale, or an inter-rater reliability study. No independent human validation is recorded. The codebook and row-level judgments were developed iteratively in the same pass. Counts summarize attributed text in the supplied archive, not autonomous generations, all deployment interactions, or population rates. The author should review judgments before submission.

A unit is one archived group round, peer-private session, or host-private slot. The denominator is six group, nine peer-private, and five host-private episodes. Different surfaces have different prompts, number of turns, and observability; counts do not estimate a causal surface effect. Repeated seeds remain separate sessions because replies and session IDs differ. Aggregate exports and split files are duplicate representations, not extra units. Some episode seeds or antecedents may have been replayed or supplied externally.

Only labeled original utterances support codes. Deployment summaries locate context but do not substitute for missing original turns. Host-private records contain two quoted character replies each; host words are summarized, so full dyadic exchange structure is unassessable. A group prompt followed by four individual answers is not coded as four peer responses.

## Code values

- **O:** the defined feature is observed in the supplied quoted text.
- **N:** the feature is not observed in that text; this is not absence from the deployment or proof of incapacity.
- **U:** required evidence is unavailable or incomplete; never numerically treated as N.
- **NA:** the indicator does not apply to this surface.

## Indicators

**Contingent peer response.** O requires a quoted utterance substantively accepting, challenging, or modifying another character's quoted contribution in the same episode. Merely answering the host's topic, repeating an earlier episode, or using a shared theme does not qualify. Group rounds are N because no such within-round response is displayed; all nine peer-private sessions are O. Host-private exchanges are U because the host side is not quoted. This detects responsiveness, not novelty, sincerity, successful delivery, or independent generation.

**Prospective pledge or norm.** O requires a speaker to undertake or explicitly renew an identifiable future action, restraint, conditional response, or inclusive interpersonal norm. Includes conditional warnings and audience restrictions. Mutual ratification is not required: this indicator counts a statement, not a contract, new intention, new norm, or fulfillment. Exclude general advice, a hypothetical preference, a request addressed only to another person, and merely reporting a past promise. F06 explicitly renews a gaze pledge; F04 reports an earlier pact but does not explicitly renew it. F08's future voting norm and F11's conditional monitoring warning count under this deliberately broad rule. F19's group-disclosure restriction counts even though most of its text is reflection. F09 requests conduct without a quoted future promise; F21 offers hypothetical advice without explicitly undertaking it. Each O has a literal anchor, line locator, and rationale in the CSV. This rule yields 1/6 group, 8/9 peer-private, and 4/5 host-private episodes; it must not be described as 13 new commitments or 13 independent obligations.

**Multi-turn peer exchange.** O requires at least four alternating quoted character turns in one peer-private session, with contingent response present. The four O episodes are F10, F14, F15, and F16 (6, 4, 6, and 6 turns). This is a structural descriptor, not proof of substantive negotiation on every turn. Group N means the displayed structure is four individual answers, not an extended exchange. Host U reflects missing original host turns. The CSV turn count includes private seeds, excludes group prompts and non-transcript headings, and counts only the two surviving target replies in each host record.

**Matched earlier seed.** O means the complete quoted first peer-private utterance exactly matches a seed in an earlier supplied record: F10/F08, F11/F09, F13/the 3 October peach source, F14/F12. N for the other five peer-private episodes means no such match in the inspected comparison set; it does not establish a fresh autonomous intention. NA for group and host-private surfaces. Four O rows are later instances in four matched sets, not eight independent repeated-intent events. The comparator for F13 is outside this 20-episode denominator.

**Fresh autonomous initiation.** U for all nine peer-private sessions: no complete intention-to-dispatch trace was supplied. A host summary attributes F16 to a self-check, but this does not independently authenticate fresh initiation. NA for the assigned group-round and host-private surfaces. Do not convert U into a zero initiation rate; skipped self-checks and failed sends are not in the denominator.

## Themes and outcomes

Every row also supplies a thematic memo and an outcome memo. We deliberately do not derive a numeric thematic-novelty rate: the archive lacks a comparable baseline and a validated semantic threshold. This is a limitation of the new coding, not something the counts solve. Different objects or preferences can add specificity; local norms can develop within an existing theme. Recurrence does not make every utterance redundant.

Commitment outcomes are examined in [followup-commitment-traces.md](followup-commitment-traces.md). Distinguish a present acknowledgment, a stated future pledge, a later reference or revision, a performed and evaluated conversational act, and an unobserved future outcome. A new agreement is itself a local social event, but does not prove the future obligation was fulfilled. Verbal action counts: F15 performs and evaluates a compliment in the same exchange; F07-to-F15 revises preferences across episodes. Neither can be erased by calling all activity repetitive. Likewise, F18's quoted response is consistent with the call-and-answer pact, even though the host cue and restart are summary-level evidence.

No fulfillment percentage is computed: commitments can overlap, opportunities differ, the export is right-censored, and antecedents are sometimes unresolved. An unobserved outcome is not a violated promise. The F17/F18-to-F04 audience restriction is a visible content-constraint inconsistency; missing contexts and unobserved permissions prevent diagnosing an execution-level privacy failure.

## Interpretation

The countable contrast is between individual-answer group rounds and responsive private exchanges, many of which articulate future conduct. Counts strengthen evidence for local interaction while leaving its sustained consequences uncertain. They do not quantitatively establish stagnation, a creativity decline, model-specific causes, or a causal link from the September prequel to October interaction. An independent human recoding, ideally with a predeclared codebook, remains needed to assess reliability.
