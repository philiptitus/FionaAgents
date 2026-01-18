"""
Cloud Run / Cloud Functions entry point for PersonalizedLeadOutreachAgent
Handles HTTP requests and processes contact research requests
"""

import os
import json
import functions_framework
from flask import Request, make_response
from personalized_outreach import PersonalizedLeadOutreachAgent

# Initialize the agent at module level (singleton pattern)
# This ensures the agent is only created once when the Cloud Run instance starts
_agent = None

def get_agent():
    """Get or create the agent instance (singleton)"""
    global _agent
    if _agent is None:
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        if not google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Please set it in Cloud Run environment variables."
            )
        _agent = PersonalizedLeadOutreachAgent(google_api_key)
    return _agent


@functions_framework.http
def hello_http(request: Request):
    """
    HTTP Cloud Function / Cloud Run handler for PersonalizedLeadOutreachAgent
    
    Expected JSON request body:
    {
        "contact_name": "Name",
        "contact_email": "email@domain.com", 
        "career_field": "Your field",
        "career_description": "Your description",
        "contact_type": "emaillist|company" (optional, default: "emaillist"),
        "contact_context": {...} (optional)
    }
    
    Args:
        request (flask.Request): The request object.
    
    Returns:
        JSON response with research results or error message
    """
    # Set CORS headers for browser requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Only allow POST requests
    if request.method != 'POST':
        headers = {'Access-Control-Allow-Origin': '*'}
        return make_response(
            {'error': 'Method not allowed. Please use POST.'}, 
            405, 
            headers
        )
    
    try:
        # Get JSON from request body
        request_json = request.get_json(silent=True)
        
        if not request_json:
            # Try to get from query parameters as fallback
            request_args = request.args
            if request_args and 'data' in request_args:
                try:
                    request_json = json.loads(request_args['data'])
                except json.JSONDecodeError:
                    pass
        
        if not request_json:
            headers = {'Access-Control-Allow-Origin': '*'}
            return make_response(
                {'error': 'No JSON data provided. Please send a JSON request body.'}, 
                400, 
                headers
            )
        
        # Validate required fields
        required_fields = ['contact_name', 'contact_email', 'career_field', 'career_description']
        missing_fields = [field for field in required_fields if field not in request_json]
        
        if missing_fields:
            headers = {'Access-Control-Allow-Origin': '*'}
            return make_response(
                {
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'required_fields': required_fields
                }, 
                400, 
                headers
            )
        
        # Get agent instance
        agent = get_agent()
        
        # Extract parameters
        contact_name = request_json['contact_name']
        contact_email = request_json['contact_email']
        career_field = request_json['career_field']
        career_description = request_json['career_description']
        contact_type = request_json.get('contact_type', 'emaillist')
        contact_context = request_json.get('contact_context', {})
        
        # Process the contact through the agent
        result = agent.process_contact(
            contact_name=contact_name,
            contact_email=contact_email,
            career_field=career_field,
            career_description=career_description,
            contact_type=contact_type,
            contact_context=contact_context
        )
        
        # Return successful response with CORS headers
        headers = {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'}
        return make_response(
            {
                'success': True,
                'contact_name': contact_name,
                'contact_email': contact_email,
                'research': result
            }, 
            200, 
            headers
        )
        
    except ValueError as ve:
        # Handle missing API key or other value errors
        headers = {'Access-Control-Allow-Origin': '*'}
        return make_response(
            {'error': f'Configuration error: {str(ve)}'}, 
            500, 
            headers
        )
    except json.JSONDecodeError:
        headers = {'Access-Control-Allow-Origin': '*'}
        return make_response(
            {'error': 'Invalid JSON format in request body'}, 
            400, 
            headers
        )
    except Exception as e:
        # Handle any other unexpected errors
        error_message = str(e)
        headers = {'Access-Control-Allow-Origin': '*'}
        return make_response(
            {
                'error': 'An error occurred while processing your request',
                'details': error_message
            }, 
            500, 
            headers
        )

