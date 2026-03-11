# Architecture — B2B Banking Chatbot

10 diagrams documenting the system design of a production-grade banking chatbot powered by Claude Sonnet 4.6 with native `tool_use`.

## Table of Contents

1. [Engine Overview](#1-engine-overview)
2. [The Main Loop — One Turn](#2-the-main-loop--one-turn)
3. [Claude Decision Space](#3-claude-decision-space)
4. [Memory System — 5 Stores](#4-memory-system--5-stores)
5. [Context Window Assembly](#5-context-window-assembly)
6. [FAQ Engine — Three Confidence Tiers](#6-faq-engine--three-confidence-tiers)
7. [Tool Executor + Workflow Engine](#7-tool-executor--workflow-engine)
8. [Dialogue State Machine — 11 States](#8-dialogue-state-machine--11-states)
9. [Guardrails — Safety Layers](#9-guardrails--safety-layers)
10. [Real Conversation — All Systems in Action](#10-real-conversation--all-systems-in-action)

---

## 1. Engine Overview

High-level data flow from user message to bot response.

```
┌──────────────────┐     ┌─────────────────────────────────────────────────────────┐
│                  │     │                  CONVERSATION ENGINE                     │
│   React + Vite   │     │                                                         │
│    Frontend      │────▶│  ┌───────────┐   ┌─────────────┐   ┌────────────────┐  │
│                  │     │  │ Auth Gate  │──▶│   Context    │──▶│ Claude Sonnet  │  │
│  POST /api/chat  │     │  │           │   │   Builder    │   │    4.6         │  │
│                  │     │  │ phone/acct │   │ (5 stores)   │   │  + 20 tools    │  │
└──────────────────┘     │  └─────┬─────┘   └─────────────┘   └───────┬────────┘  │
                         │    fail 3x                                  │           │
                         │        │                              ┌─────▼────────┐  │
                         │        ▼                              │  Tool Loop   │  │
                         │  ┌───────────┐   ┌─────────────┐     │  (agentic)   │  │
                         │  │  Human    │   │ Guardrails  │◀────│              │  │
                         │  │ Transfer  │   │ G1: halluci │     │ execute tool │  │
                         │  └───────────┘   │ G5: emotion │     │ → fact store │  │
                         │                  └──────┬──────┘     │ → loop back  │  │
                         │                         │            └──────────────┘  │
                         │                         ▼                              │
                         │                  ┌─────────────┐                       │
                         │                  │  Response    │──────────────────────▶│
                         │                  └─────────────┘                       │
                         └─────────────────────────────────────────────────────────┘
```

**Design rationale**: Single-pass architecture replaces the old Llama 8B two-pass design (Pass 1: Resolve+Decide → structured JSON → Pass 2: Naturalize). Claude natively handles intent resolution, tool selection, and natural language response in one API call via `tool_use`, eliminating the structured JSON action routing layer entirely.

**Key files**: `chatbot/engine/conversation.py`, `chatbot/main.py`, `chatbot/api/routes.py`

---

## 2. The Main Loop — One Turn

The `process_turn()` method in `chatbot/engine/conversation.py` executes 9 steps per user message.

```
  User Message
       │
       ▼
  ┌─────────────────────────────────┐
  │ 1. STATE CHECK                  │   Is user authenticated?
  │    Auth gate / human transfer   │   If not → handle auth flow
  └──────────────┬──────────────────┘
                 │ (authenticated)
                 ▼
  ┌─────────────────────────────────┐
  │ 2. APPEND to turn store         │   Store user message
  │ 3. SCORE EMOTION (heuristic)    │   Caps, exclamations, negative words
  │ 4. CHECK ESCALATION             │   3+ turns rising anger ≥ 0.7?
  └──────────────┬──────────────────┘
                 ▼
  ┌─────────────────────────────────┐
  │ 5. BUILD SYSTEM PROMPT          │   Identity + rules + 5 memory stores
  │    + escalation instruction     │   + active workflow instruction
  │    + workflow instruction       │
  └──────────────┬──────────────────┘
                 ▼
  ┌─────────────────────────────────┐
  │ 6. CLAUDE TOOL LOOP             │   while stop_reason == "tool_use":
  │    messages + 20 tool defs      │     execute tools
  │                                 │     write to fact store
  │    ┌─────────────────────────┐  │     append results
  │    │ Claude ──tool_use──▶    │  │     call Claude again
  │    │ Tool ──result──▶ Claude │  │
  │    └─────────────────────────┘  │
  └──────────────┬──────────────────┘
                 ▼
  ┌─────────────────────────────────┐
  │ 7. GUARDRAILS                   │   G1: scan for ungrounded financial data
  │    hallucination blocker        │   If unsafe → re-prompt with stricter rules
  └──────────────┬──────────────────┘
                 ▼
  ┌─────────────────────────────────┐
  │ 8. UPDATE STORES                │   Sync turn store with full tool history
  │    Track threads + workflows    │   Create/resume conversation threads
  └──────────────┬──────────────────┘
                 ▼
  ┌─────────────────────────────────┐
  │ 9. STATE TRANSITIONS            │   tool_called → LISTENING
  │    Detect farewell / escalation │   goodbye → FAREWELL
  └──────────────┬──────────────────┘
                 ▼
          TurnResult
   (response, state, emotion, tool_calls)
```

**Design rationale**: No filler responses needed. The old system streamed "Let me check that for you" while Llama processed. Claude's single-pass tool_use handles everything — intent resolution, action selection, AND natural language response — in one call. No structured JSON routing, no action_type dispatcher.

---

## 3. Claude Decision Space

Claude decides which tools to call based on the tool definitions in the system prompt. No explicit routing.

```
                    ┌──────────────────────────────┐
                    │     CLAUDE SONNET 4.6         │
                    │                              │
                    │  System prompt + Rules        │
                    │  + Customer context           │
                    │  + Verified facts             │
                    │  + Active threads             │
                    │  + Emotion state              │
                    │  + 20 Tool definitions        │
                    │                              │
                    │         ┌─────────┐          │
                    │         │ Decide  │          │
                    │         └────┬────┘          │
                    └──────────────┼───────────────┘
                                   │
          ┌────────────┬───────────┼───────────┬────────────┐
          ▼            ▼           ▼           ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
    │ talk     │ │ faq      │ │ tool   │ │ workflow │ │ escalate │
    │          │ │          │ │ call   │ │          │ │          │
    │ No tool  │ │ search_  │ │ Any of │ │ Triggers │ │initiate_ │
    │ called — │ │knowledge_│ │ the 19 │ │ multi-   │ │human_    │
    │ direct   │ │base      │ │ other  │ │ step     │ │transfer  │
    │ response │ │          │ │ tools  │ │ flow     │ │          │
    └──────────┘ └──────────┘ └────────┘ └──────────┘ └──────────┘
```

**What changed**: The old system used Llama Pass 1 to output structured JSON with an explicit `action_type` field (`faq | tool | workflow | talk | escalate`), then routed to separate engines. Now Claude makes this decision implicitly through native `tool_use` — if it calls `search_knowledge_base`, that's an FAQ lookup. If it calls `block_card`, that's a tool action. No routing layer needed.

**Key file**: `chatbot/tools/definitions.py` (20 tool schemas)

---

## 4. Memory System — 5 Stores

Five in-memory stores feed the context builder. Each has strict write rules.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           5 MEMORY STORES                           │
├──────────────┬──────────────┬──────────────┬───────────┬────────────┤
│              │              │              │           │            │
│  SESSION     │  FACT STORE  │  THREAD      │  EMOTION  │  TURN      │
│  STORE       │              │  STORE       │  STORE    │  STORE     │
│              │              │              │           │            │
│ Written:     │ Written:     │ Written:     │ Written:  │ Written:   │
│ once at      │ ONLY by tool │ when tools   │ every     │ every      │
│ auth verify  │ results      │ are called   │ user turn │ message    │
│              │ NEVER by LLM │ (auto topic  │           │            │
│ Contains:    │              │ tracking)    │ Contains: │ Contains:  │
│ • name       │ Contains:    │              │ • score   │ • role     │
│ • customer_id│ • key=value  │ Contains:    │   (0-1)   │ • content  │
│ • accounts[] │ • source_tool│ • topic      │ • label   │ • tool_use │
│ • cards[]    │ • turn_number│ • status     │ • rising? │ • tool_    │
│ • segment    │ • timestamp  │   (active/   │ • labels: │   result   │
│ • tenure     │ • versioned  │   suspended/ │   neutral │            │
│ • verified   │   (supersede)│   resolved)  │   →angry  │ Max: 100   │
│              │              │ • workflow_id│           │ turns      │
│              │              │ • slots      │ Window:   │            │
│              │              │              │ last 3    │            │
└──────────────┴──────────────┴──────────────┴───────────┴────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  CONTEXT BUILDER  │
                    │  → system prompt  │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  Claude Sonnet   │
                    │      4.6         │
                    └──────────────────┘
```

**Design rationale**: Strict write rules prevent data corruption:
- **Facts** only come from tool results (G3: Fact Integrity guarantee). Claude's text output never writes to the fact store. This ensures the hallucination blocker has a reliable ground truth to check against.
- **Sessions** are immutable after auth — no mid-conversation changes to customer identity.
- **Versioning** in fact store means corrections don't overwrite — old values are superseded, maintaining audit trail.

**Key files**: `chatbot/memory/session_store.py`, `chatbot/memory/fact_store.py`, `chatbot/memory/thread_store.py`, `chatbot/memory/emotion_store.py`, `chatbot/memory/turn_store.py`

---

## 5. Context Window Assembly

The system prompt is assembled from 6 sections, each tagged with XML for clear boundaries.

```
  ┌───────────────────────────────────────────────────────────┐
  │                    ASSEMBLED SYSTEM PROMPT                 │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 1: Identity + 10 Rules                      │  │
  │  │ "You are a customer service assistant for HSBC..."   │  │
  │  │ Rule 1: NEVER fabricate financial data               │  │
  │  │ Rule 2-4: FAQ confidence tier handling               │  │
  │  │ Rule 5: Lead with empathy                            │  │
  │  │ Rule 6-10: Behavior constraints                      │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 2: <customer_context>                       │  │
  │  │ Name: Jennifer Park                                 │  │
  │  │ Segment: preferred | Tenure: 5 years                │  │
  │  │ Accounts: checking_3301, savings_3301               │  │
  │  │ Cards: visa_3301, amex_3301                         │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 3: <verified_facts>                         │  │
  │  │ get_balance: {"balance": 4215.60, "currency": "USD"}│  │
  │  │ block_card: {"blocked": true, "ref": "BLK-9182"}   │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 4: <active_threads>                         │  │
  │  │ - [active] fraud_report (workflow step 2)           │  │
  │  │   — need: card_possession, last_authorized_use      │  │
  │  │ - [suspended] account_inquiry                       │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 5: <emotion_state>                          │  │
  │  │ Turn 1: neutral (0.1) → Turn 2: concerned (0.4)    │  │
  │  │ → Turn 3: stressed (0.6)                            │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 6: <active_workflow>  (conditional)         │  │
  │  │ You are in the "Fraud Report" workflow, step 2/4.   │  │
  │  │ You need to collect: card_possession, last_auth_use │  │
  │  │ Already collected: card_id=visa_3301                │  │
  │  └─────────────────────────────────────────────────────┘  │
  │                                                           │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │ SECTION 7: <escalation_instruction>  (conditional)  │  │
  │  │ Customer emotion is escalating. Proactively offer   │  │
  │  │ to transfer to a human agent.                       │  │
  │  └─────────────────────────────────────────────────────┘  │
  └───────────────────────────────────────────────────────────┘
```

**What changed**: The old system had a ~2,500 token budget with 7 layers carefully sized (system prompt ~500tok, session ~100tok, facts ~150tok, threads ~100tok, emotion ~50tok, turns ~1,200tok, utterance ~50tok). With Claude's much larger context window, we no longer need aggressive token budgeting. XML tags provide clear section boundaries for Claude to parse.

**Key file**: `chatbot/engine/context_builder.py`

---

## 6. FAQ Engine — Three Confidence Tiers

The `search_knowledge_base` tool queries a ChromaDB vector store with OpenAI embeddings, returning results with confidence scores that determine Claude's response style.

```
  User asks: "What documents do I need for a credit card?"
       │
       ▼
  ┌────────────────────────────┐
  │ Claude calls tool:         │
  │ search_knowledge_base      │
  │   query: "credit card      │
  │          required docs"    │
  └────────────┬───────────────┘
               ▼
  ┌────────────────────────────┐
  │ OpenAI Embed               │
  │ text-embedding-3-small     │
  │ → query vector             │
  └────────────┬───────────────┘
               ▼
  ┌────────────────────────────┐
  │ ChromaDB Cosine Search     │
  │ banking_faq.json corpus    │
  │ → top match + score        │
  └────────────┬───────────────┘
               │
       ┌───────┼───────────┐
       ▼       ▼           ▼

   HIGH        MEDIUM       LOW
   > 0.85      0.6–0.85     < 0.6

  ┌────────┐  ┌──────────┐  ┌────────────┐
  │ PURE   │  │ HEDGED   │  │ LLM +      │
  │ FAQ    │  │ BLEND    │  │ DISCLAIMER  │
  │        │  │          │  │            │
  │Present │  │"Typicall │  │ General    │
  │answer  │  │y", "in   │  │ knowledge  │
  │directly│  │most case │  │ + "please  │
  │        │  │s"        │  │ verify     │
  │        │  │          │  │ with a     │
  │        │  │NEVER say │  │ specialist"│
  │        │  │"always", │  │            │
  │        │  │"definite │  │            │
  │        │  │ly"       │  │            │
  └────────┘  └──────────┘  └────────────┘
```

**Design rationale**: Same three-tier concept as the old system, but now `search_knowledge_base` is a Claude tool rather than a separate routing target. Claude calls it when it judges a user question is about bank policy. The confidence score is returned in the tool result, and system prompt rules (2-4) tell Claude how to frame the answer based on the tier.

**Key files**: `chatbot/tools/knowledge_base_tool.py`, `chatbot/knowledge/vector_store.py`, `data/knowledge_base/banking_faq.json`

---

## 7. Tool Executor + Workflow Engine

### 7a. Tool Execution via Native tool_use

```
  ┌──────────────────────────────────────────────────────────────┐
  │                     TOOL EXECUTION FLOW                       │
  │                                                              │
  │   Claude                    ToolHandlerRegistry              │
  │     │                            │                           │
  │     │──tool_use: block_card──────▶│                           │
  │     │  {card_id: "visa_3301",    │                           │
  │     │   reason: "fraud"}         │──access check──▶ session  │
  │     │                            │                 store     │
  │     │                            │◀──card owned?───          │
  │     │                            │                           │
  │     │                            │──▶ MockCardService        │
  │     │                            │     .block_card()         │
  │     │                            │◀── {blocked: true,        │
  │     │                            │     ref: "BLK-9182"}      │
  │     │                            │                           │
  │     │◀──tool_result──────────────│                           │
  │     │  {blocked: true, ...}      │                           │
  │     │                     ┌──────┴──────┐                    │
  │     │                     │ Fact Store  │                    │
  │     │                     │ write(...)  │                    │
  │     │                     └─────────────┘                    │
  └──────────────────────────────────────────────────────────────┘
```

### 7b. Service Adapter Pattern

```
  ┌─────────────────────┐     ┌─────────────────────┐
  │  Protocol (abstract) │     │  Mock Implementation │
  │                     │     │                     │
  │  AccountService     │◀────│  MockAccountService  │
  │  CardService        │     │  MockCardService     │
  │  LoanService        │     │  MockLoanService     │
  │  TransferService    │     │  MockTransferService  │
  │  DocumentService    │     │  MockDocumentService  │
  │  ComplaintService   │     │  MockComplaintService  │
  └─────────────────────┘     └─────────────────────┘
           ▲
           │  (production: swap in real API clients)
  ┌─────────────────────┐
  │  BankXYZAccountSvc  │
  │  BankXYZCardSvc     │
  │  ...                │
  └─────────────────────┘
```

### 7c. Workflow Engine

Multi-step flows with slot filling, suspend/resume on topic switch.

```
  3 Workflow Definitions:
  ┌────────────────────────────────────────────────────────┐
  │ fraud_report:           4 steps                        │
  │   1. block_card (proactive)                            │
  │   2. collect dispute details (needs input)             │
  │   3. file_dispute (auto)                               │
  │   4. order_replacement_card (proactive)                │
  │                                                        │
  │ credit_card_application: 4 steps                       │
  │   1. confirm details (needs input)                     │
  │   2. collect income (needs input)                      │
  │   3. collect SSN last 4 (needs input)                  │
  │   4. submit application (auto)                         │
  │                                                        │
  │ international_transfer: 3 steps                        │
  │   1. collect recipient details (needs input)           │
  │   2. confirm summary (confirm)                         │
  │   3. execute transfer (auto)                           │
  └────────────────────────────────────────────────────────┘

  Workflow lifecycle:

  ┌─────────┐  tool matches   ┌─────────────┐  all slots   ┌───────────┐
  │LISTENING │──workflow def──▶│ WORKFLOW_    │──filled────▶│ next step │
  └─────────┘                 │ ACTIVE       │             └─────┬─────┘
                              └──────┬───────┘                   │
                                     │                     last step?
                              topic switch                       │
                                     │                    ┌──────▼──────┐
                              ┌──────▼───────┐            │ WORKFLOW    │
                              │ WORKFLOW_    │            │ COMPLETE    │
                              │ SUSPENDED   │            │ → LISTENING │
                              └──────┬───────┘            └─────────────┘
                                     │
                              user returns
                                     │
                              ┌──────▼───────┐
                              │ WORKFLOW_    │
                              │ ACTIVE      │
                              │ (resumed)   │
                              └─────────────┘
```

**Key files**: `chatbot/tools/handlers.py`, `chatbot/tools/definitions.py`, `chatbot/services/protocols.py`, `chatbot/workflows/engine.py`, `chatbot/workflows/definitions/`

---

## 8. Dialogue State Machine — 11 States

Flat state machine with deterministic transitions. Auth is a precondition, not a tool call.

```
                              ┌──────────┐
                              │ GREETING │
                              └────┬─────┘
                           user_message
                              ┌────▼──────────┐
                              │ AUTH_COLLECT   │◀──────────────┐
                              └────┬──────────┘               │
                         identifier_provided                failed
                              ┌────▼──────────┐               │
                              │ AUTH_VERIFY    │───────────────┘
                              └─┬──────────┬──┘
                          verified      locked (3x fail)
                              │            │
                      ┌───────▼──┐   ┌─────▼──────┐
                      │LISTENING │   │ AUTH_LOCKED │
                      └──┬───┬──┘   └─────┬───────┘
                         │   │          always
    ┌────────────────────┤   └────┐   ┌───▼──────────┐
    │                    │        │   │HUMAN_TRANSFER │
    │              tool_called    │   └───────────────┘
    │                    │   faq_called        ▲
    │              ┌─────▼────┐   │            │
    │              │  TOOL_   │   │        escalation
    │              │EXECUTING │   │            │
    │              └────┬─────┘   │      ┌─────┴────┐
    │                done         │      │WORKFLOW_ │
    │                 │    ┌──────▼───┐  │ ACTIVE   │◀──resumed──┐
    │                 │    │ FAQ_     │  └──┬───┬───┘            │
    │                 │    │SEARCHING │     │   │                │
    │                 │    └────┬─────┘     │  topic_switch      │
    │                 │      done  workflow_│   │                │
    │                 │        │    done    │   ▼                │
    │                 ▼        ▼     │  ┌──────────────┐        │
    │              ───▶ LISTENING ◀──┘  │ WORKFLOW_    │────────┘
    │                      │            │ SUSPENDED   │
    │                   goodbye         └─────────────┘
    │                      │
    │                ┌─────▼────┐
    │                │ FAREWELL │
    │                └──────────┘
    │
    └─▶ (any tool/faq/workflow flows return to LISTENING via "done")
```

**What changed**: The old system had complex nested superstates (Listening contained Clarifying, Ready; ToolAction contained Chaining, Executing; FAQLookup contained Searching, PureFAQ, BlendedFAQ, LLMFallback; WorkflowActive contained WaitUser, StepExec, Done). The new system uses 11 flat states. Claude handles clarification and chaining internally, so those sub-states aren't needed.

**Key files**: `chatbot/state/machine.py`, `chatbot/state/models.py`

---

## 9. Guardrails — Safety Layers

Four safety layers protect against hallucination, data corruption, misleading language, and emotional escalation.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                         GUARDRAILS                               │
 │                                                                  │
 │  ┌─────────────────────────────────────────────────────────────┐ │
 │  │ G1: HALLUCINATION BLOCKER  [runtime — post-response scan]  │ │
 │  │                                                             │ │
 │  │  Claude's response text                                     │ │
 │  │       │                                                     │ │
 │  │       ▼                                                     │ │
 │  │  Regex scan: $amounts, %rates, reference IDs                │ │
 │  │       │                                                     │ │
 │  │       ▼                                                     │ │
 │  │  Cross-reference with Fact Store                            │ │
 │  │       │                                                     │ │
 │  │   ┌───┴───┐                                                 │ │
 │  │   ▼       ▼                                                 │ │
 │  │ CLEAN   UNGROUNDED                                          │ │
 │  │   │       │                                                 │ │
 │  │   ▼       ▼                                                 │ │
 │  │ Deliver  Re-prompt Claude:                                  │ │
 │  │          "use ONLY data from tool results"                  │ │
 │  │          + list of ungrounded claims                        │ │
 │  └─────────────────────────────────────────────────────────────┘ │
 │                                                                  │
 │  ┌─────────────────────────────────────────────────────────────┐ │
 │  │ G3: FACT INTEGRITY  [architectural — enforced by code path] │ │
 │  │                                                             │ │
 │  │  Tool result ──write──▶ Fact Store                          │ │
 │  │  Claude text ────X────▶ Fact Store  (no code path exists)   │ │
 │  │                                                             │ │
 │  │  Guarantees: fact store is always ground truth               │ │
 │  └─────────────────────────────────────────────────────────────┘ │
 │                                                                  │
 │  ┌─────────────────────────────────────────────────────────────┐ │
 │  │ G4: HEDGE ENFORCER  [prompt-based — system prompt rules]    │ │
 │  │                                                             │ │
 │  │  FAQ confidence 0.6–0.85 → Claude MUST use:                 │ │
 │  │    "typically", "generally", "in most cases"                │ │
 │  │  Claude MUST NOT use:                                       │ │
 │  │    "definitely", "always", "guaranteed"                     │ │
 │  └─────────────────────────────────────────────────────────────┘ │
 │                                                                  │
 │  ┌─────────────────────────────────────────────────────────────┐ │
 │  │ G5: EMOTION ESCALATION  [runtime — pre-response check]     │ │
 │  │                                                             │ │
 │  │  Emotion readings over last 3 turns:                        │ │
 │  │    neutral (0.1) → concerned (0.4) → stressed (0.7)        │ │
 │  │                                                             │ │
 │  │  Trigger: rising trajectory AND current ≥ 0.7              │ │
 │  │  Action: inject <escalation_instruction> into system prompt │ │
 │  │          "Proactively offer to transfer to a human agent"   │ │
 │  │                                                             │ │
 │  │  Scoring heuristic (no LLM call):                           │ │
 │  │    caps_ratio + exclamation_density + negative_words        │ │
 │  │    + urgency_phrases → score 0.0–1.0                       │ │
 │  │                                                             │ │
 │  │  Labels: neutral → concerned → anxious → stressed           │ │
 │  │          → angry → furious                                  │ │
 │  └─────────────────────────────────────────────────────────────┘ │
 └──────────────────────────────────────────────────────────────────┘
```

**What changed**: The old system had 5 explicit guardrails including G2 (Tool Call Validator — schema check). With Claude's native `tool_use`, the Anthropic API handles tool call validation (function exists, params match schema), so G2 is no longer needed as a custom layer. G3 and G4 are now architectural and prompt-based respectively, not runtime checks.

**Key files**: `chatbot/guardrails/hallucination_blocker.py`, `chatbot/guardrails/emotion_escalation.py`, `chatbot/engine/context_builder.py` (rules 2-4)

---

## 10. Real Conversation — All Systems in Action

A multi-turn session showing Jennifer Park investigating fraud, checking balance, and switching topics.

```
  Customer       Engine            Claude              Tools            Memory
     │              │                │                   │                │
     │──"Hi"───────▶│                │                   │                │
     │              │──AUTH_COLLECT──▶│                   │                │
     │◀─"Welcome,   │                │                   │                │
     │  phone #?"───│                │                   │                │
     │              │                │                   │                │
     │──"646-555-   │                │                   │                │
     │   0921"─────▶│                │                   │                │
     │              │──verify───────▶│                   │                │
     │              │                │                   │──auth_svc────▶│
     │              │                │                   │◀─Jennifer     │
     │              │                │                   │  Park,        │
     │              │                │                   │  visa_3301,   │
     │              │                │                   │  checking─────│
     │◀─"Hi         │                │                   │                │
     │  Jennifer"───│  LISTENING     │                   │                │
     │              │                │                   │                │
     │──"I see      │                │                   │                │
     │  charges I   │                │                   │                │
     │  didn't      │                │                   │                │
     │  make"──────▶│                │                   │                │
     │              │──system+msg───▶│                   │                │
     │              │                │──get_transactions─▶│                │
     │              │                │◀─transactions──────│──fact_write──▶│
     │              │                │──block_card───────▶│                │   thread:
     │              │                │◀─{blocked, ref}────│──fact_write──▶│   fraud_report
     │              │                │                   │                │   [ACTIVE]
     │              │◀─response──────│                   │                │
     │              │──G1 scan: OK───│                   │                │
     │◀─"I see 3    │                │                   │                │
     │  unauthorized│                │                   │                │
     │  charges.    │                │                   │                │
     │  I've blocked│                │                   │                │
     │  your card"──│                │                   │                │
     │              │                │                   │                │
     │──"what's my  │                │                   │                │   thread:
     │  balance?"──▶│                │                   │                │   fraud_report
     │              │──system+msg───▶│                   │                │   [SUSPENDED]
     │              │  (facts, thread│                   │                │   account_inquiry
     │              │   context)     │                   │                │   [ACTIVE]
     │              │                │──get_balance──────▶│                │
     │              │                │◀─{4215.60, USD}────│──fact_write──▶│
     │              │◀─response──────│                   │                │
     │              │──G1 scan: OK───│                   │                │
     │◀─"Your       │                │                   │                │
     │  checking    │                │                   │                │
     │  balance is  │                │                   │                │
     │  $4,215.60"──│                │                   │                │
     │              │                │                   │                │
     │──"thanks"───▶│                │                   │                │
     │              │──FAREWELL──────│                   │                │
     │◀─"Summary:   │                │                   │                │
     │  blocked     │                │                   │                │
     │  visa, bal   │                │                   │                │
     │  $4,215.60"──│                │                   │                │
     │              │                │                   │                │
```

This shows: auth flow → fraud detection with proactive card block → topic switch (balance inquiry) with thread suspend/resume → farewell with multi-topic summary.

**Key files**: All files work together. See `sample-conversations/` for 12 recorded conversations with real bot responses.
