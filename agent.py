"""Larkspur disruption agent. This is the file you build.
 
It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:
 
    python3 run.py K7PQ2M --trace
 
Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
from pyexpat.errors import messages
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, seats_left, care_entitlements, fare_rules, record_tool_result,
                     runtime_preamble)
 
MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.
 
TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
EXTRA_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "seats_left",
        "description": (
            "Use this tool when the customer asks how many seats remain in Main or First "
            "on the flight in their booking. Pass the booking's PNR; the tool looks up the "
            "flight and returns the seats_left_Y and seats_left_J counts from flights.csv. "
            "Do not use it to search for alternate flights."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_code": {
                    "type": "string",
                    "description": "The customer's PNR from this conversation.",
                },
            },
            "required": ["booking_code"],
        },
    },
    # {
    #     "name": "next_available_day",
    #     "description": (
    #         "Use when a customer asks for the soonest day they can travel on a route. "
    #         "After looking up the booking, provide the disrupted segment's origin, "
    #         "destination, date, and cabin; date must be YYYY-MM-DD and cabin is Y (main) "
    #         "or J (first). Returns the earliest date on or after that date with an open "
    #         "seat for one passenger, or says no open seat was found in the schedule."
    #     ),
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "origin": {"type": "string", "description": "Three-letter origin airport code."},
    #             "dest": {"type": "string", "description": "Three-letter destination airport code."},
    #             "date": {"type": "string", "description": "Start searching on this date, YYYY-MM-DD."},
    #             "cabin": {
    #                 "type": "string",
    #                 "enum": ["Y", "J"],
    #                 "description": "Cabin to search: Y for main or J for first.",
    #             },
    #         },
    #         "required": ["origin", "dest", "date"],
    #     },
    # },
    {
        "name": "care_entitlements",
        "description": (
            "Answer 'do I get a meal, a hotel or ground transport while I wait?' for this "
            "booking's disrupted flight, from Larkspur's disruption policy (care while you "
            "wait). Use it when the customer asks about food, a hotel, a taxi or where to stay, "
            "or when a flight is cancelled, diverted or delayed 2 hours or more. Call "
            "get_flight_status first: cause_code, delay_minutes and status must come from it, "
            "never from what the customer says. Overnight, fare and loyalty tier are looked up "
            "from the booking. Returns meal, hotel and ground amounts with any conditions, and "
            "the policy_row_id to pass to issue_voucher."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pnr": {"type": "string", "description": "The booking's confirmation code."},
                "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                               "description": "The delay cause as get_flight_status reported it."},
                "delay_minutes": {"type": "integer",
                                  "description": "Delay from get_flight_status. 0 if cancelled or diverted."},
                "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                "wait_minutes_for_alternative": {
                    "type": "integer",
                    "description": "Only for cancelled or diverted flights, once the customer has "
                                   "chosen an alternative: minutes until it departs. Leave out otherwise.",
                },
            },
            "required": ["pnr", "cause_code", "delay_minutes", "status"],
        },
    },
    # {
    #     "name": "fare_rules",
    #     "description": (
    #         "Use when a customer asks why he do not get a hotel"
    #         "Read the published Larkspur Customer Commitment and fare rules excerpt for a"
    #         "specific handbook section. Use this when the customer asks what the rule says, "
    #         "wants a citation, or challenges an entitlement decision. Pass either a section "
    #         "wait' or 'fare families'. Returns the full text of that handbook section. It is"
    #         "policy table for the actual entitlement decision."
    #     ),
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "section": {"type": "string", "description": "Which handbook section to read: a number like '6' or words from the title such as 'fare families', 'when we delay', 'care while you wait', or 'chat automation'."},
    #             },
    #         "required": ["section"],
    #     },
    # },
]   # ✏️ Build 2, step 2.1: schemas for the tools you add
LOCAL_TOOLS: Dict[str, Any] = {
    "seats_left": seats_left,
    # "next_available_day": next_available_day,
    "care_entitlements": care_entitlements,
    # "fare_rules": fare_rules,
}         # ✏️ Build 2, step 2.1: the functions behind them
 
 
def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""
 
 
def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results
 
 
def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        {"role": "user", "content": f"PNR {pnr}, last name {last_name}. {message}"},
    ]
 
    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )
 
    answer = ""
    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )
        turns += 1
 
    return text_of(response)
 
 
def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    # return 
    return mcp_client.tools() + build_tools() + EXTRA_TOOLS
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string"},
                    "date": {"type": "string", "description": "The flight's local travel date, in ISO format YYYY-MM-DD (for example 2025-05-08)."},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": (
                "Find other Larkspur flights to rebook onto, for the segment that was "
                "disrupted on this booking. Looks up the disrupted segment itself, so pass "
                "only the pnr; do not guess an origin, destination, date, or cabin. Returns "
                "a ranked list of alternative flight options, each with an option_id to pass "
                "to hold_seat."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}},
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]