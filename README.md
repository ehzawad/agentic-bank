# Product-Grade B2B Chatbot

A production-ready, domain-agnostic B2B conversational AI chatbot powered by Claude Sonnet 4.6. Reference implementation targets banking customer service (HSBC/Citi-grade), but the core engine is reusable across any vertical.

## Architecture

Single-pass Claude with native tool_use, replacing the original Llama 8B two-pass design. See [ARCHITECTURE.md](./ARCHITECTURE.md) for 10 detailed diagrams with design rationale.

```
User Message → Auth Gate → Context Builder (5 memory stores) → Claude Sonnet 4.6
    → Tool Loop (20 banking tools via Service Adapters) → Guardrails → Response
```

### Core Components

| Component | What it does |
|-----------|-------------|
| **Conversation Engine** | Per-turn loop: auth gate, context assembly, Claude API call, tool execution, guardrails, memory update |
| **5 Memory Stores** | Session, Facts (tool-only writes), Threads (topic tracking), Emotion (heuristic scoring), Turns |
| **Service Adapter Layer** | Protocol-based interfaces for banking APIs. Mock implementations for dev, swappable per bank deployment |
| **20 Tool Definitions** | Balance, transactions, card management, loans, transfers, documents, complaints, knowledge base search |
| **FAQ/Knowledge Base** | OpenAI text-embedding-3-small + ChromaDB. Three confidence tiers: high (>0.85) pure FAQ, medium (0.6-0.85) hedged blend, low (<0.6) LLM with disclaimer |
| **Workflow Engine** | Multi-step flows with slot filling, suspend/resume on topic switch |
| **Guardrails** | G1: hallucination blocker, G3: fact integrity (architectural), G4: hedge enforcer (system prompt), G5: emotion escalation |
| **Dialogue State Machine** | 11 states: Greeting → Auth → Listening → Tool/FAQ/Workflow → Farewell/HumanTransfer |

### Key Design Decisions

- **Single-pass LLM**: Claude handles intent resolution, tool calling, and natural response in one API call via native `tool_use`
- **Domain-agnostic core**: Only the FAQ corpus, tool definitions, and service adapters change per domain
- **Token streaming**: Real token streaming replaces the Llama filler response hack
- **Service Adapters**: Python Protocol classes with swappable implementations (mock for dev, real API clients per bank)
- **Auth gate as system precondition**: Not a tool call — tools are withheld until verification passes

## Quick Start

```bash
# Install
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Run
uvicorn chatbot.main:app --reload

# Test
curl -X POST http://localhost:8000/api/sessions
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "Hi, I need help"}'
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions` | Create a new chat session |
| POST | `/api/chat` | Send a message, get a response |
| GET | `/api/sessions/{id}` | Get full session state |
| DELETE | `/api/sessions/{id}` | End a session |
| GET | `/api/health` | Health check |

## Project Structure

```
chatbot/
    engine/          # Core conversation loop, Claude client, context builder
    memory/          # 5 stores: session, facts, threads, emotion, turns
    services/        # Protocol definitions + mock banking services
    knowledge/       # OpenAI text-embedding-3-small + ChromaDB vector store
    workflows/       # Multi-step workflow engine + definitions
    guardrails/      # Hallucination blocker, emotion escalation
    state/           # Dialogue state machine
    tools/           # 20 tool schemas + handler registry
    api/             # FastAPI endpoints
scenarios/           # 10 HSBC/Citi-grade test conversations
sample-conversations/ # 12 recorded conversations with real bot responses
ARCHITECTURE.md      # 10 system design diagrams with rationale
```

## Reference Materials

- `ARCHITECTURE.md` — 10 architecture diagrams documenting the current Claude-based design
- `scenarios/` — 10 realistic banking conversation scenarios with annotations
- `sample-conversations/` — 12 recorded multi-turn conversations with real bot responses

## License

All rights reserved.
