# Personalized Lead Outreach Agent - API Documentation

## Overview

The Personalized Lead Outreach Agent is a Cloud Run service that performs comprehensive research on business contacts (individuals or companies) using Google's Agent Development Kit (ADK). The agent gathers detailed intelligence including professional background, current role, company information, social media presence, recent achievements, and industry expertise.

## Base URL

For Cloud Run deployment, use your Cloud Run service URL:
```
https://your-service-name-xxxxx.run.app
```

For local testing:
```
http://localhost:8080
```

## Endpoint

**POST** `/` (base route only - no additional paths)

## Request Format

All requests must be **POST** requests with a JSON body.

### Headers

```
Content-Type: application/json
```

---

## Request Fields

### Required Fields

These fields **MUST** be included in every request:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `contact_name` | string | Name of the contact or company to research | `"Satya Nadella"` or `"OpenAI"` |
| `contact_email` | string | Email address of the contact | `"satya@microsoft.com"` |
| `career_field` | string | Career field/industry of the person doing the outreach | `"Software Development"` |
| `career_description` | string | Description of expertise/specialization of the person doing outreach | `"Senior Python developer specializing in AI solutions"` |

### Optional Fields

These fields can be omitted or left empty:

| Field | Type | Default | Description | Valid Values |
|-------|------|---------|-------------|--------------|
| `contact_type` | string | `"emaillist"` | Type of contact being researched | `"emaillist"` (individual person) or `"company"` (organization) |
| `contact_context` | object | `{}` | Additional context information as key-value pairs | Any object with string keys and values |

### Contact Context Fields

The `contact_context` field accepts any key-value pairs. Common fields include:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `location` | string | Geographic location of the contact/company | `"Seattle, Washington"` |
| `company` | string | Company name (if researching a person) | `"Microsoft Corporation"` |
| `industry` | string | Industry sector | `"Technology"` or `"semiconductors"` |
| `recent_project` | string | Recent projects or initiatives | `"AI chip development"` |
| `website` | string | Company or personal website URL | `"https://www.microsoft.com"` |
| `linkedin` | string | LinkedIn profile URL | `"https://linkedin.com/in/satyanadella"` |

**Note:** You can include any additional fields in `contact_context` - these will be passed to the research agent to provide context for more accurate research.

---

## Contact Types

The service supports two types of contacts:

### 1. Individual Professional (`contact_type: "emaillist"`)

For researching individual people/professionals. The agent focuses on:
- Professional background and career history
- Current role, responsibilities, and company
- Social media presence (LinkedIn, Twitter, GitHub, personal website)
- Expertise areas and industry involvement
- Recent achievements, projects, publications, awards
- Professional network and notable connections

### 2. Company/Organization (`contact_type: "company"`)

For researching companies or organizations. The agent focuses on:
- Company overview (industry, business model, size, location)
- Products and services, value proposition
- Recent news, developments, funding, partnerships
- Leadership and team structure
- Market position, competitive advantages, growth
- Website and online presence

---

## JSON Examples

### Example 1: Research Individual Professional (Minimal)

Basic request with only required fields:

```json
{
  "contact_name": "Satya Nadella",
  "contact_email": "satya@microsoft.com",
  "career_field": "Software Development",
  "career_description": "Senior Python developer specializing in AI solutions"
}
```

### Example 2: Research Individual Professional (With Context)

Individual research with additional context information:

```json
{
  "contact_name": "Jensen Huang",
  "contact_email": "jensen@nvidia.com",
  "career_field": "AI Engineering",
  "career_description": "ML engineer focused on computer vision",
  "contact_type": "emaillist",
  "contact_context": {
    "company": "NVIDIA",
    "location": "Santa Clara, California",
    "industry": "semiconductors",
    "recent_project": "AI chip development"
  }
}
```

### Example 3: Research Company/Organization

Company research request:

```json
{
  "contact_name": "OpenAI",
  "contact_email": "partnerships@openai.com",
  "career_field": "Business Development",
  "career_description": "B2B partnerships specialist focusing on AI solutions",
  "contact_type": "company",
  "contact_context": {
    "location": "San Francisco, California",
    "industry": "Artificial Intelligence",
    "website": "https://openai.com"
  }
}
```

### Example 4: Research Individual with Full Context

Comprehensive individual research with extensive context:

```json
{
  "contact_name": "Tim Cook",
  "contact_email": "tcook@apple.com",
  "career_field": "Technology Sales",
  "career_description": "Enterprise sales specialist in mobile technology solutions",
  "contact_type": "emaillist",
  "contact_context": {
    "company": "Apple Inc.",
    "location": "Cupertino, California",
    "industry": "Consumer Electronics",
    "linkedin": "https://linkedin.com/in/tim-cook",
    "recent_project": "Supply chain sustainability initiatives"
  }
}
```

### Example 5: Research Company with Full Context

Comprehensive company research with detailed context:

```json
{
  "contact_name": "Tesla",
  "contact_email": "info@tesla.com",
  "career_field": "Electric Vehicle Technology",
  "career_description": "EV technology consultant specializing in battery systems",
  "contact_type": "company",
  "contact_context": {
    "location": "Austin, Texas",
    "industry": "Automotive & Energy",
    "website": "https://tesla.com",
    "recent_project": "Cybertruck production ramp-up"
  }
}
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "contact_name": "Satya Nadella",
  "contact_email": "satya@microsoft.com",
  "research": {
    "name": "Research Completed",
    "current_role": "Based on research",
    "company": "Research available",
    "professional_background": [
      "Research summary point 1",
      "Research summary point 2"
    ],
    "social_media": {
      "linkedin": "URL or description",
      "twitter": "URL or description",
      "github": "URL or description"
    },
    "recent_achievements": [
      "Achievement 1",
      "Achievement 2"
    ],
    "industry_focus": "Industry and expertise areas",
    "notable_connections": "Detailed research narrative with key information about the contact's background, current role, company, achievements, and expertise (2-3 paragraphs)"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if the request was successful |
| `contact_name` | string | The name that was researched (echoed back) |
| `contact_email` | string | The email that was researched (echoed back) |
| `research` | object | Research findings object |
| `research.name` | string | Name from research results |
| `research.current_role` | string | Current job title/role |
| `research.company` | string | Company name |
| `research.professional_background` | array | List of professional background points |
| `research.social_media` | object | Social media presence (LinkedIn, Twitter, GitHub, etc.) |
| `research.recent_achievements` | array | List of recent achievements, projects, awards |
| `research.industry_focus` | string | Industry focus and expertise areas |
| `research.notable_connections` | string | Comprehensive research narrative (2-3 paragraphs) |

### Error Responses

#### 400 Bad Request - Missing Required Fields

```json
{
  "error": "Missing required fields: contact_name, contact_email",
  "required_fields": [
    "contact_name",
    "contact_email",
    "career_field",
    "career_description"
  ]
}
```

#### 400 Bad Request - Invalid JSON

```json
{
  "error": "Invalid JSON format in request body"
}
```

#### 400 Bad Request - No JSON Data

```json
{
  "error": "No JSON data provided. Please send a JSON request body."
}
```

#### 405 Method Not Allowed

```json
{
  "error": "Method not allowed. Please use POST."
}
```

#### 500 Internal Server Error - Configuration Error

```json
{
  "error": "Configuration error: GOOGLE_API_KEY environment variable not set. Please set it in Cloud Run environment variables."
}
```

#### 500 Internal Server Error - General Error

```json
{
  "error": "An error occurred while processing your request",
  "details": "Error details here"
}
```

---

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) for browser-based requests. All responses include appropriate CORS headers:

```
Access-Control-Allow-Origin: *
```

---

## Field Requirements Summary

### ✅ Required Fields (Must Have Values)

- `contact_name` - **Cannot be empty**
- `contact_email` - **Cannot be empty**
- `career_field` - **Cannot be empty**
- `career_description` - **Cannot be empty**

### ⚪ Optional Fields (Can Be Omitted or Empty)

- `contact_type` - Defaults to `"emaillist"` if not provided
- `contact_context` - Defaults to `{}` if not provided (empty object is allowed)

### Contact Context Notes

- `contact_context` can be an empty object `{}`
- Any key-value pairs can be included in `contact_context`
- Values in `contact_context` that are `"Not specified"` or empty strings are automatically filtered out
- Common fields include: `location`, `company`, `industry`, `recent_project`, `website`, `linkedin`

---

## Usage Tips

1. **Individual vs Company**: Use `"contact_type": "emaillist"` for people and `"contact_type": "company"` for organizations. The research focus changes based on this field.

2. **Provide Context**: The more context you provide in `contact_context`, the more accurate and targeted the research will be.

3. **Location Matters**: Including `location` in `contact_context` can help the agent find more relevant information, especially for companies.

4. **Email Format**: While `contact_email` is required, it's primarily used for context. The agent researches based on `contact_name` and `contact_context`.

5. **Response Time**: Research requests may take 10-30 seconds depending on the complexity and availability of information online.

---

## Testing with Postman

1. **Method**: POST
2. **URL**: Your Cloud Run service URL (base route only)
3. **Headers**: 
   - `Content-Type: application/json`
4. **Body**: Select "raw" and "JSON", then paste one of the JSON examples above
5. **Send**: Click "Send" to receive the research results

---

## Notes

- The service uses Google ADK (Agent Development Kit) with Gemini models
- Research is performed using Google Search capabilities
- The agent uses retry logic (up to 3 attempts) for reliability
- All responses are returned in JSON format
- The service is stateless - each request is independent

## Command to run with agent framework when in same directory as main.py
- functions-framework --target=hello_http --source=main.py --port=8080