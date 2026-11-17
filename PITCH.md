# PITCH.md
 
Six lines and a lever. Your words. The last two are scored.
 
Built: A Larkspur disruption-care agent with two MCP tools: `next_available_day` finds the earliest date with an open seat for one passenger, and `fare_rules` retrieves Handbook textand locally implemented `seats_left` and `care_entitlements` functions.
Does: It verifies the booking and disruption, checks what the customer is entitled to, finds rebooking options and can hold a seat, then explains next steps; cases outside scope go to a human.
Number: 19,406 to 19,430 input tokens per contact, measured over 15 runs each (5 Stage 1 ticket types x 3); 15/15 contacts returned text both times.
Safety check: It never finalizes a rebooking on chat consent alone; the customer's Confirm-click must provide the required token.
Next: Have the agent answer in the language recorded on the booking, so customers can handle a disruption in their own language.
Still broken: When a booking has multiple passengers, the agent can suggest a travel date with an open seat for only one person, leaving the rest of the party without seats.
Lever: cost 
 
## Priya asked
 
Costs:
Wrong:
Runs it:
Left out: