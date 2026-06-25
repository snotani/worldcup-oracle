# 01 · Problem / use case

**Goal:** make the audience care, and frame it as a real, gradable problem.

## The problem
Everyone predicts football — pundits, your group chat, the bookies. Can a transparent AI agent,
using only pre-match info, do it as well as simple baselines? And can we *prove* it?

## Why it's a good agent problem (talking points)
- Clear input (match facts) and output (probabilities) → a clean contract.
- A ground truth arrives every match → real, quantitative evals.
- Naturally modular → one agent, three content angles.

## The constraints we set (say these)
- Honest: no information from after kickoff.
- Calibrated: it must output probabilities, not vibes.
- Explainable: every step observable.

## On-camera
- Read the top of [`spec/AGENT_SPEC.md`](../spec/AGENT_SPEC.md) section 1.
- Whiteboard / overlay: "input → agent → probabilities → compare to reality."

## What to show next
The spec — `02-spec.md`.
