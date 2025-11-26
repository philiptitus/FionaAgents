# Using MCP Tools: Jupyter vs Standalone Scripts

## The Problem: MCP Tools in Jupyter Notebooks

When you try to use MCP tools in a Jupyter notebook (especially on Windows), you get errors like:

```
UnsupportedOperation: fileno
NotImplementedError: [Errno None] Unknown error
```

### Why This Happens

MCP tools require subprocess creation to communicate with external MCP servers. Jupyter notebooks have limitations:

1. **File Descriptor Issues** - Jupyter's output streams don't support `fileno()` operations needed for subprocess creation
2. **Windows Subprocess Limitations** - Windows subprocess creation is more restrictive than Unix-like systems
3. **Jupyter Environment Constraints** - The notebook environment isn't designed for async subprocess management

---

## Solution: Use Standalone Python Scripts

MCP tools work reliably outside of Jupyter. Here's how:

### File Structure

```
mira/
├── mcp_image_generator.py       # Standalone script (this file)
├── personalized-lead-outreach.ipynb  # Uses function tools (works in Jupyter)
└── requirements.txt
```

### Running the Standalone Script

**Prerequisites:**
```bash
# 1. Node.js and npm must be installed
# Check: node --version && npm --version

# 2. Install MCP server globally (optional but recommended)
npm install -g @modelcontextprotocol/server-everything
```

**Run the script:**
```bash
# Activate your Python environment
& C:\Users\Philip\Desktop\CODE\Python\Agents\env\Scripts\Activate.ps1

# Run the script
python mira/mcp_image_generator.py
```

---

## Key Differences: Jupyter vs Standalone

| Aspect | Jupyter Notebook | Standalone Script |
|--------|------------------|-------------------|
| **MCP Tools** | ❌ Problematic | ✅ Works reliably |
| **Function Tools** | ✅ Works great | ✅ Works great |
| **Agent Tools** | ✅ Works great | ✅ Works great |
| **Long-Running Ops** | ✅ Works | ✅ Works |
| **Subprocess Management** | ❌ Limited | ✅ Full control |
| **Development Speed** | ✅ Fast iteration | Slower (manual runs) |
| **Production Use** | ❌ Not recommended | ✅ Recommended |

---

## When to Use Each Approach

### Use Jupyter Notebooks When:
- ✅ Building **function tools** (custom Python functions)
- ✅ Creating **agent tools** (agents as tools in agents)
- ✅ Implementing **long-running operations** with pause/resume
- ✅ Learning and experimenting
- ✅ Interactive development and visualization

### Use Standalone Scripts When:
- ✅ Working with **MCP tools** (external services)
- ✅ Production deployments
- ✅ Running scheduled tasks/agents
- ✅ Integration with web services or APIs
- ✅ Complex external dependencies

---

## Example Usage Patterns

### Pattern 1: Simple MCP Tool Script

```python
# mcp_script.py
import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

async def main():
    # Create MCP toolset (works here!)
    mcp = McpToolset(...)
    
    # Create agent with MCP tools
    agent = LlmAgent(..., tools=[mcp])
    
    # Run
    runner = InMemoryRunner(agent=agent)
    response = await runner.run_debug("your prompt")

asyncio.run(main())
```

### Pattern 2: Web Service Wrapper

```python
# web_service.py (Flask/FastAPI wrapper)
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.post("/generate-image")
async def generate_image(prompt: str):
    """Endpoint that uses MCP tools"""
    result = await run_image_generation(prompt)
    return result
```

### Pattern 3: Scheduled Task

```python
# scheduled_task.py
import schedule
import time
import asyncio

def job():
    asyncio.run(run_agent_with_mcp_tools())

schedule.every().hour.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Your Project: ADK Agent Notebooks for Fiona

### Recommended Setup

**Notebooks (use these for Fiona integration):**
- ✅ `personalized-lead-outreach.ipynb` - Uses function + agent tools
- ✅ `career-outreach-sequential-agents.ipynb` - Sequential agents
- ✅ `parallel-cold-email-outreach.ipynb` - Parallel agents
- ✅ `loop-agent-problem-refinement.ipynb` - Loop agents

**Standalone Scripts (for production MCP usage):**
- 📄 `mcp_image_generator.py` - Example MCP tool usage
- 📄 `mcp_research_tool.py` - (you can create more as needed)

**Integration with Fiona:**
```
Fiona Frontend (Career + Lead inputs)
        ↓
Fiona Backend (Django)
        ↓
Call Python Agent Service
        ├─→ personalized-lead-outreach.ipynb (function/agent tools)
        └─→ mcp_*.py scripts (if MCP tools needed)
        ↓
Generate Results
        ↓
Return to Fiona (email templates, research)
```

---

## Troubleshooting

### Issue: "npx: command not found"
**Solution:** Install Node.js from https://nodejs.org/

### Issue: "No module named 'google.adk'"
**Solution:** Ensure environment is activated and requirements installed
```bash
pip install -r requirements.txt
```

### Issue: Script hangs or times out
**Solution:** MCP server may not be responding. Check:
```bash
npx -y @modelcontextprotocol/server-everything --help
```

### Issue: "timeout" errors
**Solution:** Increase timeout in script:
```python
timeout=60  # Instead of 30
```

---

## Best Practices

1. **Always use `.env` files** for API keys (never hardcode)
2. **Test MCP tools outside Jupyter first** before integrating
3. **Wrap scripts in try/except** for production use
4. **Use proper async/await patterns** for multiple concurrent calls
5. **Log all operations** for debugging
6. **Version your MCP server specs** if deploying

---

## Next Steps

1. **Install Node.js** if not already installed
2. **Run the example script**: `python mcp_image_generator.py`
3. **Adapt the script** for your specific use cases
4. **Deploy as needed**: Docker, scheduled tasks, web service, etc.

---

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Server Registry](https://modelcontextprotocol.io/examples)
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Node.js Installation](https://nodejs.org/)

---

## Summary

| Use Case | Best Approach |
|----------|---------------|
| Learning agents | Jupyter Notebooks |
| Function/Agent tools | Jupyter Notebooks |
| Production agents | Standalone Scripts |
| MCP tool integration | Standalone Scripts |
| Fiona integration | Hybrid (Notebooks + Scripts) |

**For Fiona:**
- Keep interactive agent development in notebooks
- Use standalone scripts for MCP tools and production deployment
- Wrap scripts in web service for seamless integration
