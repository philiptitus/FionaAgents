"""
ADK Web Interface for PersonalizedLeadOutreachAgent
This file exposes the root_agent that ADK web command expects.
"""

import os
import json
from dotenv import load_dotenv
from .personalized_outreach import PersonalizedLeadOutreachAgent

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please add it to your .env file.")

# Create the wrapper instance to get access to the internal ADK agent
# ADK expects the root_agent to be an actual BaseAgent (LlmAgent), not our wrapper
try:
    agent_wrapper = PersonalizedLeadOutreachAgent(google_api_key)
    # Expose the internal main_agent (which is the actual ADK LlmAgent) as root_agent
    root_agent = agent_wrapper.main_agent
    print(f"✅ root_agent (ADK LlmAgent) initialized successfully for ADK web interface")
except Exception as e:
    print(f"❌ Failed to initialize root_agent: {str(e)}")
    raise


# Chat interface function for handling JSON input
def process_json_input(user_input: str) -> str:
    """
    Process JSON input from ADK web chat interface
    
    Expected JSON format:
    {
        "contact_name": "Name",
        "contact_email": "email@domain.com", 
        "career_field": "Your field",
        "career_description": "Your description",
        "contact_type": "emaillist|company",
        "contact_context": {...}
    }
    """
    try:
        # Try to parse as JSON
        if user_input.strip().startswith('{'):
            data = json.loads(user_input)
            
            # Validate required fields
            required_fields = ['contact_name', 'contact_email', 'career_field', 'career_description']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return f"❌ Missing required fields: {', '.join(missing_fields)}\n\nRequired fields: {required_fields}"
            
            # Call the research agent
            result = root_agent.process_contact(
                contact_name=data['contact_name'],
                contact_email=data['contact_email'],
                career_field=data['career_field'], 
                career_description=data['career_description'],
                contact_type=data.get('contact_type', 'emaillist'),
                contact_context=data.get('contact_context', {})
            )
            
            # Format result for display
            return format_research_result(result, data['contact_name'])
            
        else:
            return get_usage_help()
            
    except json.JSONDecodeError:
        return f"❌ Invalid JSON format. Please provide valid JSON input.\n\n{get_usage_help()}"
    except Exception as e:
        return f"❌ Error processing request: {str(e)}\n\n{get_usage_help()}"


def format_research_result(result: dict, contact_name: str) -> str:
    """Format research results for display"""
    output = f"🔍 **Research Results for {contact_name}**\n"
    output += "=" * 50 + "\n\n"
    
    output += f"**Name:** {result.get('name', 'N/A')}\n"
    output += f"**Current Role:** {result.get('current_role', 'N/A')}\n" 
    output += f"**Company:** {result.get('company', 'N/A')}\n"
    output += f"**Industry Focus:** {result.get('industry_focus', 'N/A')}\n\n"
    
    # Professional background
    bg = result.get('professional_background', [])
    if bg and isinstance(bg, list):
        output += "**Professional Background:**\n"
        for item in bg:
            output += f"• {item}\n"
        output += "\n"
    
    # Recent achievements
    achievements = result.get('recent_achievements', [])
    if achievements and isinstance(achievements, list):
        output += "**Recent Achievements:**\n"
        for item in achievements:
            output += f"• {item}\n"
        output += "\n"
    
    # Social media
    social = result.get('social_media', {})
    if social and isinstance(social, dict):
        output += "**Social Media:**\n"
        for platform, info in social.items():
            if info:
                output += f"• {platform.title()}: {info}\n"
        output += "\n"
    
    # Research summary
    connections = result.get('notable_connections', '')
    if connections and len(connections) > 10:
        output += f"**Research Summary:**\n{connections}\n\n"
    
    output += "=" * 50
    return output


def get_usage_help() -> str:
    """Return usage instructions"""
    return """
📖 **Usage Instructions for PersonalizedLeadOutreachAgent**

**Paste JSON input in this format:**

**For researching a person:**
```json
{
  "contact_name": "Satya Nadella",
  "contact_email": "satya@microsoft.com", 
  "career_field": "Software Development",
  "career_description": "Senior Python developer specializing in AI solutions",
  "contact_type": "emaillist"
}
```

**For researching a company:**
```json
{
  "contact_name": "OpenAI",
  "contact_email": "partnerships@openai.com",
  "career_field": "Business Development", 
  "career_description": "B2B partnerships specialist focusing on AI solutions",
  "contact_type": "company"
}
```

**With additional context:**
```json
{
  "contact_name": "Jensen Huang",
  "contact_email": "jensen@nvidia.com",
  "career_field": "AI Engineering", 
  "career_description": "ML engineer focused on computer vision",
  "contact_type": "emaillist",
  "contact_context": {
    "company": "NVIDIA",
    "industry": "semiconductors", 
    "recent_project": "AI chip development"
  }
}
```

**Required fields:**
- contact_name, contact_email, career_field, career_description

**Optional fields:**
- contact_type: "emaillist" (person) or "company" (default: "emaillist")
- contact_context: Additional info as key-value pairs
    """