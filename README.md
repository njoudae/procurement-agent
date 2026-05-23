# Phase 1 — Advanced Python for AI Engineering

Modern AI systems are not simple scripts.

Production AI applications are:

- asynchronous
- distributed
- API-driven
- tool-oriented
- stateful
- scalable
- observable

This means AI Engineers must master advanced Python engineering concepts.

---

# 1. Async / Await

## What Problem Does It Solve?

AI systems spend most of their time waiting for:

- LLM API responses
- databases
- vector stores
- web requests
- file uploads
- external tools

Without async programming, the entire application blocks while waiting.

---

## Basic Example

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(2)
    return "Done"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

---

## Important Keywords

| Keyword | Meaning |
|---|---|
| `async def` | Defines an asynchronous function |
| `await` | Waits for an async operation without blocking |
| `asyncio.run()` | Starts the async event loop |

---

## Parallel Execution Example

```python
import asyncio

async def llm_call():
    await asyncio.sleep(3)
    return "LLM Response"

async def database_call():
    await asyncio.sleep(1)
    return "Database Result"

async def main():
    results = await asyncio.gather(
        llm_call(),
        database_call()
    )

    print(results)

asyncio.run(main())
```

---

## Why This Matters for AI

AI agents often execute:

- memory retrieval
- web search
- vector search
- LLM calls

at the same time.

Async programming dramatically improves latency.

---

# 2. Context Managers

## What Problem Does It Solve?

Resources must be cleaned properly:

- files
- database connections
- HTTP sessions
- browser sessions

Context managers guarantee cleanup.

---

## Basic Example

```python
with open("data.txt") as file:
    content = file.read()
```

The file automatically closes after usage.

---

## Async Context Manager

```python
import aiohttp
import asyncio

async def fetch():
    async with aiohttp.ClientSession() as session:
        response = await session.get("https://example.com")
        print(response.status)

asyncio.run(fetch())
```

---

## What Happens Internally?

```text
Open Session
    ↓
Send Request
    ↓
Wait Without Blocking
    ↓
Receive Response
    ↓
Close Session Automatically
```

---

# 3. Decorators

## What Problem Does It Solve?

Decorators modify function behavior without changing the original code.

Used for:

- logging
- tracing
- retries
- caching
- authentication
- tool registration

---

## Basic Example

```python
def trace(func):
    def wrapper():
        print("Function started")
        func()
        print("Function finished")

    return wrapper


@trace
def hello():
    print("Hello")


hello()
```

---

## Output

```text
Function started
Hello
Function finished
```

---

## AI Engineering Usage

```python
@retry
@trace
async def call_llm():
    ...
```

Common in:

- LangGraph
- FastAPI
- OpenAI Agents SDK
- AI observability systems

---

# 4. Generators

## What Problem Does It Solve?

Generators stream data gradually instead of loading everything into memory.

Important for:

- token streaming
- large datasets
- event streams
- real-time AI responses

---

## Basic Example

```python
def numbers():
    for i in range(5):
        yield i

for num in numbers():
    print(num)
```

---

## Streaming LLM Example

```python
async for chunk in response:
    print(chunk)
```

Used in:

- streaming chatbots
- voice AI
- real-time interfaces

---

# 5. Threading vs Multiprocessing

## Threading

Best for:

- API calls
- I/O operations
- waiting tasks

---

## Example

```python
import threading

def task():
    print("Running task")

thread = threading.Thread(target=task)
thread.start()
```

---

## Multiprocessing

Best for:

- heavy computation
- ML preprocessing
- embedding generation

---

## Example

```python
import multiprocessing

def worker():
    print("Processing")

process = multiprocessing.Process(target=worker)
process.start()
```

---

## Mental Model

```text
Threading
= many waiters

Multiprocessing
= many workers
```

---

# 6. Dependency Injection

## What Problem Does It Solve?

Avoid hardcoded dependencies.

Makes systems:

- modular
- testable
- scalable

---

## Bad Example

```python
db = PostgreSQL()
```

The system is tightly coupled.

---

## Better Example

```python
class Database:
    ...

def agent(db: Database):
    print("Using database")
```

Now any database implementation can be injected.

---

## AI Example

```python
def agent(llm):
    return llm.generate("Hello")
```

You can swap:

- OpenAI
- Claude
- Gemini
- Local Models

without changing agent logic.

---

# 7. Package Management

## What Problem Does It Solve?

AI projects contain many dependencies.

Examples:

- torch
- transformers
- fastapi
- openai
- numpy

Managing them manually becomes difficult.

---

# Modern Tool: uv

`uv` is a modern Python package manager.

Advantages:

- very fast
- dependency resolution
- virtual environment management
- reproducible environments

---

## Example

```bash
uv init
uv add fastapi
uv add openai
```

---

# 8. Virtual Environments

## What Problem Does It Solve?

Different projects require different package versions.

Without isolation:

```text
Dependency conflicts
Broken environments
CUDA mismatches
```

---

## Create Virtual Environment

```bash
uv venv --python 3.12
```

Activate:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / Mac

```bash
source .venv/bin/activate
```

---

# 9. Structured Logging

## What Problem Does It Solve?

Production AI systems require debugging and monitoring.

Using `print()` is insufficient.

---

## Basic Logging

```python
import logging

logging.basicConfig(level=logging.INFO)

logging.info("Application started")
```

---

## Structured Logging Example

```python
logger.info(
    "tool_call",
    extra={
        "tool": "web_search",
        "latency": 1.2
    }
)
```

---

## Why It Matters

AI systems need:

- observability
- tracing
- latency tracking
- token usage monitoring
- failure debugging

---

# 10. Type Hints

## What Problem Does It Solve?

Large AI systems become difficult to maintain without typing.

---

## Example

```python
def add(a: int, b: int) -> int:
    return a + b
```

---

## Benefits

- autocomplete
- static analysis
- safer refactoring
- better readability

---

## AI Engineering Usage

```python
async def retrieve_context(
    query: str
) -> list[str]:
    ...
```

---

# 11. Pydantic

## What Problem Does It Solve?

LLM outputs are unpredictable.

Pydantic validates and structures data.

---

## Example

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
```

---

## Valid Input

```python
user = User(
    name="Ali",
    age="25"
)

print(user)
```

Pydantic automatically converts types.

---

## Invalid Input

```python
User(
    name="Ali",
    age="hello"
)
```

Produces validation errors.

---

## AI Engineering Usage

```python
class AgentAction(BaseModel):
    action: str
    query: str
```

Useful for:

- structured outputs
- tool calling
- API validation
- agent state

---

# 12. Production Folder Structure

## Why Folder Structure Matters

AI systems quickly become large and complex.

Good architecture improves:

- scalability
- maintainability
- debugging
- collaboration

---

# Recommended Structure

```text
app/
├── agents/
├── tools/
├── memory/
├── prompts/
├── workflows/
├── api/
├── schemas/
├── services/
├── observability/
├── config/
├── tests/
└── main.py
```

---

# Folder Responsibilities

| Folder | Purpose |
|---|---|
| `agents/` | AI agents |
| `tools/` | External tools |
| `memory/` | Memory systems |
| `prompts/` | Prompt templates |
| `workflows/` | Agent workflows |
| `api/` | FastAPI routes |
| `schemas/` | Pydantic models |
| `services/` | Business logic |
| `observability/` | Logging & tracing |
| `config/` | Settings & secrets |
| `tests/` | Unit tests |

---

# Final Mindset

Production AI Engineering is not:

```text
Prompt + Chatbot
```

It is:

```text
Reliable Software Systems
that use AI
```

This is why advanced Python engineering is foundational for modern AI systems.

# Phase 2 — APIs API & Backend Fundamentals for AI Systems

## 1. HTTP
Protocol used for communication between client and server over the internet.

```text
Client → HTTP Request → Server
Client ← HTTP Response ← Server
```

Common methods:
- GET → Read data
- POST → Create/process data
- PUT → Replace data
- PATCH → Partial update
- DELETE → Remove data

Example:
```http
GET /users/1
```

---

## 2. REST API
Architecture style for designing APIs using resources.

Example:
```text
/users
/orders
/messages
```

REST principles:
- Resource-based URLs
- Stateless communication
- Correct HTTP methods
- JSON-based communication

Example:
```http
GET /products/5
```

---

## 3. JSON
Standard data format used in APIs.

Example:
```json
{
  "name": "Nejood",
  "role": "AI Engineer"
}
```

Used for:
- API requests/responses
- Tool calling
- LLM structured outputs

---

## 4. Authentication (Auth)
Verifies identity.

Common methods:
- API Keys
- JWT
- OAuth
- Sessions

Example:
```http
Authorization: Bearer sk-xxxx
```

Best practice:
- Never expose secrets in frontend
- Store keys in backend/env variables

---

## 5. OAuth
Delegated authorization system.

Used for:
- Google login
- GitHub login
- Gmail/Slack integrations

Flow:
```text
User → Google Login → Access Token → App Access
```

Important tokens:
- Access Token
- Refresh Token

---

## 6. Webhooks
Event-driven HTTP callbacks.

Instead of polling repeatedly:
```text
Any update?
Any update?
Any update?
```

The service pushes updates automatically.

Flow:
```text
Event Happens
    ↓
Webhook POST Request
    ↓
Your Server Receives Event
```

Used in:
- Stripe
- GitHub
- Slack
- n8n
- Automation systems

---

## 7. Streaming
Sending data progressively instead of waiting for full completion.

Without streaming:
```text
Wait 20 seconds
```

With streaming:
```text
Hello...
How...
Are...
You...
```

Used heavily in:
- LLM token streaming
- AI chat systems
- Real-time generation

---

## 8. SSE (Server-Sent Events)
One-way streaming over HTTP.

Direction:
```text
Server → Client
```

Used for:
- AI token streaming
- Notifications
- Live updates

Advantages:
- Simple
- Browser-friendly
- Lightweight

Limitation:
- Not bidirectional

---

## 9. WebSockets
Persistent real-time bidirectional communication.

Direction:
```text
Client ↔ Server
```

Used in:
- Realtime chat
- Voice AI agents
- Multiplayer apps
- Live dashboards

Difference:
- SSE = one-way
- WebSockets = two-way

---

## 10. Rate Limits
Limits API usage to prevent overload or abuse.

Example:
```text
100 requests/minute
```

Common response:
```http
429 Too Many Requests
```

Why important:
- Prevent abuse
- Control costs
- Protect infrastructure

---

## 11. Retries
Retry failed requests automatically.

Flow:
```text
Request
 ↓
Fail
 ↓
Retry
```

Common failure causes:
- Network issues
- Temporary outages
- Timeouts

Best practice:
- Use exponential backoff
- Retry only safe/idempotent operations

---

## 12. Timeouts
Prevent requests from hanging forever.

Example:
```python
requests.get(url, timeout=10)
```

Meaning:
```text
Stop waiting after 10 seconds
```

Critical for:
- APIs
- LLM calls
- Distributed systems

---

## 13. Idempotency
Repeating the same request should not create duplicate side effects.

Good:
```text
SET balance = 100
```

Bad:
```text
ADD 100
```

Why important:
- Network failures happen
- Clients retry requests
- Prevent duplicate charges/actions

Common solution:
```http
Idempotency-Key: abc123
```

---

# Production AI System Flow

```text
AI Agent
   ↓
HTTP Request
   ↓
REST API
   ↓
JSON Payload
   ↓
Authentication
   ↓
Streaming Response
   ↓
Retry Handling
   ↓
Timeout Protection
   ↓
Rate Limit Control
   ↓
Idempotent Execution
```

---

# Engineering Mindset

Junior engineers focus on:
- prompts
- models
- frameworks

Senior engineers focus on:
- reliability
- scalability
- networking
- retries
- observability
- distributed systems
- production failures

# Phase 3 - Databases & Storage in AI Agent Systems

> “Agents without memory are toys.”

Modern AI systems use different storage types because each solves a different problem.

---

# 1. PostgreSQL → Structured Persistent State

Used for structured relational data.

## Stores
- Users
- Conversations metadata
- Tasks
- Workflow state
- Logs
- Permissions
- Transactions

## Why?
- Reliable persistence
- SQL querying
- Relationships between data
- ACID consistency
- Production-grade reliability

## Example
```sql
SELECT * FROM users WHERE id = 1;
#   p r o c u r e m e n t - a g e n t  
 