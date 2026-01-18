# 🤖 Educational Multi-Agent Orchestration System

An educational project demonstrating fundamental AI agent architecture patterns using LangChain and LangGraph. Built to teach through working code with extensive inline documentation.

---

## 🎯 Learning Objectives

This project teaches you:

1. **How LangGraph's state machine differs from simple function calling**
   - Shared state vs parameter passing
   - Conditional routing vs fixed sequences
   - Cycles for iterative workflows

2. **When to use LangChain's RunnableSequence vs LangGraph nodes**
   - Linear workflows → RunnableSequence
   - Dynamic routing → LangGraph
   - Multi-agent coordination → LangGraph

3. **How to structure prompts for delegation vs execution**
   - Meta-agent prompts (routing decisions)
   - Specialized agent prompts (task execution)
   - Context passing between agents

4. **Best practices for agent-to-agent communication**
   - State as shared memory
   - Structured outputs with Pydantic
   - Message passing patterns

5. **How to handle cases where multiple agents need to collaborate**
   - Collaboration planning
   - Sequential execution
   - Output synthesis

---

## 📊 Architecture Overview

### System Diagram

```
                         USER REQUEST
                              │
                              ▼
                    ┌─────────────────┐
                    │ Analyze Request │
                    │ (Pre-processing)│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
              ┌────▶│   Delegator     │◀────┐
              │     │  (Meta-Agent)   │     │
              │     └────────┬─────────┘     │
              │              │                │
              │              ▼                │
              │     ┌────────────────┐        │
              │     │   Route Agent  │        │
              │     └───┬───┬───┬───┬┘        │
              │         │   │   │   │         │
              │    ┌────┘   │   │   └────┐    │
              │    │        │   │        │    │
              │    ▼        ▼   ▼        ▼    │
              │ ┌──────┐ ┌────┐ ┌────┐ ┌────┐ │
              │ │Research│ │Data│ │Code│ │Writing│
              │ │ Agent │ │Agent│ │Agent│ │ Agent│
              │ └───┬──┘ └──┬─┘ └──┬─┘ └──┬─┘ │
              │     │       │      │      │    │
              │     └───────┴──────┴──────┘    │
              │              │                  │
              │              ▼                  │
              │     ┌─────────────────┐        │
              │     │   Synthesis     │        │
              │     │(Combine Outputs)│        │
              │     └────────┬─────────┘        │
              │              │                  │
              │              ▼                  │
              │     ┌─────────────────┐        │
              │     │ Should Continue?│        │
              │     └────┬──────┬──────┘        │
              │          │      │               │
              │     Yes  │      │  No           │
              └──────────┘      └──────▶ END
```

### Components

#### **1. Delegator Agent (Meta-Agent)**
- **Role**: Intelligent request routing
- **How it works**: Uses Claude to analyze requests and decide which agent should handle them
- **Pattern**: Meta-agent (manages other agents)
- **Key learning**: LLM-powered routing vs hardcoded rules

#### **2. Specialized Task Agents**

| Agent | Capability | Pattern Demonstrated |
|-------|------------|---------------------|
| **Writing** | Content creation, summaries, editing | Single-purpose generative agent |
| **Code** | Code generation, technical explanations | Multi-step reasoning agent |
| **Data Analysis** | Statistics, calculations, insights | Computational agent (Python + LLM) |
| **Research** | Web search, information gathering | Tool-augmented agent |

#### **3. LangGraph Workflow**
- **State Management**: Shared state flows through all nodes
- **Conditional Routing**: Delegator decisions determine path
- **Cycles**: Enables multi-agent sequential workflows
- **Synthesis**: Combines outputs from multiple agents

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (Python 3.11+ recommended)
- Anthropic API key ([get one here](https://console.anthropic.com/settings/keys))
- (Optional) Tavily API key for web search ([get here](https://tavily.com/))

### Installation

1. **Navigate to the project root directory:**
```bash
cd bots
```

2. **Create a virtual environment** (recommended to avoid package conflicts):
```bash
python -m venv venv
```

3. **Activate the virtual environment:**

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r multi_agent_system/requirements.txt
```

> **Note:** If you encounter version conflicts, use the updated requirements:
> ```bash
> pip install langchain langchain-anthropic langgraph langchain-community anthropic python-dotenv pydantic rich
> ```

5. **Set up your API key** (choose ONE method):

**Option A: TOML file (recommended)** - Create `config.toml` in the `bots/` root directory:
```toml
[anthropic]
api_key = "sk-ant-your-api-key-here"

[settings]
default_model = "claude-3-5-haiku-20241022"
temperature = 0.7

[features]
max_iterations = 10
show_decision_log = true
```

**Option B: Environment file** - Copy and edit `.env`:
```bash
cd multi_agent_system
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Running the System

> **IMPORTANT:** Always use the virtual environment Python, not your system Python!

**From the `bots/` root directory:**

```bash
# Interactive mode (recommended for learning)
cd multi_agent_system
..\venv\Scripts\python.exe main.py      # Windows
../venv/bin/python main.py               # macOS/Linux

# Single request mode
..\venv\Scripts\python.exe main.py "Write a haiku about Python"

# Run example scenarios
..\venv\Scripts\python.exe examples/example_requests.py
```

**Or if you activated the virtual environment:**
```bash
cd multi_agent_system
python main.py
```

### Quick Test

Verify everything works:
```bash
cd multi_agent_system
..\venv\Scripts\python.exe main.py "Explain Python decorators in 2 sentences"
```

You should see:
1. The system banner
2. Agent decision log showing the delegator routing to the writing agent
3. The generated response

### Model Cost Comparison

The default model is `claude-3-5-haiku-20241022` (cheapest option):

| Model | Input Cost | Output Cost | Best For |
|-------|-----------|-------------|----------|
| claude-3-5-haiku-20241022 | $1/MTok | $5/MTok | Learning, testing, simple tasks |
| claude-3-5-sonnet-20241022 | $3/MTok | $15/MTok | Better quality, code generation |
| claude-sonnet-4-5-20250929 | $3/MTok | $15/MTok | Latest features |
| claude-opus-4-5-20251101 | $15/MTok | $75/MTok | Most powerful |

Change models in `config.toml` or `.env` file.

### 🖥️ Visual Learning UI (Streamlit)

For a visual, interactive learning experience, run the Streamlit app:

**Windows (easiest - double-click):**
```bash
# Double-click: multi_agent_system/run_streamlit.bat
```

**From command line:**
```bash
cd multi_agent_system

# Windows
..\venv\Scripts\streamlit.exe run streamlit_app/app.py

# macOS/Linux
../venv/bin/streamlit run streamlit_app/app.py

# Or with activated venv
streamlit run streamlit_app/app.py
```

**What the Streamlit UI shows:**
- **Graph Tab**: Visual workflow with highlighted current node
- **State Tab**: Real-time AgentState changes
- **Timeline Tab**: Every step with prompts and responses
- **Learn Tab**: Educational explanations of concepts

**Features:**
- Step-through execution mode (pause at each step)
- See exact prompts sent to Claude
- Watch state accumulation in real-time
- Educational tooltips and concept explanations

---

## 🎓 Learning Path

### Step 1: Understand the Foundation
Start by reading these files in order:

1. **`graph/state.py`** - The data structure that flows through the system
   - Learn about TypedDict and state management
   - Understand why state beats parameter passing

2. **`agents/writing_agent.py`** - Simplest agent
   - See the basic agent pattern
   - Understand system prompts vs user messages
   - Learn error handling

3. **`graph/workflow.py`** - The orchestration engine
   - Understand nodes vs edges
   - Learn conditional routing
   - See how cycles enable iteration

4. **`agents/delegator.py`** - The coordinator
   - Meta-agent pattern
   - LLM-powered routing decisions
   - Structured outputs with Pydantic

### Step 2: Run and Experiment

```bash
# Start with simple single-agent requests
python main.py "Write a haiku about Python"

# Try code generation
python main.py "Generate a function to sort a list"

# Test multi-agent collaboration
python main.py "Research Python 3.12 features, analyze adoption rates, and write a summary"

# Run all example scenarios
python examples/example_requests.py
```

### Step 3: Modify and Extend

Try these exercises:

1. **Add a new agent:**
   - Create `agents/my_agent.py` following the writing_agent pattern
   - Add it to the delegator's system prompt
   - Update `workflow.py` to include the new node

2. **Modify prompts:**
   - Change agent system prompts to alter behavior
   - Adjust delegator prompt to change routing strategy
   - See how prompt engineering affects results

3. **Add custom state fields:**
   - Add new fields to `AgentState` in `graph/state.py`
   - Use them to pass custom data between agents

---

## 📁 Project Structure

```
multi_agent_system/
├── agents/                  # Specialized agents
│   ├── delegator.py        # Routing coordinator (meta-agent)
│   ├── writing_agent.py    # Content creation
│   ├── code_agent.py       # Code generation
│   ├── data_agent.py       # Statistical analysis
│   └── research_agent.py   # Web search & research
│
├── graph/                   # LangGraph workflow
│   ├── state.py            # State schema (AgentState)
│   └── workflow.py         # Workflow definition
│
├── utils/                   # Utilities
│   └── config.py           # Environment & model configuration
│
├── examples/                # Example scenarios
│   └── example_requests.py # 6 scenarios demonstrating capabilities
│
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

---

## 🔍 Key Concepts Explained

### 1. State Management

**Traditional approach** (parameter passing):
```python
result1 = agent1(user_input)
result2 = agent2(result1)  # Must explicitly pass
result3 = agent3(result2)
```

**LangGraph approach** (shared state):
```python
state = {"user_request": "...", "messages": []}
agent1(state)  # Updates state
agent2(state)  # Can access agent1's results from state
agent3(state)  # Can access both agent1 and agent2 results
```

**Benefits:**
- Nodes don't need to know about each other
- Easy to add/remove agents
- State accumulates information naturally
- Enables complex routing logic

### 2. Meta-Agent Pattern

The **delegator** is a meta-agent - it doesn't do work itself, but decides WHO should do it.

**Why this matters:**
- Separation of concerns (routing vs executing)
- Flexible - easy to add new agents
- Intelligent - uses LLM reasoning for routing
- Debuggable - routing logic in one place

**Alternatives and why we didn't use them:**
- Keyword matching: Brittle, misses nuance
- User selection: More work for user
- Hardcoded rules: Difficult to maintain

### 3. Conditional Routing vs Linear Chains

**Linear Chain** (LangChain RunnableSequence):
```python
chain = research | analyze | write
result = chain.invoke(request)  # Always same sequence
```

**Conditional Routing** (LangGraph):
```python
# Route based on request content
if needs_research:
    route_to(research_agent)
elif needs_code:
    route_to(code_agent)
else:
    route_to(writing_agent)
```

**When to use each:**
- Linear Chain: Predictable workflows (always same steps)
- Conditional Routing: Request determines path

### 4. Cycles for Iteration

LangGraph enables cycles, allowing:
```
delegator → agent1 → synthesis → delegator → agent2 → synthesis → END
```

**Use cases:**
- Multi-step workflows
- Iterative refinement
- Complex tasks requiring multiple specialists

### 5. Tool-Augmented Agents

The **research agent** demonstrates this pattern:
- LLM for reasoning and synthesis
- Web search tool for current information
- Combines LLM intelligence with external data

---

## 🎯 Example Scenarios

### Scenario 1: Simple Single-Agent
**Request:** "Write a summary of microservices architecture"

**What happens:**
1. Analyze: Detects writing task, no collaboration needed
2. Delegator: Routes to writing agent
3. Writing agent: Generates summary
4. Synthesis: Minimal (only one agent)
5. Finish

**Learning:** Simplest routing case, demonstrates basic flow

### Scenario 2: Multi-Agent Collaboration
**Request:** "Research Python async frameworks, analyze their GitHub stars, then write a comparison"

**What happens:**
1. Analyze: Detects multi-step workflow, creates plan: [research, data, writing]
2. Delegator (iteration 1): Routes to research agent
3. Research agent: Gathers framework information
4. Synthesis: Checks plan, sees more work needed
5. Delegator (iteration 2): Routes to data agent
6. Data agent: Analyzes GitHub metrics
7. Synthesis: Still more work
8. Delegator (iteration 3): Routes to writing agent
9. Writing agent: Creates comparison report
10. Synthesis: All done
11. Finish

**Learning:** Sequential collaboration, state accumulation, iterative workflow

### More Scenarios

See `examples/example_requests.py` for 6 complete scenarios with expected outputs and learning points.

---

## 🛠️ Extension Ideas

### Easy Extensions
1. **Agent Metrics**: Track latency, success rate per agent
2. **Human-in-the-Loop**: Add approval gates before expensive operations
3. **Better Logging**: Enhanced decision visibility

### Medium Extensions
4. **Memory Agent**: Add vector database for conversation history
5. **Multi-Model Support**: Use different models per agent
6. **Streaming**: Real-time output as agents work

### Advanced Extensions
7. **Hierarchical Teams**: Agents that manage sub-agents
8. **Learning from Feedback**: Improve routing based on user feedback
9. **Parallel Execution**: Run independent agents concurrently

See `docs/extending.md` (coming soon) for implementation guides.

---

## 📖 Additional Resources

### Official Documentation
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)

### Related Patterns
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - Autonomous agent framework
- [BabyAGI](https://github.com/yoheinakajima/babyagi) - Task-driven autonomous agent
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

### Learning More
- Read the inline documentation - every function explains WHY
- Look for "KEY CONCEPT" blocks throughout the code
- Check "WHY THIS MATTERS" sections
- Compare "LEARNING OBJECTIVE" comments

---

## 🐛 Troubleshooting

### "ImportError: cannot import name 'CheckpointAt'" or similar import errors
**This is the most common issue!** You're using your system Python instead of the virtual environment.

**Solution:** Always use the venv Python:
```bash
# WRONG (uses system Python):
python main.py

# CORRECT (uses virtual environment):
..\venv\Scripts\python.exe main.py      # Windows
../venv/bin/python main.py               # macOS/Linux
```

### "ANTHROPIC_API_KEY not set"
- Create `config.toml` in the `bots/` root directory with your API key, OR
- Ensure `.env` file exists in `multi_agent_system/` (copy from `.env.example`)
- Add your API key: `ANTHROPIC_API_KEY=sk-ant-...`
- Don't commit these files to git (they're in `.gitignore`)

### "Your credit balance is too low"
- Add credits to your Anthropic account at [console.anthropic.com](https://console.anthropic.com/settings/billing)
- The cheapest model (Haiku) costs ~$1/million tokens input

### "Module not found: langchain" or similar
- You need to install dependencies in the virtual environment:
```bash
.\venv\Scripts\python.exe -m pip install -r multi_agent_system/requirements.txt
```

### "Module not found: utils"
- Make sure you're in the `multi_agent_system` directory when running
- Run from the correct location:
```bash
cd multi_agent_system
..\venv\Scripts\python.exe main.py
```

### "No search results" (Research Agent)
- Research agent works without API keys (uses LLM knowledge)
- For web search: Add `TAVILY_API_KEY` to `config.toml` or `.env`
- Or install DuckDuckGo: `.\venv\Scripts\python.exe -m pip install duckduckgo-search`

### Agent routing seems wrong
- Check logs - delegator explains reasoning
- Set `LOG_LEVEL=DEBUG` in `config.toml` or `.env` for verbose output
- `show_decision_log = true` in config.toml shows the full decision trail

### PowerShell script execution disabled
If you see "running scripts is disabled on this system":
- This is a Windows security setting and doesn't affect running the application
- Just use the direct Python path: `..\venv\Scripts\python.exe main.py`

---

## 🤝 Contributing

This is an educational project. Contributions welcome:
- Documentation improvements
- Additional example scenarios
- New agent types with educational value
- Bug fixes

Please keep the focus on **learning** - prioritize clarity over complexity.

---

## 📝 License

MIT License - feel free to use this for learning and teaching!

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Anthropic Claude](https://www.anthropic.com/) - LLM powering the agents
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output

---

## 📬 Questions or Feedback?

This project prioritizes learning. If something is unclear:
1. Check the inline documentation in the code
2. Look for "KEY CONCEPT" blocks
3. Run example scenarios to see patterns in action
4. Read error messages carefully - they're educational too!

**Remember:** The best way to learn is by modifying the code. Break things, fix them, and understand why!

---

**Happy Learning! 🚀**
