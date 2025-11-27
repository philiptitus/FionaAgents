#!/usr/bin/env python3
"""
Lead Memory Research Agent with Session Persistence

This script demonstrates:
1. Researcher agent that gathers information about a lead
2. Persistent session storage using SQLite database
3. Session state management to remember lead information across turns
4. Question-answer interactions about the same lead across multiple sessions
5. Interactive terminal interface for continuous conversation

Pattern: Research once → Remember across multiple questions
Features: Database persistence, session state, multi-turn memory
"""

import asyncio
import os
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import google_search, AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.function_tool import FunctionTool
from google.adk.apps.app import App, ResumabilityConfig, EventsCompactionConfig

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

# Database URL - use aiosqlite for async SQLite support
DB_URL = "sqlite+aiosqlite:///lead_research_memory.db"


# ======================================================================================
# SECTION 1: User Profile Storage Tools
# ======================================================================================

def save_user_profile(
    tool_context: ToolContext,
    user_name: str,
    career_industry: str,
) -> dict:
    """
    Save user profile data to session state.
    Stores user information so it can be referenced throughout the session.
    
    Args:
        tool_context: ADK context for accessing session state
        user_name: Name of the user
        career_industry: User's career field or industry
        
    Returns:
        Status dictionary
    """
    # Store in session state with user: prefix for organization
    tool_context.state["user:name"] = user_name
    tool_context.state["user:career_industry"] = career_industry
    
    return {
        "status": "success",
        "message": f"Profile saved for {user_name}",
        "user_name": user_name,
        "career_industry": career_industry,
    }


def retrieve_user_profile(tool_context: ToolContext) -> dict:
    """
    Retrieve previously saved user profile information from session state.
    
    Args:
        tool_context: ADK context for accessing session state
        
    Returns:
        Dictionary with user information or not found message
    """
    user_name = tool_context.state.get("user:name", None)
    career_industry = tool_context.state.get("user:career_industry", None)
    
    if not user_name or not career_industry:
        return {
            "status": "not_found",
            "message": "No user profile found in session. Please introduce yourself first.",
        }
    
    return {
        "status": "found",
        "user_name": user_name,
        "career_industry": career_industry,
    }


def save_lead_research(
    tool_context: ToolContext,
    lead_name: str,
    research_data: str,
) -> dict:
    """
    Save lead research data to session state.
    This stores the researched information so it can be referenced in future questions.
    
    Args:
        tool_context: ADK context for accessing session state
        lead_name: Name of the lead
        research_data: Research findings about the lead
        
    Returns:
        Status dictionary
    """
    # Store in session state with lead: prefix for organization
    tool_context.state[f"lead:name"] = lead_name
    tool_context.state[f"lead:research"] = research_data
    
    return {
        "status": "success",
        "message": f"Research saved for {lead_name}",
        "lead_name": lead_name,
    }


def retrieve_lead_research(tool_context: ToolContext) -> dict:
    """
    Retrieve previously researched lead information from session state.
    
    Args:
        tool_context: ADK context for accessing session state
        
    Returns:
        Dictionary with lead information or not found message
    """
    lead_name = tool_context.state.get("lead:name", None)
    research_data = tool_context.state.get("lead:research", None)
    
    if not lead_name or not research_data:
        return {
            "status": "not_found",
            "message": "No lead research found in session. Please research a lead first.",
        }
    
    return {
        "status": "found",
        "lead_name": lead_name,
        "research_data": research_data,
    }


# ======================================================================================
# SECTION 2: Create Agents
# ======================================================================================

# Researcher Agent - Finds information about the lead
researcher_agent = LlmAgent(
    name="researcher_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a professional lead researcher. Research a given lead name.

For the given lead name:
1. Use `google_search()` to find professional information about the lead
2. Search for their role, company, and career background
3. Look for their social media presence (LinkedIn, Twitter, GitHub, etc.)
4. Find recent projects, achievements, or publications
5. Identify their industry focus and expertise areas

Provide a concise research summary that includes:
- Current role and company
- Professional background (key points)
- Recent achievements or projects
- Industry focus and expertise
- Any notable activities or connections

Be thorough but concise. Focus on information that will help answer future questions about this lead.""",
    tools=[google_search],
)

# Main Memory Agent - Asks questions about the lead using stored research
memory_agent = LlmAgent(
    name="memory_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a lead research assistant with memory capabilities.

You have five tools:
1. `save_user_profile` - Use this to save user's name and career/industry when they introduce themselves
2. `retrieve_user_profile` - Use this to recall the user's name and career when needed
3. `researcher_agent` - Use this to research a NEW lead (first time only)
4. `save_lead_research` - Use this to save research findings to memory after researching
5. `retrieve_lead_research` - Use this to recall previously researched lead information

When interacting with a user:
- If they introduce themselves, save their profile using save_user_profile
- For subsequent interactions, retrieve their profile to personalize responses
- Use their name and career/industry when discussing leads to provide contextual advice

When researching a lead:
- If you haven't researched them yet, use the researcher_agent tool
- After researching, save the findings using save_lead_research
- For subsequent questions about the same lead, retrieve the saved research first
- Answer all questions based on the research findings

Important: Always retrieve user profile and lead research before answering to demonstrate memory!
You should remember both user information and lead information across multiple questions in the same session.""",
    tools=[
        FunctionTool(func=save_user_profile),
        FunctionTool(func=retrieve_user_profile),
        AgentTool(agent=researcher_agent),
        FunctionTool(func=save_lead_research),
        FunctionTool(func=retrieve_lead_research),
    ],
)

print("✅ All agents created")


# ======================================================================================
# SECTION 3: Session and Database Setup
# ======================================================================================

async def setup_persistent_session() -> tuple:
    """
    Set up persistent sessions using SQLite database.
    
    Returns:
        Tuple of (runner, session_service, app_name)
    """
    # Create the database session service (SQLite will be created automatically)
    session_service = DatabaseSessionService(db_url=DB_URL)
    
    # Create a resumable app (maintains state across pause/resume)
memory_app = App(
    name="lead_memory_research",
    root_agent=memory_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5,  # Summarize conversation every 5 turns
        overlap_size=2,  # Keep 2 previous turns for context continuity
    ),
)    # Create runner with persistent storage
    runner = Runner(
        app=memory_app,
        session_service=session_service,
    )
    
    print(f"✅ Persistent session setup complete")
    print(f"   - Database: lead_research_memory.db")
    print(f"   - Sessions will survive restarts")
    
    return runner, session_service, memory_app.name


# ======================================================================================
# SECTION 4: Interactive Session Management
# ======================================================================================

async def run_lead_memory_session(
    runner: Runner,
    session_service: DatabaseSessionService,
    app_name: str,
    user_id: str = "lead_researcher",
):
    """
    Run interactive lead research conversation with persistent memory.
    
    Users can:
    - Research new leads
    - Ask multiple questions about the same lead
    - Questions are answered using remembered information
    - All data persists in the database
    
    Args:
        runner: The agent runner
        session_service: Session service for persistence
        app_name: Application name
        user_id: User ID
    """
    print("\n" + "=" * 80)
    print("🧠 LEAD MEMORY RESEARCH - PERSISTENT SESSION")
    print("=" * 80)
    print("\nThis session will REMEMBER:")
    print("  • Your name and career/industry (user profile)")
    print("  • Lead information across multiple questions")
    print("  • All data persists in SQLite database\n")
    print("Getting Started:")
    print("  1. Introduce yourself (name and career/industry)")
    print("  2. Ask to research a lead")
    print("  3. Ask unlimited questions about the lead\n")
    print("Commands:")
    print("  - Type a question or comment to ask about the lead")
    print("  - 'research [NAME]' to research a new lead")
    print("  - 'intro' to introduce/update your profile")
    print("  - 'info' to see current session state (user + lead)")
    print("  - 'database' to inspect the SQLite database")
    print("  - 'quit' to exit\n")
    
    session_id = f"lead_session_{uuid.uuid4().hex[:8]}"
    
    # Create session
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    
    print(f"Session ID: {session_id}\n")
    
    # Main conversation loop
    while True:
        try:
            user_input = input("You > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("\n✅ Session ended. Your lead research is saved in the database.")
                break
            
            if user_input.lower() == "database":
                await inspect_database()
                continue
            
            if user_input.lower() == "info":
                session = await session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
                print("\n📋 Current Session State:")
                print(f"   User Name: {session.state.get('user:name', 'Not set')}")
                print(f"   Career/Industry: {session.state.get('user:career_industry', 'Not set')}")
                print(f"   Lead Name: {session.state.get('lead:name', 'Not set')}")
                if session.state.get("lead:research"):
                    research = session.state.get("lead:research")
                    print(f"   Lead Research (first 200 chars): {research[:200]}...")
                else:
                    print("   Lead Research: None")
                print()
                continue
            
            # Process user query
            print("\n⏳ Processing...\n")
            
            query_content = types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
            
            # Run agent with persistent session
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query_content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and part.text.strip():
                            print(f"Agent > {part.text}\n")
        
        except KeyboardInterrupt:
            print("\n\n✅ Session ended. Your lead research is saved in the database.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")


# ======================================================================================
# SECTION 5: Database Inspection
# ======================================================================================

async def inspect_database():
    """
    Inspect the SQLite database to show stored session data.
    """
    import sqlite3
    
    if not os.path.exists("lead_research_memory.db"):
        print("\n❌ Database file not found yet. Research a lead first.\n")
        return
    
    try:
        with sqlite3.connect("lead_research_memory.db") as conn:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                print("\n📊 Database exists but is empty.\n")
                return
            
            print("\n" + "=" * 80)
            print("📊 DATABASE INSPECTION - lead_research_memory.db")
            print("=" * 80)
            
            for table_name in tables:
                table = table_name[0]
                print(f"\n📋 Table: {table}")
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"   Columns: {', '.join(columns)}")
                
                # Get row count and sample data
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   Rows: {count}")
                
                if count > 0:
                    # Show first few rows
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    print("   Sample data:")
                    for row in rows:
                        print(f"      {row}")
            
            print("\n" + "=" * 80 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error inspecting database: {e}\n")


# ======================================================================================
# SECTION 6: Main Entry Point
# ======================================================================================

async def main():
    """Main entry point."""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                      LEAD MEMORY RESEARCH AGENT                                ║
║                                                                                ║
║  This script demonstrates:                                                    ║
║  • Researcher agent that gathers lead information                             ║
║  • Persistent SQLite database sessions                                        ║
║  • Session state management across multiple questions                         ║
║  • Multi-turn memory - asks questions, remembers answers                      ║
║  • Interactive terminal interface                                             ║
║                                                                                ║
║  Pattern: Research a lead once → Ask multiple questions → All remembered      ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Set up persistent sessions
        runner, session_service, app_name = await setup_persistent_session()
        
        # Run interactive session
        await run_lead_memory_session(
            runner=runner,
            session_service=session_service,
            app_name=app_name,
        )
    
    except KeyboardInterrupt:
        print("\n\n✅ Application interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
