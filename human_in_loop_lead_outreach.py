#!/usr/bin/env python3
"""
Human-in-the-Loop Lead Outreach Agent

This script demonstrates:
1. Personalized lead research using Agent Tools
2. Email generation for cold outreach
3. Human-in-the-loop approval workflow
4. Automatic regeneration if user rejects the email
5. Mock email sending when approved

Pattern: Researcher Agent → Main Outreach Agent → Human Review → Approve/Reject Loop
"""

import asyncio
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.function_tool import FunctionTool
from google.adk.apps.app import App, ResumabilityConfig

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

# Track email generation attempts
generation_attempt = 0
MAX_ATTEMPTS = 3


# ======================================================================================
# SECTION 1: Email Approval Tool with Human-in-the-Loop
# ======================================================================================

def request_email_approval(
    email_subject: str,
    email_body: str,
    lead_name: str,
    tool_context: ToolContext,
) -> dict:
    """
    Tool that pauses the workflow to request human approval of the generated email.
    
    This is the critical long-running operation tool:
    - First call: Pauses and asks for approval
    - Second call (after human decision): Processes the approval/rejection
    
    Args:
        email_subject: Subject line of the email
        email_body: Body text of the email
        lead_name: Name of the lead (for context)
        tool_context: ADK context for pause/resume
        
    Returns:
        Dict with approval status
    """
    
    # SCENARIO 1: First call - Request approval
    if not tool_context.tool_confirmation:
        tool_context.request_confirmation(
            hint=f"⏸️  Review email for {lead_name}. Subject: '{email_subject}' - Approve or reject?",
            payload={
                "email_subject": email_subject,
                "email_body": email_body,
                "lead_name": lead_name,
            },
        )
        return {
            "status": "pending",
            "message": f"Email for {lead_name} awaiting approval",
        }
    
    # SCENARIO 2: Resumed call - Handle approval/rejection
    if tool_context.tool_confirmation.confirmed:
        return {
            "status": "approved",
            "message": f"Email approved for {lead_name}",
            "email_subject": email_subject,
            "email_body": email_body,
        }
    else:
        return {
            "status": "rejected",
            "message": f"Email rejected. Request regeneration.",
            "reason": "User requested changes",
        }


# ======================================================================================
# SECTION 2: Email Sending Tool (Mock)
# ======================================================================================

def send_email_mock(
    to_email: str,
    subject: str,
    body: str,
) -> dict:
    """
    Mock email sending function.
    In production, this would integrate with:
    - Fiona platform
    - SendGrid / SMTP
    - Email service API
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text
        
    Returns:
        Dict with send status
    """
    import time
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "sent",
        "timestamp": timestamp,
        "to": to_email,
        "subject": subject,
        "message_length": len(body),
        "message_id": f"MSG-{uuid.uuid4().hex[:8].upper()}",
    }


# ======================================================================================
# SECTION 3: Create Agents
# ======================================================================================

# Researcher Agent - Finds information about the lead
researcher_agent = LlmAgent(
    name="researcher_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a professional lead researcher. Your job is to investigate a potential business contact.

For the given lead name and context:
1. Use `google_search()` to find professional information about the lead
2. Search for their role, company, and career background
3. Look for their social media presence (LinkedIn, Twitter, GitHub, etc.)
4. Find recent projects, achievements, or publications
5. Identify their industry focus and expertise areas

Provide a concise but detailed research summary that includes:
- Current role and company
- Professional background (3-5 key points)
- Recent achievements or projects
- Industry focus and key expertise
- Any notable activities or connections

Focus on information useful for personalized cold outreach.""",
    tools=[google_search],
)

# Main Outreach Agent - Generates personalized emails
main_outreach_agent = LlmAgent(
    name="main_outreach_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a personalized cold outreach specialist who creates research-backed emails.

You have TWO key tasks:

**Task 1: Research the Lead**
Use the researcher_agent tool to gather information about the lead and career context provided.

**Task 2: Generate Personalized Email**
Based on research findings, create a professional cold outreach email that:
- Opens with a personalized reference to their work/achievement/expertise
- Demonstrates genuine knowledge of their background
- Explains clear value relevant to THEIR interests
- Is professional, authentic, and concise (100-150 words)
- Includes a clear call-to-action
- Uses a compelling subject line

**Important:** When generating the email, include BOTH a subject line AND body text.

Format your response as:
SUBJECT: [subject line]
BODY: [email body]

Make it personal and reference specific findings from the research.""",
    tools=[AgentTool(agent=researcher_agent)],
)

# Email Approval Agent - Manages the approval workflow
email_approval_agent = LlmAgent(
    name="email_approval_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an email approval coordinator.

Your role is to submit emails for human review before sending.

When you receive an email:
1. Extract the SUBJECT and BODY clearly
2. Use the request_email_approval tool with these components and the lead name
3. Report the approval status back to the user

Format: Present the email clearly with subject and body separated.""",
    tools=[FunctionTool(func=request_email_approval)],
)

# Final Delivery Agent - Sends approved emails
final_delivery_agent = LlmAgent(
    name="final_delivery_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a delivery coordinator. When an email is approved, send it.

Extract the recipient email, subject, and body, then use the send_email_mock tool.
Report success with the message ID.""",
    tools=[FunctionTool(func=send_email_mock)],
)

print("✅ All agents created")


# ======================================================================================
# SECTION 4: Helper Functions for Event Processing
# ======================================================================================

def check_for_approval(events) -> Optional[dict]:
    """
    Detect if workflow paused for human approval.
    
    Returns:
        Dict with approval_id and invocation_id if paused, None otherwise
    """
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "adk_request_confirmation"
                ):
                    return {
                        "approval_id": part.function_call.id,
                        "invocation_id": event.invocation_id,
                    }
    return None


def extract_email_from_response(events) -> Optional[dict]:
    """
    Extract email subject and body from agent response.
    
    Returns:
        Dict with 'subject' and 'body' if found, None otherwise
    """
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text = part.text
                    if "SUBJECT:" in text and "BODY:" in text:
                        # Parse email format
                        lines = text.split("\n")
                        subject = None
                        body_start = None
                        
                        for i, line in enumerate(lines):
                            if line.startswith("SUBJECT:"):
                                subject = line.replace("SUBJECT:", "").strip()
                            if line.startswith("BODY:"):
                                body_start = i
                                break
                        
                        if subject and body_start is not None:
                            body = "\n".join(lines[body_start + 1:]).replace("BODY:", "").strip()
                            return {"subject": subject, "body": body}
    
    return None


def create_approval_response(approval_info: dict, approved: bool) -> types.Content:
    """
    Create the response message for approval/rejection.
    
    Args:
        approval_info: Dict with approval_id and invocation_id
        approved: Boolean - True to approve, False to reject
        
    Returns:
        ADK Content object with the decision
    """
    confirmation_response = types.FunctionResponse(
        id=approval_info["approval_id"],
        name="adk_request_confirmation",
        response={"confirmed": approved},
    )
    return types.Content(
        role="user", parts=[types.Part(function_response=confirmation_response)]
    )


def print_section(title: str, char: str = "="):
    """Print formatted section header."""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")


def print_email_preview(email_dict: dict):
    """Print email in readable format."""
    if not email_dict:
        return
    
    print("📧 EMAIL PREVIEW")
    print(f"─" * 80)
    print(f"Subject: {email_dict['subject']}")
    print(f"─" * 80)
    print(email_dict['body'])
    print(f"─" * 80)


# ======================================================================================
# SECTION 5: Main Workflow - Human-in-the-Loop with Regeneration
# ======================================================================================

async def run_lead_outreach_workflow(
    career_field: str,
    lead_name: str,
    lead_email: str = "lead@example.com",
):
    """
    Run the complete lead outreach workflow with human approval and regeneration.
    
    Flow:
    1. Research the lead
    2. Generate personalized email
    3. Request human approval
    4. If approved: Send email
    5. If rejected: Regenerate (up to MAX_ATTEMPTS times)
    
    Args:
        career_field: User's career field/background
        lead_name: Name of the lead to research
        lead_email: Email address of the lead (for mock sending)
    """
    global generation_attempt
    
    print_section(f"🚀 LEAD OUTREACH WORKFLOW - {lead_name}")
    print(f"👤 Career Field: {career_field}")
    print(f"🎯 Lead: {lead_name} ({lead_email})")
    print(f"⏳ Starting workflow...\n")
    
    session_service = InMemorySessionService()
    session_id = f"outreach_{uuid.uuid4().hex[:8]}"
    
    # Create resumable app for the outreach agent
    outreach_app = App(
        name="lead_outreach",
        root_agent=main_outreach_agent,
        resumability_config=ResumabilityConfig(is_resumable=True),
    )
    
    outreach_runner = Runner(
        app=outreach_app,
        session_service=session_service,
    )
    
    # Create session
    await session_service.create_session(
        app_name="lead_outreach",
        user_id="outreach_user",
        session_id=session_id,
    )
    
    # Step 1: Generate personalized email
    print_section("📝 STEP 1: Generating Personalized Email")
    
    generation_attempt = 0
    email_approved = False
    
    while generation_attempt < MAX_ATTEMPTS and not email_approved:
        generation_attempt += 1
        print(f"Generation Attempt: {generation_attempt}/{MAX_ATTEMPTS}\n")
        
        # Initial request for email generation
        query = f"""I work in {career_field}.

Please research {lead_name} and create a personalized cold outreach email.
Make it relevant to my career and their background.
The email should be authentic and demonstrate genuine research.

Format with SUBJECT: and BODY: headers."""
        
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        
        # Run agent to generate email
        events = []
        async for event in outreach_runner.run_async(
            user_id="outreach_user",
            session_id=session_id,
            new_message=query_content,
        ):
            events.append(event)
        
        # Extract generated email
        email = extract_email_from_response(events)
        if email:
            print_email_preview(email)
        else:
            print("⚠️  Could not extract email format. Please check agent response.")
            continue
        
        # Step 2: Request human approval
        print_section("👤 STEP 2: Requesting Human Approval")
        
        # Create approval app
        approval_app = App(
            name="email_approval",
            root_agent=email_approval_agent,
            resumability_config=ResumabilityConfig(is_resumable=True),
        )
        
        approval_runner = Runner(
            app=approval_app,
            session_service=session_service,
        )
        
        approval_session_id = f"approval_{uuid.uuid4().hex[:8]}"
        await session_service.create_session(
            app_name="email_approval",
            user_id="outreach_user",
            session_id=approval_session_id,
        )
        
        # Request approval
        approval_query = f"""Review this email for {lead_name}:

SUBJECT: {email['subject']}

BODY:
{email['body']}

Use request_email_approval to submit for review."""
        
        approval_content = types.Content(
            role="user", parts=[types.Part(text=approval_query)]
        )
        
        approval_events = []
        async for event in approval_runner.run_async(
            user_id="outreach_user",
            session_id=approval_session_id,
            new_message=approval_content,
        ):
            approval_events.append(event)
        
        # Check if approval was requested
        approval_info = check_for_approval(approval_events)
        
        if approval_info:
            print(f"⏸️  Awaiting human decision...\n")
            
            # Simulate human decision (in production, this comes from UI)
            user_decision = await get_user_approval_decision(
                email, lead_name, generation_attempt
            )
            
            # Resume with decision
            approval_response = create_approval_response(approval_info, user_decision)
            
            print(f"\n{'─' * 80}")
            print(f"Human Decision: {'✅ APPROVED' if user_decision else '❌ REJECTED'}")
            print(f"{'─' * 80}\n")
            
            # Resume approval agent
            async for event in approval_runner.run_async(
                user_id="outreach_user",
                session_id=approval_session_id,
                new_message=approval_response,
                invocation_id=approval_info["invocation_id"],
            ):
                pass  # Just consume events
            
            if user_decision:
                email_approved = True
                print_section("✅ EMAIL APPROVED")
                
                # Step 3: Send email
                print("📧 STEP 3: Sending Email\n")
                
                delivery_app = App(
                    name="email_delivery",
                    root_agent=final_delivery_agent,
                    resumability_config=ResumabilityConfig(is_resumable=False),
                )
                
                delivery_runner = Runner(
                    app=delivery_app,
                    session_service=session_service,
                )
                
                send_query = f"""Send this email:
                
TO: {lead_email}
SUBJECT: {email['subject']}
BODY: {email['body']}

Use send_email_mock to deliver it."""
                
                send_content = types.Content(
                    role="user", parts=[types.Part(text=send_query)]
                )
                
                delivery_session_id = f"delivery_{uuid.uuid4().hex[:8]}"
                await session_service.create_session(
                    app_name="email_delivery",
                    user_id="outreach_user",
                    session_id=delivery_session_id,
                )
                
                async for event in delivery_runner.run_async(
                    user_id="outreach_user",
                    session_id=delivery_session_id,
                    new_message=send_content,
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                print(f"✉️  {part.text}")
            else:
                print_section("❌ EMAIL REJECTED - Regenerating")
                if generation_attempt < MAX_ATTEMPTS:
                    print(f"Will regenerate... ({MAX_ATTEMPTS - generation_attempt} attempts remaining)\n")
                else:
                    print(f"❌ Maximum regeneration attempts reached ({MAX_ATTEMPTS})")
                    print("Please modify your input and try again.\n")
        else:
            print("⚠️  Approval request not detected. Check agent configuration.\n")
            break
    
    print_section("🎉 WORKFLOW COMPLETE")


async def get_user_approval_decision(
    email: dict, lead_name: str, attempt: int
) -> bool:
    """
    Get user approval decision via command line.
    In production, this would be a web UI with approve/reject buttons.
    
    Args:
        email: Dict with 'subject' and 'body'
        lead_name: Name of the lead
        attempt: Attempt number
        
    Returns:
        True to approve, False to reject
    """
    print("\n" + "=" * 80)
    print(f"🤔 HUMAN REVIEW (Attempt {attempt})")
    print("=" * 80)
    print("\nOptions:")
    print("  [A]pprove - Send this email")
    print("  [R]eject  - Regenerate with improvements")
    print("  [E]dit    - View full email again")
    print("  [Q]uit    - Exit workflow")
    print()
    
    while True:
        choice = input("Your decision (A/R/E/Q): ").strip().upper()
        
        if choice == "A":
            return True
        elif choice == "R":
            return False
        elif choice == "E":
            print("\n" + "─" * 80)
            print_email_preview(email)
            print()
        elif choice == "Q":
            print("\n❌ Workflow cancelled by user")
            exit(0)
        else:
            print("Invalid choice. Please enter A, R, E, or Q")


# ======================================================================================
# SECTION 6: Main Entry Point
# ======================================================================================

async def main():
    """Main entry point."""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                    HUMAN-IN-THE-LOOP LEAD OUTREACH AGENT                       ║
║                                                                                ║
║  This script demonstrates:                                                    ║
║  • Personalized lead research using Agent Tools                               ║
║  • AI-generated cold outreach emails                                          ║
║  • Human-in-the-loop approval workflow                                        ║
║  • Automatic regeneration on rejection                                        ║
║  • Mock email sending                                                         ║
║                                                                                ║
║  Workflow: Research → Generate → Approve/Reject → Regenerate (if needed) → Send
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Example workflow
    career_field = "AI/ML Engineer specializing in Agent Development"
    lead_name = "Susan Gatura"  # Change to any lead you want to research
    lead_email = "susan.gatura@example.com"  # Mock email for demonstration
    
    try:
        await run_lead_outreach_workflow(
            career_field=career_field,
            lead_name=lead_name,
            lead_email=lead_email,
        )
    except KeyboardInterrupt:
        print("\n\n❌ Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
