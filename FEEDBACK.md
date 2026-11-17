# Client review: Larkspur disruption-care agent

**To:** Room 16  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-17 11:23

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. agent.py tool_list() returns mcp_client.tools(), so EXTRA_TOOLS and build_tools() are never sent to Claude.**

The diff comments out `return build_tools() + EXTRA_TOOLS` and returns `mcp_client.tools()` instead. Your seats_left and care_entitlements schemas sit in EXTRA_TOOLS, and LOCAL_TOOLS holds their executors. tool_results() only reaches LOCAL_TOOLS for names Claude was offered, and tool_list() no longer lists them. The 278 and 599 character descriptions you wrote may never reach the model.

Run python3 run.py --show-tools and paste the list, so the names Claude is actually offered can be read against your two local tools.

**2. readout-trace.json shows 1 API turn and 0 tool calls, so the committed run exercised none of your tools.**

The last committed wire run records "tools called, in order: none" at 1666 tokens in and 470 out, with 0 cache read and 0 written. A disruption agent that answers without calling lookup_booking or get_flight_status has produced nothing to compare against. This is the only wire run in the repository, and it says nothing about seats_left, care_entitlements or the search_alternatives rewrite.

Run python3 run.py --all --trace and paste the totals footer with the per-booking tool lists.

**3. PITCH.md Number line gives 70,537 to 92,401 input tokens, and no bench output or file in the repository produces it.**

The range is unlabeled: no before, no after, no runs count, no stage. readout-trace.json holds 1666 input tokens for its one run, and agent.py has no cache_control anywhere. Without a labelled before and after, the 70,537 to 92,401 spread could be the lever working or run-to-run variance.

Run python3 bench.py --label before --stage 1 --runs 3, repeat with --label after, then paste the output of python3 bench.py --compare before after.

**4. PITCH.md says two MCP tools and a Handbook lookup, but fare_rules and next_available_day are commented out in agent.py.**

The EXTRA_TOOLS entries for next_available_day and fare_rules and their LOCAL_TOOLS lines are all prefixed with # in your diff. The fare_rules description also still reads "why he do not get a hotel" and has a broken sentence about the policy table. PITCH.md's Built line claims fare_rules retrieves Handbook text. Only seats_left and care_entitlements are live in the dicts.

Run python3 run.py --show-tools and paste the output, marking which of next_available_day and fare_rules appear.

**5. There is no evals/cases.json, and your Still broken line, multi-passenger seats, has no case that reproduces it.**

PITCH.md says the agent can suggest a date with an open seat for only one person, and the only trace is a single zero-tool run. The banked gates stop at 2.2, so verify.py 3.1 and 4.1 have no banked result. Nothing in the repository shows the multi-passenger failure happening or shows a fix landing. No model choice changes that, because the missing piece is a case that fails.

Add a multi-passenger booking to evals/cases.json, run python3 eval_harness.py, and paste the result for that case.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (329 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
