"""
Personalized Lead Research Agent
Converts the Jupyter notebook implementation to Django-compatible Python
Uses Google ADK (Agent Development Kit) for research and personalized email generation
Follows the Agent Tool pattern: Main agent orchestrates specialist agents
"""

import logging
import json
import asyncio
import os
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Load prompts from JSON file
def _load_prompts() -> Dict:
    """Load prompts from prompts.json file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, 'prompts.json')
    
    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"prompts.json not found at {prompts_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing prompts.json: {e}")
        raise

# Load prompts once at module level
_PROMPTS = _load_prompts()


def _initialize_adk():
    """Initialize ADK components for agent creation"""
    try:
        from google.adk.agents import LlmAgent
        from google.adk.models.google_llm import Gemini
        from google.adk.tools import google_search, AgentTool
        from google.genai import types
        
        # Configure retry options
        retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )
        
        # Section 1: Create ResearcherAgent (Specialist Agent with google_search tool)
        researcher_agent = LlmAgent(
            name="researcher_agent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=_PROMPTS["researcher_agent"]["instruction"],
            tools=[google_search],
        )
        
        logger.info("✅ Researcher agent initialized with google_search tool")
        
        # Section 2: Create MainOutreachAgent (Orchestrator with researcher_agent as tool)
        main_outreach_agent = LlmAgent(
            name="main_outreach_agent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=_PROMPTS["main_outreach_agent"]["instruction"],
            tools=[AgentTool(agent=researcher_agent)],
        )
        
        logger.info("✅ Main outreach agent initialized with researcher_agent as tool")
        
        return main_outreach_agent, retry_config
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize ADK: {str(e)}")
        raise


class PersonalizedLeadOutreachAgent:
    """
    Orchestrator agent that coordinates research and email generation
    Implements the Agent Tool pattern from the Jupyter notebook
    
    Pattern:
    - Main agent (PersonalizedLeadOutreachAgent) is the entry point
    - Main agent has ResearcherAgent as a tool via AgentTool
    - InMemoryRunner executes the main agent
    - Main agent orchestrates the workflow
    """
    
    def __init__(self, google_api_key: str):
        """
        Initialize the main orchestrator agent
        
        Args:
            google_api_key: Google Generative AI API key
        """
        self.google_api_key = google_api_key
        self.main_agent, self.retry_config = _initialize_adk()
        logger.info("✅ PersonalizedLeadOutreachAgent initialized")
    
    def process_contact(
        self,
        contact_name: str,
        contact_email: str,
        career_field: str,
        career_description: str,
        contact_type: str = 'emaillist',
        contact_context: Dict = None
    ) -> Dict:
        """
        Complete workflow: research contact
        
        This method follows the Agent Tool pattern:
        1. Run the main agent via InMemoryRunner
        2. Main agent uses researcher_agent as a tool to research the contact
        
        Args:
            contact_name: Name of the contact
            contact_email: Email of the contact
            career_field: Career field of the person doing outreach
            career_description: Career description
            contact_type: Type of contact - 'emaillist' (person) or 'company' (organization)
            contact_context: Optional dict with additional context
        
        Returns:
            research_summary dict with research findings
        """
        if contact_context is None:
            contact_context = {}
            
        try:
            logger.info(f"🚀 Starting workflow for {contact_name} ({contact_type})")
            print(f"\n🚀 PersonalizedLeadOutreachAgent: Starting workflow for {contact_name} ({contact_type})")
            
            # Build context string from contact_context dict
            context_str = ""
            if contact_context:
                context_str = "\n\nAdditional context about this contact:\n"
                for key, value in contact_context.items():
                    if value and value != 'Not specified':
                        readable_key = key.replace('_', ' ').title()
                        context_str += f"- {readable_key}: {value}\n"
            
            # Build the user prompt for the main agent
            # The main agent will use its tools (researcher_agent) to complete this task
            if contact_type == 'company':
                contact_type_str = "company/organization"
                context_guidance = _PROMPTS["context_guidance"]["company"]
            else:  # emaillist (person)
                contact_type_str = "individual professional"
                context_guidance = _PROMPTS["context_guidance"]["individual"]
            
            user_prompt = _PROMPTS["user_prompt_template"].format(
                contact_type=contact_type_str,
                contact_name=contact_name,
                contact_email=contact_email,
                career_field=career_field,
                career_description=career_description,
                context_guidance=context_guidance,
                context_str=context_str
            )
            
            # Run the main agent via InMemoryRunner with retries
            print(f"[→] Running main agent via InMemoryRunner...")
            
            max_retries = 3
            retry_delay = 2  # seconds
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    research_summary = asyncio.run(
                        self._run_agent(user_prompt)
                    )
                    
                    # Validate research results
                    if self._is_valid_research(research_summary):
                        logger.info(f"✅ Workflow completed for {contact_name}")
                        # Normalize and clean the research data
                        research_summary = self._normalize_research_data(research_summary)
                        return research_summary
                    else:
                        # Invalid research - treat as failure
                        raise ValueError("Research validation failed - returned invalid/default data")
                        
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        print(f"[⚠️] Research attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                        print(f"[→] Retrying in {retry_delay} seconds...")
                        logger.warning(f"Research attempt {attempt + 1}/{max_retries} failed, retrying...")
                        import time
                        time.sleep(retry_delay)
                    else:
                        # Max retries reached
                        error_msg = f"Research failed after {max_retries} attempts. Last error: {str(e)}"
                        logger.error(f"❌ {error_msg}")
                        print(f"[❌] {error_msg}")
                        raise ValueError(error_msg)
            
            # Should not reach here, but just in case
            raise ValueError(f"Research failed after {max_retries} attempts")
            
        except ValueError as ve:
            # Re-raise validation errors with clear message
            raise
        except Exception as e:
            logger.error(f"❌ Workflow failed for {contact_name}: {str(e)}")
            print(f"[❌] Workflow failed: {str(e)}")
            raise ValueError(f"Research failed: {str(e)}")
    
    async def _run_agent(self, user_prompt: str) -> Dict:
        """
        Run the main ADK agent asynchronously using InMemoryRunner
        
        Args:
            user_prompt: Prompt for the main agent
        
        Returns:
            research_data dict with research findings
        """
        from google.adk.runners import InMemoryRunner
        
        # Retry configuration for agent execution
        # Similar to retry_config but for the overall agent execution
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create runner for the main agent
                runner = InMemoryRunner(agent=self.main_agent)
                
                if attempt == 0:
                    print(f"[→] Agent executing workflow with tools...")
                else:
                    print(f"[→] Agent retry attempt {attempt}/{max_retries-1}...")
                
                logger.info(f"Starting agent execution with InMemoryRunner (attempt {attempt+1}/{max_retries})")
                
                # Run the main agent - it will orchestrate researcher_agent as a tool
                response = await runner.run_debug(user_prompt)
                
                print(f"[✓] Agent execution complete")
                print(f"    Response type: {type(response).__name__}")
                logger.debug(f"Raw response from runner: {response}")
                
                # Extract text from the last Event in the response list
                print(f"[→] Extracting text content from Event list...")
                response_text = self._extract_text_from_events(response)
                
                print(f"    Extracted text length: {len(response_text)}")
                print(f"    First 500 chars: {response_text[:500]}")
                logger.debug(f"Extracted response text: {response_text}")
                
                print(f"[→] Parsing response to extract research data...")
                
                # Parse the response to extract research data
                research_summary = self._parse_agent_response(response_text)
                
                print(f"[✓] Successfully parsed research data")
                
                return research_summary
                
            except RuntimeError as re:
                # Handle cases where agent response was incomplete/malformed
                # (e.g., only function_call parts, no final text)
                error_msg = str(re)
                
                if attempt < max_retries - 1:
                    # Retry on retriable errors
                    print(f"[⚠️] Retriable error on attempt {attempt+1}: {error_msg}")
                    logger.warning(
                        f"Retriable error on attempt {attempt+1}/{max_retries}: {error_msg}, "
                        f"will retry in {retry_delay}s"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Max retries reached
                    print(f"\n[❌] RuntimeError in _run_agent (attempt {attempt+1}/{max_retries}):")
                    print(f"    Message: {error_msg}")
                    logger.error(
                        f"RuntimeError in _run_agent after {attempt+1} attempts: {error_msg}"
                    )
                    logger.warning(f"Max retries reached for incomplete response in _run_agent")
                    print(f"[⚠️] Agent returned incomplete response after {max_retries} attempts in _run_agent")
                    raise RuntimeError(f"Agent execution failed: {error_msg}")
                
            except TypeError as te:
                # Handle ADK library error: 'NoneType' object is not iterable
                # This is a transient issue with the ADK library response parsing
                error_msg = str(te)
                
                # Check if it's the specific ADK error we know about
                is_adk_error = "'NoneType' object is not iterable" in error_msg
                
                if is_adk_error and attempt < max_retries - 1:
                    # Retry on ADK errors
                    print(f"[⚠️] ADK library error on attempt {attempt+1}, retrying...")
                    logger.warning(
                        f"ADK library NoneType error on attempt {attempt+1}/{max_retries}, "
                        f"will retry in {retry_delay}s"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Max retries reached or different error
                    print(f"\n[❌] TypeError in _run_agent (attempt {attempt+1}/{max_retries}):")
                    print(f"    Message: {error_msg}")
                    import traceback
                    logger.error(
                        f"TypeError in _run_agent after {attempt+1} attempts: {error_msg}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    
                    if is_adk_error:
                        logger.warning(f"Max retries reached for ADK library error in _run_agent")
                        print(f"[⚠️] Agent execution failed after {max_retries} attempts in _run_agent")
                        raise TypeError(f"ADK library error: {error_msg}")
                    else:
                        raise
            
            except Exception as e:
                # Non-retriable exceptions - don't retry, fail fast
                error_msg = str(e)
                error_type = type(e).__name__
                
                print(f"\n[❌] {error_type} caught in _run_agent:")
                print(f"    Message: {error_msg}")
                import traceback
                logger.error(
                    f"{error_type} in _run_agent: {error_msg}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                raise
        
        # Should not reach here, but just in case
        logger.error("Unexpected: exited retry loop without returning")
        raise RuntimeError("Unexpected: agent execution loop exited without result")
    
    def _extract_text_from_events(self, response) -> str:
        """
        Extract text content from the ADK Event list response.
        
        The response is a list of Event objects. We need to find the last Event
        that contains the final text output from the agent (not function calls).
        
        Args:
            response: List of Event objects from InMemoryRunner
        
        Returns:
            The text content from the final model response
            
        Raises:
            RuntimeError: When response contains only function_call parts (incomplete execution)
        """
        try:
            # Handle case where response is already a string
            if isinstance(response, str):
                return response
            
            # Response should be a list of Event objects
            if not isinstance(response, list):
                print(f"[⚠️] Response is not a list, trying to convert: {type(response)}")
                return str(response)
            
            print(f"[→] Processing Event list with {len(response)} events")
            print(f"\n[📋] FULL RESPONSE OBJECT DUMP:")
            print("="*100)
            
            # Dump full response structure
            for i, event in enumerate(response):
                print(f"\nEvent {i}:")
                print(f"  Type: {type(event).__name__}")
                print(f"  Author: {getattr(event, 'author', 'N/A')}")
                print(f"  Has content: {hasattr(event, 'content')}")
                
                if hasattr(event, 'content') and event.content:
                    print(f"  Content type: {type(event.content).__name__}")
                    print(f"  Has parts: {hasattr(event.content, 'parts')}")
                    
                    if hasattr(event.content, 'parts') and event.content.parts:
                        print(f"  Number of parts: {len(event.content.parts)}")
                        for j, part in enumerate(event.content.parts):
                            print(f"\n    Part {j}:")
                            print(f"      Type: {type(part).__name__}")
                            print(f"      Attributes: {dir(part)}")
                            
                            # Try to access different part types
                            if hasattr(part, 'text'):
                                text_val = part.text
                                if text_val:
                                    print(f"      Text (first 200 chars): {str(text_val)[:200]}")
                                else:
                                    print(f"      Text: None/Empty")
                            
                            if hasattr(part, 'function_call'):
                                fc = part.function_call
                                if fc:
                                    print(f"      Function call: {fc}")
                                    if hasattr(fc, 'name'):
                                        print(f"        Name: {fc.name}")
                                    if hasattr(fc, 'args'):
                                        print(f"        Args keys: {list(fc.args.keys()) if isinstance(fc.args, dict) else 'N/A'}")
                            
                            if hasattr(part, 'function_response'):
                                fr = part.function_response
                                if fr:
                                    print(f"      Function response: {type(fr).__name__}")
                    else:
                        print(f"  Parts: Empty or None")
                else:
                    print(f"  Content: None/Empty")
            
            print("\n" + "="*100)
            print(f"\nFULL RESPONSE AS STRING:\n{response}\n")
            print("="*100 + "\n")
            
            # Now do the actual extraction
            print(f"[→] Processing Event list with {len(response)} events (actual extraction)")
            
            # PRIORITY 1: Look for function_response with JSON data (most complete)
            print(f"[→] PRIORITY 1: Searching for function_response with structured data...")
            for i, event in enumerate(response):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            # Check if this is a function_response
                            if hasattr(part, 'function_response') and part.function_response:
                                fr = part.function_response
                                if hasattr(fr, 'response') and fr.response:
                                    response_data = fr.response
                                    
                                    # Check if response contains JSON
                                    if isinstance(response_data, dict) and 'result' in response_data:
                                        result = response_data['result']
                                        # The result might be a string containing JSON
                                        if isinstance(result, str) and result.strip().startswith('```json'):
                                            print(f"[✓] Found function_response with JSON result in Event {i}")
                                            # Extract JSON from code block
                                            json_start = result.find('{')
                                            json_end = result.rfind('}') + 1
                                            if json_start != -1 and json_end > json_start:
                                                json_str = result[json_start:json_end]
                                                try:
                                                    json_data = json.loads(json_str)
                                                    print(f"[✓] Successfully parsed JSON from function_response")
                                                    print(f"    JSON keys: {list(json_data.keys())}")
                                                    # Return as JSON string so _parse_agent_response can handle it
                                                    return json.dumps(json_data)
                                                except json.JSONDecodeError:
                                                    print(f"[⚠️] Failed to parse JSON from function_response")
                                                    pass
            
            # PRIORITY 2: Look through events in reverse order to find the last text output
            print(f"[→] PRIORITY 2: Searching for final text output...")
            found_text = False
            for i in range(len(response) - 1, -1, -1):
                event = response[i]
                print(f"    Event {i}: author={getattr(event, 'author', '?')}, has content={hasattr(event, 'content')}")
                
                # Check if this event has text content
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            # Look for text parts (not function_call or function_response)
                            if hasattr(part, 'text') and part.text:
                                print(f"[✓] Found text in Event {i}")
                                found_text = True
                                return part.text
            
            # Check if we found only function_call parts (agent executed tool but no final text)
            response_str = str(response)
            if 'function_call' in response_str and not found_text:
                print(f"[⚠️] Response contains only function_call parts (agent executed tool but returned no final text)")
                print(f"[⚠️] This is a retriable condition - will trigger retry")
                raise RuntimeError("Agent executed tool but returned no final text - incomplete response")
            
            # If no text found and no function_call, fallback to stringifying
            print(f"[⚠️] No text content found in Event list, falling back to string conversion")
            return str(response)
            
        except RuntimeError:
            # Re-raise retriable errors so retry loop catches them
            raise
        except Exception as e:
            print(f"[❌] Error extracting text from events: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error in _extract_text_from_events: {str(e)}\n{traceback.format_exc()}")
            return str(response)
    
    def _extract_research_and_email_text(self, response_text: str) -> Tuple[str, str]:
        """
        Extract raw research and email text from agent response
        
        Looks for the pattern:
        main_outreach_agent > RESEARCH:
        [research content]
        
        EMAIL:
        [email JSON]
        
        Args:
            response_text: The agent's complete response text
        
        Returns:
            Tuple of (research_text, email_text) as strings
        """
        research_text = ""
        email_text = ""
        
        # Find RESEARCH: marker
        if "RESEARCH:" in response_text:
            research_start = response_text.find("RESEARCH:") + len("RESEARCH:")
            
            # Find EMAIL: marker
            if "EMAIL:" in response_text:
                email_start = response_text.find("EMAIL:")
                research_text = response_text[research_start:email_start].strip()
                email_text = response_text[email_start + len("EMAIL:"):].strip()
            else:
                # No EMAIL marker, treat rest as research
                research_text = response_text[research_start:].strip()
                email_text = ""
        else:
            # No RESEARCH marker, fallback
            research_text = response_text
            email_text = ""
        
        return research_text, email_text
    
    def _parse_agent_response(self, response_text: str) -> Dict:
        """
        Parse the main agent's response.
        
        Flexible parsing that handles:
        1. RESEARCH_DATA: [plain text]
        2. {"research_data": "[text]"} (JSON)
        3. Plain text (no marker) - just use it directly if it looks like research
        
        Args:
            response_text: The agent's complete response text
        
        Returns:
            research_summary dict with research findings
        """
        try:
            # Log incoming response for debugging
            print(f"\n[→] Parsing agent response...")
            print(f"    Response type: {type(response_text).__name__}")
            print(f"    Response length: {len(str(response_text))} chars")
            print(f"    First 500 chars: {str(response_text)[:500]}")
            
            logger.debug(f"Full response text:\n{response_text}")
            
            research_text = None
            
            # Try to parse as JSON first (fallback format)
            if response_text.strip().startswith('{'):
                try:
                    print(f"[→] Attempting to parse response as JSON...")
                    response_json = json.loads(response_text)
                    
                    # Check if it's a complete research data dict from function_response
                    if isinstance(response_json, dict) and 'professional_background' in response_json:
                        print(f"[✓] Found complete research data dict with all fields")
                        print(f"    Keys: {list(response_json.keys())}")
                        # This is the full structured research data - normalize before returning
                        return self._normalize_research_data(response_json)
                    
                    # Look for research_data field in JSON
                    if isinstance(response_json, dict) and 'research_data' in response_json:
                        research_text = response_json['research_data']
                        print(f"[✓] Found research_data in JSON response")
                    elif isinstance(response_json, dict) and 'notable_connections' in response_json:
                        # Already parsed as research dict - normalize before returning
                        print(f"[✓] Response is already a research data dict")
                        return self._normalize_research_data(response_json)
                except json.JSONDecodeError:
                    print(f"[⚠️] JSON parsing failed, trying text format...")
                    research_text = None
            
            # Try to parse text format (RESEARCH_DATA: marker)
            if not research_text:
                marker = None
                if "RESEARCH_DATA:" in response_text:
                    marker = "RESEARCH_DATA:"
                    print(f"[✓] Found RESEARCH_DATA marker")
                elif "RESEARCH:" in response_text:
                    marker = "RESEARCH:"
                    print(f"[✓] Found RESEARCH marker (legacy format)")
                
                if marker:
                    research_start = response_text.find(marker) + len(marker)
                    
                    # Find next section marker if it exists (otherwise take rest of response)
                    next_marker = -1
                    for search_marker in ["EMAIL_JSON:", "EMAIL:", "---", "\n\n"]:
                        pos = response_text.find(search_marker, research_start)
                        if pos != -1 and (next_marker == -1 or pos < next_marker):
                            next_marker = pos
                    
                    if next_marker != -1:
                        research_text = response_text[research_start:next_marker].strip()
                        print(f"[✓] Found next marker at position {next_marker}, extracted {len(research_text)} chars")
                    else:
                        research_text = response_text[research_start:].strip()
                        print(f"[✓] No next marker found, extracted {len(research_text)} chars from start")
            
            # If still no research text, treat the entire response as research (plain text fallback)
            if not research_text:
                # The agent might have returned plain text research without markers
                # Check if response looks like research (not JSON, not Event repr)
                response_stripped = response_text.strip()
                
                # If it starts with [Event (repr of Event list), that's not usable
                if response_stripped.startswith('[Event('):
                    print(f"[⚠️] Response is Event list repr, cannot extract research")
                    logger.warning(f"Response is Event list repr, no research text available")
                    raise ValueError("Response format invalid: Event list repr cannot be parsed")
                
                # Otherwise, treat the entire response as research text
                if len(response_stripped) > 50:  # Must be substantial text
                    print(f"[✓] No markers found, using entire response as research text (plain text format)")
                    research_text = response_stripped
                else:
                    print(f"[⚠️] Response text too short to be research: {len(response_stripped)} chars")
                    logger.warning(f"Response text insufficient for research")
                    raise ValueError(f"Response text too short to be valid research: {len(response_stripped)} chars")
            
            if not research_text:
                print(f"[⚠️] Research text is empty after all extraction attempts")
                logger.warning(f"Research text empty after all extraction attempts")
                raise ValueError("Research text is empty after all extraction attempts")
            
            # Research: plain text narrative
            # Create minimal structure - notable_connections will contain the research text
            research_data = {
                "name": "",
                "current_role": "",
                "company": "",
                "professional_background": [],
                "social_media": {
                    "linkedin": "",
                    "twitter": "",
                    "github": ""
                },
                "recent_achievements": [],
                "industry_focus": "",
                "notable_connections": research_text if research_text else ""
            }
            
            print(f"[✓] Successfully created research_data dict with {len(research_text)} chars of research")
            return self._normalize_research_data(research_data)
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            print(f"\n[❌] Exception caught in _parse_agent_response:")
            print(f"    Type: {error_type}")
            print(f"    Message: {error_msg}")
            print(f"    Full traceback:")
            import traceback
            traceback.print_exc()
            
            logger.error(
                f"Exception in _parse_agent_response: {error_type}\n"
                f"Message: {error_msg}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            print(f"[⚠️] Error parsing response")
            raise ValueError(f"Error parsing agent response: {error_msg}")
    

    def _is_valid_research(self, research_data: Dict) -> bool:
        """
        Check if research data is valid (not default/incomplete structure)
        
        Args:
            research_data: Research data dict to validate
        
        Returns:
            True if research appears valid, False if it's default/incomplete
        """
        if not research_data or not isinstance(research_data, dict):
            return False
        
        # Check if it matches the default/incomplete structure
        name = research_data.get('name', '')
        current_role = research_data.get('current_role', '')
        company = research_data.get('company', '')
        
        # Invalid if all key fields are empty or match default values
        invalid_indicators = [
            'Research Incomplete', 'Unknown', 'N/A', 
            'Research Completed', 'Based on research', 'Research available'
        ]
        
        if (name in invalid_indicators or 
            current_role in invalid_indicators or 
            company in invalid_indicators):
            return False
        
        # Valid if at least one key field has meaningful content
        if (name and name not in invalid_indicators) or \
           (current_role and current_role not in invalid_indicators) or \
           (company and company not in invalid_indicators):
            return True
        
        # Check if notable_connections has meaningful content
        notable = research_data.get('notable_connections', '')
        if notable and len(notable.strip()) > 50:
            return True
        
        return False
    
    def _normalize_social_media_url(self, url: str) -> str:
        """
        Normalize and validate social media URL
        Returns empty string if not a valid URL
        
        Args:
            url: URL string to normalize
        
        Returns:
            Valid URL string or empty string
        """
        if not url or not isinstance(url, str):
            return ""
        
        url = url.strip()
        
        # Return empty if it's a placeholder or description
        invalid_values = ['Unknown', 'N/A', 'Not found', 'Not available', 
                         'url or description', 'description', '']
        if url.lower() in [v.lower() for v in invalid_values]:
            return ""
        
        # Check if it's a valid URL (starts with http:// or https://)
        if url.startswith(('http://', 'https://')):
            return url
        
        # Return empty string for invalid/non-URL values
        return ""
    
    def _normalize_research_data(self, research_data: Dict) -> Dict:
        """
        Normalize research data: ensure all fields use empty strings instead of placeholders
        and validate social media URLs
        
        Args:
            research_data: Raw research data dict
        
        Returns:
            Normalized research data dict
        """
        if not research_data:
            return self._default_research()
        
        # Normalize string fields - replace invalid placeholders with empty strings
        invalid_placeholders = ['Unknown', 'N/A', 'Not found', 'Not available', 
                               'Research Incomplete', 'Based on research', 
                               'Research available', 'See research summary',
                               'Research Completed']
        
        normalized = {}
        
        # Normalize name
        name = research_data.get('name', '')
        if isinstance(name, str):
            normalized['name'] = '' if name in invalid_placeholders else name.strip()
        else:
            normalized['name'] = ''
        
        # Normalize current_role
        current_role = research_data.get('current_role', '')
        if isinstance(current_role, str):
            normalized['current_role'] = '' if current_role in invalid_placeholders else current_role.strip()
        else:
            normalized['current_role'] = ''
        
        # Normalize company
        company = research_data.get('company', '')
        if isinstance(company, str):
            normalized['company'] = '' if company in invalid_placeholders else company.strip()
        else:
            normalized['company'] = ''
        
        # Normalize industry_focus
        industry_focus = research_data.get('industry_focus', '')
        if isinstance(industry_focus, str):
            normalized['industry_focus'] = '' if industry_focus in invalid_placeholders else industry_focus.strip()
        else:
            normalized['industry_focus'] = ''
        
        # Normalize notable_connections
        notable_connections = research_data.get('notable_connections', '')
        if isinstance(notable_connections, str):
            normalized['notable_connections'] = notable_connections.strip()
        else:
            normalized['notable_connections'] = ''
        
        # Normalize professional_background (must be array)
        professional_background = research_data.get('professional_background', [])
        if isinstance(professional_background, list):
            # Filter out invalid entries
            normalized['professional_background'] = [
                str(item).strip() for item in professional_background 
                if item and str(item).strip() and str(item).strip() not in invalid_placeholders
            ]
        else:
            normalized['professional_background'] = []
        
        # Normalize recent_achievements (must be array)
        recent_achievements = research_data.get('recent_achievements', [])
        if isinstance(recent_achievements, list):
            normalized['recent_achievements'] = [
                str(item).strip() for item in recent_achievements 
                if item and str(item).strip() and str(item).strip() not in invalid_placeholders
            ]
        else:
            normalized['recent_achievements'] = []
        
        # Normalize social_media - must be dict with URL-only values
        social_media = research_data.get('social_media', {})
        if isinstance(social_media, dict):
            normalized['social_media'] = {}
            for platform in ['linkedin', 'twitter', 'github']:
                url = social_media.get(platform, '')
                normalized['social_media'][platform] = self._normalize_social_media_url(url)
        else:
            normalized['social_media'] = {}
        
        return normalized
    
    def _default_research(self) -> Dict:
        """Return default research structure with empty strings"""
        return {
            "name": "",
            "current_role": "",
            "company": "",
            "professional_background": [],
            "social_media": {
                "linkedin": "",
                "twitter": "",
                "github": ""
            },
            "recent_achievements": [],
            "industry_focus": "",
            "notable_connections": ""
        }

