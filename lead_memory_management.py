#!/usr/bin/env python3
"""
Lead Memory Management Agent with MemoryService

This script demonstrates memory management capabilities from day-3b:
1. InMemoryMemoryService for long-term knowledge storage
2. Transfer session data to memory using add_session_to_memory()
3. Search and retrieve memories with search_memory()
4. Two retrieval patterns:
   - load_memory: Reactive (agent decides when to search)
   - preload_memory: Proactive (automatic retrieval)
5. Automatic memory storage with callbacks
6. Cross-conversation memory recall

Pattern: Sessions (short-term) + Memory (long-term)
Features: Persistent knowledge, semantic search, automatic storage
"""

import asyncio
import os
from typing import Optional
from dotenv import load_dotenv

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory, preload_memory

# Load environment variables
load_dotenv()

try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    print("✅ Gemini API key loaded")
except Exception as e:
    print(f"❌ Authentication Error: {e}")
    exit(1)

# Configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Application constants
APP_NAME = "LeadMemoryManagement"
USER_ID = "lead_researcher"


# ======================================================================================
# SECTION 1: Callback for Automatic Memory Storage
# ======================================================================================

async def auto_save_to_memory(callback_context):
    """
    Automatically save session to memory after each agent turn.
    
    This callback is triggered after every agent response (after_agent_callback).
    It takes the current session and stores it in the memory service without
    requiring manual intervention.
    
    Args:
        callback_context: ADK context containing session and memory service
    """
    try:
        await callback_context._invocation_context.memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )
        print("  💾 Session saved to memory automatically")
    except Exception as e:
        print(f"  ⚠️  Note: Memory auto-save attempted (for production use)")


# ======================================================================================
# SECTION 2: Helper Functions
# ======================================================================================

async def run_session(
    runner_instance: Runner, user_queries: list[str] | str, session_id: str = "default"
):
    """
    Helper function to run queries in a session and display responses.
    
    Args:
        runner_instance: ADK Runner instance
        user_queries: Single query string or list of queries
        session_id: Identifier for this session
    """
    print(f"\n### Session: {session_id}")

    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
    except:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )

    # Convert single query to list
    if isinstance(user_queries, str):
        user_queries = [user_queries]

    # Process each query
    for query in user_queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])

        # Stream agent response
        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    print(f"Model > {text}")


async def manually_save_session_to_memory(session_id: str):
    """
    Manually transfer a session to memory (for reactive pattern demonstration).
    
    Args:
        session_id: The session ID to save
    """
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        await memory_service.add_session_to_memory(session)
        print(f"✅ Session '{session_id}' manually saved to memory!")
    except Exception as e:
        print(f"❌ Error saving session: {e}")


async def search_memory_for_leads(query: str):
    """
    Search the memory service for lead information.
    
    Args:
        query: Search query to find relevant memories
    """
    try:
        search_response = await memory_service.search_memory(
            app_name=APP_NAME, user_id=USER_ID, query=query
        )

        print(f"\n🔍 Search Results for: '{query}'")
        if search_response.memories:
            print(f"  Found {len(search_response.memories)} relevant memories:\n")
            for i, memory in enumerate(search_response.memories, 1):
                if memory.content and memory.content.parts:
                    text = memory.content.parts[0].text
                    print(f"  [{i}] {memory.author}: {text[:100]}...")
        else:
            print("  No memories found matching this query.")
    except Exception as e:
        print(f"❌ Search error: {e}")


# ======================================================================================
# SECTION 3: Initialize Services and Agents
# ======================================================================================

async def setup_agents():
    """
    Initialize session service, memory service, and agents.
    
    Demonstrates three different agent configurations:
    1. Reactive with load_memory (agent decides when to search)
    2. Proactive with preload_memory (automatic retrieval)
    3. Automatic storage with callbacks
    """
    global session_service, memory_service

    # Create services
    session_service = InMemorySessionService()  # Short-term conversation storage
    memory_service = InMemoryMemoryService()  # Long-term knowledge storage

    print("\n" + "=" * 80)
    print("LEAD MEMORY MANAGEMENT - Memory Service Demo")
    print("=" * 80)
    print("\n📚 Three Memory Patterns:")
    print("  1. REACTIVE: Agent uses load_memory when needed")
    print("  2. PROACTIVE: Agent uses preload_memory automatically")
    print("  3. AUTOMATIC: Callbacks save to memory without manual calls")
    print("\n" + "-" * 80)

    # Pattern 1: Reactive (agent decides when to use load_memory)
    reactive_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="ReactiveMemoryAgent",
        instruction="Answer user questions about leads. Use load_memory tool only when you need to recall information from past conversations.",
        tools=[load_memory],
    )

    # Pattern 2: Proactive (preload_memory always available)
    proactive_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="ProactiveMemoryAgent",
        instruction="Answer user questions about leads. Use preload_memory tool to always have access to past lead information.",
        tools=[preload_memory],
    )

    # Pattern 3: Automatic storage with callback
    auto_memory_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="AutoMemoryAgent",
        instruction="Answer user questions about leads. You have access to all past lead information through memory.",
        tools=[preload_memory],
        after_agent_callback=auto_save_to_memory,  # Automatic memory storage
    )

    return reactive_agent, proactive_agent, auto_memory_agent


# ======================================================================================
# SECTION 4: Main Interactive Loop
# ======================================================================================

async def interactive_memory_demo():
    """
    Interactive demonstration of memory management patterns.
    Shows how to use load_memory, preload_memory, and automatic storage.
    """
    reactive_agent, proactive_agent, auto_memory_agent = await setup_agents()

    # Create runners for each pattern
    reactive_runner = Runner(
        agent=reactive_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    proactive_runner = Runner(
        agent=proactive_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    auto_runner = Runner(
        agent=auto_memory_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    print("\n" + "=" * 80)
    print("🧠 DEMO 1: Manual Memory Storage + Reactive Retrieval")
    print("=" * 80)
    print("\nDemonstrating: Session → Memory Transfer → Cross-session Recall")
    print("(You manually call add_session_to_memory, agent uses load_memory)")

    # Store lead information in first session
    await run_session(
        reactive_runner,
        "Our lead Alex Johnson is a software engineer at TechCorp. He specializes in cloud infrastructure.",
        "lead-alex-session-1",
    )

    # Manually save to memory
    await manually_save_session_to_memory("lead-alex-session-1")

    # Retrieve in a different session
    await run_session(
        reactive_runner,
        "What does Alex Johnson do and what is his specialty?",
        "lead-alex-session-2",  # Different session - shows cross-conversation memory
    )

    print("\n" + "=" * 80)
    print("🧠 DEMO 2: Proactive Memory with Automatic Retrieval")
    print("=" * 80)
    print("\nDemonstrating: preload_memory loads memories automatically")
    print("(No manual save needed, memories pre-loaded in LLM context)")

    # Store lead information
    await run_session(
        proactive_runner,
        "Meet Sarah Chen, a product manager at InnovateTech. She has 8 years of experience in SaaS.",
        "lead-sarah-session-1",
    )

    # Manually save for this demo
    await manually_save_session_to_memory("lead-sarah-session-1")

    # Query in new session - proactive preloading happens automatically
    await run_session(
        proactive_runner,
        "Tell me about Sarah Chen's background and experience.",
        "lead-sarah-session-2",
    )

    print("\n" + "=" * 80)
    print("🧠 DEMO 3: Fully Automated Memory Management")
    print("=" * 80)
    print("\nDemonstrating: Callback + preload_memory = Zero manual intervention")
    print("(Automatic storage after each turn, automatic retrieval)")

    # First conversation - automatically saved by callback
    await run_session(
        auto_runner,
        "I'm interested in Marcus Rodriguez. He's a data scientist at AnalyticsNow with expertise in machine learning.",
        "lead-marcus-session-1",
    )

    # Second conversation - memory automatically preloaded
    await run_session(
        auto_runner,
        "What are Marcus Rodriguez's key qualifications?",
        "lead-marcus-session-2",
    )

    # Third conversation - cross-session memory working
    await run_session(
        auto_runner,
        "Where does Marcus work and what's his role?",
        "lead-marcus-session-3",
    )

    print("\n" + "=" * 80)
    print("🔍 Memory Search Demonstration")
    print("=" * 80)

    # Search for different types of information
    await search_memory_for_leads("cloud infrastructure")
    await search_memory_for_leads("product manager")
    await search_memory_for_leads("machine learning")

    print("\n" + "=" * 80)
    print("💡 Pattern Comparison")
    print("=" * 80)
    print("""
    REACTIVE (load_memory):
    ✅ Agent decides when to search
    ✅ More efficient (only searches when needed)
    ⚠️  Risk: Agent might forget to use memory
    📚 Best for: When search should be intentional

    PROACTIVE (preload_memory):
    ✅ Guaranteed memory available
    ✅ No agent decision needed
    ⚠️  Less efficient (searches every turn)
    📚 Best for: When you always want context available

    AUTOMATIC (callback + preload_memory):
    ✅ Zero manual code needed
    ✅ Memory always current
    ✅ Full automation
    📚 Best for: Production systems
    """)

    print("\n" + "=" * 80)
    print("✅ Memory Management Demo Complete!")
    print("=" * 80)


async def manual_test_mode():
    """
    Interactive manual test mode for experimenting with memory.
    """
    _, _, auto_runner = await setup_agents()

    auto_memory_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="AutoMemoryAgent",
        instruction="You are a helpful lead research assistant. Answer questions about leads using available memory.",
        tools=[preload_memory],
        after_agent_callback=auto_save_to_memory,
    )

    auto_runner = Runner(
        agent=auto_memory_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    print("\n" + "=" * 80)
    print("🧪 Manual Test Mode")
    print("=" * 80)
    print("""
Available commands:
  research <lead_name>      - Research a new lead
  query <question>          - Ask about stored leads (uses memory)
  search <keyword>          - Search memory for specific information
  sessions                  - List all sessions
  memories                  - View all stored memories
  help                      - Show this help
  exit                      - Exit test mode
    """)

    session_count = 0
    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Exiting manual test mode...")
                break

            elif user_input.lower() == "help":
                print("""
Commands:
  research <name>   - Add new lead research
  query <question>  - Ask about leads (uses memory)
  search <keyword>  - Search memory
  sessions          - List sessions
  memories          - View all memories
  exit              - Exit
                """)

            elif user_input.lower().startswith("research "):
                lead_info = user_input[9:].strip()
                session_count += 1
                session_id = f"manual-research-{session_count}"
                await run_session(auto_runner, lead_info, session_id)

            elif user_input.lower().startswith("query "):
                question = user_input[6:].strip()
                session_count += 1
                session_id = f"manual-query-{session_count}"
                await run_session(auto_runner, question, session_id)

            elif user_input.lower().startswith("search "):
                search_term = user_input[7:].strip()
                await search_memory_for_leads(search_term)

            elif user_input.lower() == "sessions":
                print("\n📋 Sessions (stored in InMemorySessionService)")
                print("  (Sessions persist during runtime, reset on restart)")

            elif user_input.lower() == "memories":
                print("\n🧠 Memories (stored in InMemoryMemoryService)")
                await search_memory_for_leads("lead")

            else:
                session_count += 1
                session_id = f"manual-{session_count}"
                await run_session(auto_runner, user_input, session_id)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


# ======================================================================================
# SECTION 5: Main Entry Point
# ======================================================================================

async def main():
    """Main entry point for the application."""
    try:
        # Initialize global services
        global session_service, memory_service
        session_service = InMemorySessionService()
        memory_service = InMemoryMemoryService()

        print("\n" + "=" * 80)
        print("🎯 Lead Memory Management - Memory Service Patterns")
        print("=" * 80)

        print("""
This script demonstrates memory management patterns from day-3b:

Options:
  1. Run automated demo of all patterns
  2. Enter interactive manual test mode

Choose an option:
        """)

        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":
            await interactive_memory_demo()
        elif choice == "2":
            await manual_test_mode()
        else:
            print("Invalid choice. Running automated demo...")
            await interactive_memory_demo()

    except KeyboardInterrupt:
        print("\n\n👋 Exiting gracefully...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
