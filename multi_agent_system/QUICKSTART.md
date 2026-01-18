# Quick Start Guide

## Setup Instructions

### 1. Install Dependencies

```bash
cd multi_agent_system
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=your_actual_key_here
```

Get your Anthropic API key from: https://console.anthropic.com/settings/keys

### 3. Test Phase 1 (Minimal System)

The Phase 1 system includes just the writing agent - perfect for testing the foundation.

#### Option A: Interactive Mode
```bash
python main.py
```

Then try requests like:
- `Write a haiku about Python programming`
- `Summarize the benefits of microservices in 2 paragraphs`
- `Explain recursion in simple terms`

#### Option B: Single Request
```bash
python main.py "Write a 3-paragraph summary of the benefits of type hints in Python"
```

### 4. Verify It Works

You should see:
- ✅ Configuration validation success
- ✅ System initialization
- ✅ Agent execution
- ✅ Pretty formatted output

## What's Implemented ✅ COMPLETE!

### Full Multi-Agent System
- [x] Project structure with all packages
- [x] Configuration management with environment variables
- [x] State schema (AgentState TypedDict)
- [x] **Delegator Agent** - Intelligent routing coordinator
- [x] **Writing Agent** - Content creation & summarization
- [x] **Code Agent** - Code generation & technical explanations
- [x] **Data Analysis Agent** - Statistical analysis & calculations
- [x] **Research Agent** - Web search & information gathering
- [x] **Full Workflow** - Multi-agent collaboration with cycles
- [x] **Synthesis Node** - Combines multi-agent outputs
- [x] **CLI Interface** - Rich formatted interactive mode
- [x] **6 Example Scenarios** - Demonstrating different patterns
- [x] **Comprehensive README** - Architecture guide & learning path

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Make sure you created a `.env` file (copy from `.env.example`)
- Add your API key: `ANTHROPIC_API_KEY=sk-ant-...`
- Don't commit `.env` to git (it's in `.gitignore`)

### Import Errors
- Make sure you're in the `multi_agent_system` directory
- Try: `pip install -r requirements.txt` again
- Check Python version: `python --version` (need 3.8+)

### "Module not found: utils"
- Make sure you're running from the `multi_agent_system` directory
- The directory structure should have `utils/`, `agents/`, `graph/` subdirectories

## Learning Path

1. **Start with the code**: Read through the files in this order:
   - `graph/state.py` - Understand the state structure
   - `agents/writing_agent.py` - See how agents work
   - `graph/workflow.py` - Learn LangGraph basics
   - `main.py` - See how it all connects

2. **Run it**: Test with simple writing requests

3. **Modify it**: Try changing prompts, adding fields to state, etc.

4. **Read the docs**: Every function has detailed docstrings explaining WHY, not just WHAT

## Next Steps

Once Phase 1 is working, we'll add:
- **Phase 2**: Delegator agent for intelligent routing
- **Phase 3**: Three more specialized agents
- **Phase 4**: Multi-agent collaboration
- **Phase 5**: Documentation and examples

Continue implementation by checking the main TODO list in the plan file.
