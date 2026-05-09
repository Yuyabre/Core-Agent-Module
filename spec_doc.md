# Yuyabre — Core Agent Module Spec (v0.1 Draft)

**Module path:** `backend/agent/`
**Language:** Python 3.11+
**Primary dependency:** OpenAI Async SDK, FastAPI (caller), Beanie ODM (DB access)

***

## Overview

The Core Agent Module is the AI brain of Yuyabre. It receives natural language commands from the backend API, drives a multi-turn LLM loop with tool use, executes domain actions (inventory, ordering, expenses, messaging), and streams results back to callers. Everything else in the system (backend, frontend) is a consumer of this module. 

***

## Module Structure

```
backend/agent/
├── __init__.py         # Exports GroceryAgent
├── core.py             # Top-level orchestrator (GroceryAgent class)
├── conversation.py     # Multi-turn LLM loop + streaming
├── toolhandlers.py     # Concrete tool implementations
├── tools.py            # OpenAI-format JSON tool schemas
├── context.py          # System prompt builder (user-aware)
└── prompts.py          # Base SYSTEM_PROMPT constant
```

***

## Components

### 1. `prompts.py` — Base System Prompt

The simplest file. Defines a single `SYSTEM_PROMPT` string constant.

**Requirements:**
- Persona: Yuyabre is a gen-Z friendly, emoji-moderate assistant for shared flats 
- Instruct the LLM to always call `get_inventory_snapshot` before making ordering decisions 
- Instruct the LLM to call `update_user_preferences` when a user mentions dietary info mid-conversation 
- Instruct the LLM to explain group-order behaviour when `place_order` returns `is_group_order: true` 
- Instruct the LLM never to expose raw JSON or tool mechanics to the user 

***

### 2. `context.py` — Dynamic Prompt Builder

Builds a personalised system prompt per user before each conversation turn.

**Inputs:** `user_id: Optional[str]`
**Output:** `str` (enhanced system prompt)

**Requirements:**
- Fetch `User` document from MongoDB by `user_id` 
- If no user found, return the base `SYSTEM_PROMPT` unmodified
- Append a `User Context` block to the prompt containing:
  - Name, user ID, email, phone
  - Household ID
  - Splitwise connection status (has OAuth tokens or not)
  - Discord user ID (if set)
  - Dietary restrictions, allergies, favourite brands, disliked items
  - Account status and join date
- If preferences exist, append a preference-enforcement instruction (never suggest allergenic items, prefer liked brands) 

***

### 3. `tools.py` — Tool Schema Definitions

Defines the OpenAI function-calling JSON schemas for every tool the LLM can invoke.

**Requirements:**
- Single exported function `build_tool_specs() -> List[Dict]` 
- Each tool entry must conform to the OpenAI `type: "function"` schema with `name`, `description`, and `parameters`
- Tools to define (16 total):

| Tool | Description |
|---|---|
| `get_inventory_snapshot` | Fetch current stock; optional `dish` or `search` filter |
| `add_inventory_items` | Add/increment items; accepts list with `name`, `quantity`, `unit`, `category`, `shared` |
| `update_inventory_item` | Edit a single item's quantity, threshold, unit, category, notes |
| `check_low_stock` | Return items below their threshold |
| `place_order` | Create grocery order; triggers group order if shared items detected |
| `get_recent_orders` | Fetch order history with optional `limit` |
| `get_order_eta` | Get ETA for a specific order by `order_id` |
| `get_group_order_status` | Check housemate yes/no responses for a pending group order |
| `create_splitwise_expense` | Log a cost split to Splitwise with amount, description, participants |
| `get_splitwise_expenses` | Retrieve recent shared expenses |
| `get_user_info` | Fetch current user's full profile |
| `update_user_preferences` | Add/remove dietary restrictions, allergies, brands, dislikes |
| `get_housemates` | List household members; optional contact info flag |
| `send_discord_message` | Send message to household Discord channel (preferred channel) |
| `check_discord_message_responses` | Poll for housemate responses by `context_id` |
| `send_whatsapp_message` | Fallback: send via Twilio WhatsApp to household or specific number |

- Tool descriptions must guide LLM decision-making (e.g., "Always prefer `send_discord_message` first, only use WhatsApp as fallback") 

***

### 4. `conversation.py` — Multi-Turn LLM Loop

The `ConversationManager` class that drives the OpenAI chat completion loop.

**Constructor args:** `openai_client`, `tool_specs`, `execute_tool`

#### `run_conversation(messages, user_id) -> str`
Blocking version for non-streaming callers.

**Requirements:**
- Loop: call `chat.completions.create` with `tool_choice="auto"` 
- If response contains `tool_calls`: execute each tool, append results to `messages`, continue loop 
- If response has text content: return it
- If content is empty and no tools called: return a safe fallback string 

#### `run_conversation_stream(messages, user_id) -> AsyncGenerator[str]`
Streaming version for WebSocket callers.

**Requirements:**
- Use `stream=True` on the OpenAI call 
- Accumulate streamed content chunks and yield them immediately to the caller
- Accumulate tool call deltas by index into a `tool_calls_dict` (tool calls arrive in fragments over stream) 
- After stream ends: if tool calls were collected, emit `Executing <tool_name>...` status strings, execute tools, append results, and loop again 
- Cap loop at **10 iterations** to prevent infinite tool-call cycles 
- On completion: store full assistant response in `messages` and return 

***

### 5. `toolhandlers.py` — Tool Implementations

The `ToolHandlers` class wiring tool names to real async service calls.

**Constructor args:** `inventory_service`, `ordering_service`, `splitwise_service`, `whatsapp_service`, `discord_service`, `update_system_prompt_callback`

**General pattern for each handler:**
```
async def <tool_name>(self, *, userid=None, **kwargs) -> Dict[str, Any]
```

**Key implementation requirements:**

- **`get_inventory_snapshot`** — query `InventoryService`; filter by `dish` or `search` keyword; return item list with quantity, unit, category, threshold, shared flag 
- **`add_inventory_items`** — for each item, determine `shared` (default: True if user is in a household); call `InventoryService.add_or_increment_item`; return created/updated status per item 
- **`place_order`** — search store catalogue for each item, match product, build `OrderItem` list; call `OrderingService.create_order`; if any items are `shared`, trigger group order flow (send Discord/WhatsApp message, return `is_group_order: true`) 
- **`update_user_preferences`** — support additive and subtractive updates (separate `add_*` and `remove_*` lists); normalise allergy names (e.g., "lactose intolerant" → "lactose"); save to `User` document; call `update_system_prompt_callback` so the running conversation immediately reflects changes 
- **`create_splitwise_expense`** — verify user has Splitwise OAuth tokens; if `splitwise_user_id` is missing from DB, fetch it from the Splitwise API and persist it; resolve group members; post expense 
- **`send_discord_message`** — verify household has `discord_channel_id`; call `DiscordService.send_to_household`; return `message_id` and `context_id` for later response polling 
- **`check_discord_message_responses`** — poll `DiscordService` by `context_id`; return structured yes/no response map per housemate 
- **`send_whatsapp_message`** — only used as fallback; send to whole household or a specific phone number 

***

### 6. `core.py` — GroceryAgent Orchestrator

The top-level class consumed by the backend API controller.

**Constructor:** instantiates all service modules, `ToolHandlers`, `ConversationManager`; registers tool name → handler mapping.

**Conversation storage:** `self.conversations: Dict[str, List[Dict]]` keyed by `session_id` (defaults to `user_id` or `"anonymous"`) 

**History trimming:** if conversation exceeds 20 messages, keep system prompt + last 18 messages (9 exchanges) 

#### `process_command(command, user_id) -> str`
**Steps:**
1. Build personalised system prompt via `context.py`
2. Get or initialise conversation for `session_id`
3. Update `messages[0]` if system prompt changed (e.g., preferences updated)
4. Deep-copy `messages`, append user command, pass to `ConversationManager.run_conversation`
5. Persist user + assistant messages to conversation history
6. Trim if over limit; return response text 

#### `process_command_stream(command, user_id) -> AsyncGenerator[str]`
Same flow as above but delegates to `run_conversation_stream`; persists full response after streaming ends 

#### `add_message_to_conversation(user_id, message, role)`
Used by WhatsApp/Discord webhooks to inject external messages into the agent's context without triggering an LLM call 

#### `update_system_prompt_for_user(user_id)`
Callback passed to `ToolHandlers`; rebuilds and hot-swaps `messages[0]` mid-conversation when preferences are updated 

***

## Data Flow

```
User command (REST or WebSocket)
        │
        ▼
 GroceryAgent.process_command[_stream]
        │
        ▼
 context.py → builds personalised system prompt
        │
        ▼
 ConversationManager.run_conversation[_stream]
        │
   ┌────┴─────────────────────┐
   │  OpenAI chat completion   │
   │  (with tool_choice=auto)  │
   └────┬─────────────────────┘
        │ tool_calls?
        ▼
 GroceryAgent.execute_tool
        │
        ▼
 ToolHandlers.<tool_name>
        │
  InventoryService / OrderingService /
  SplitwiseService / DiscordService / WhatsAppService
        │
        ▼
 Tool result appended → loop back to LLM
        │
  Final text content
        │
        ▼
 Streamed tokens or full string returned to API
```

***

## Error Handling

- Each tool handler must return `{"error": "<message>"}` on failure — never raise exceptions to the LLM loop 
- `execute_tool` catches all unhandled exceptions from handlers and returns an error dict 
- `ConversationManager` catches LLM API errors; `GroceryAgent` catches conversation errors and returns a safe fallback message 
- Unknown tool names return `{"error": "Tool <name> is not implemented"}` 

***

## Configuration

All configuration comes from `config.py` / `.env`:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | LLM authentication |
| `OPENAI_MODEL` | Model to use (e.g., `gpt-4o`) |
| `OPENAI_PROXY_URL` | Optional custom base URL |
| `AGENT_DEBUG` | Verbose planning logs |

***

## Testing Plan

| Test | Type | What to verify |
|---|---|---|
| `test_process_command` | Unit | Agent returns a string; conversation history grows correctly |
| `test_history_trimming` | Unit | History capped at 20 messages |
| `test_tool_dispatch` | Unit | Correct handler invoked per tool name; unknown tool returns error dict |
| `test_preference_update` | Unit | `update_user_preferences` normalises allergy strings, saves to DB, fires callback |
| `test_system_prompt_rebuild` | Unit | `update_system_prompt_for_user` hot-swaps `messages[0]` |
| `test_stream_tool_accumulation` | Unit | Streamed tool call deltas correctly assembled before execution |
| `test_place_order_group_flow` | Integration | Shared items trigger Discord message + `is_group_order: true` |
| `test_full_conversation` | E2E | "We're out of oat milk" → inventory check → order → expense logged |