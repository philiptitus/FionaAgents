# Agent Development Kit (ADK) Agents for Fiona

A collection of intelligent agent workflows built with Google's Agent Development Kit (ADK) to enhance email campaign targeting and outreach automation for **Fiona**.

## What is Fiona?

Fiona is a platform designed to simplify email campaign management and communications. It enables users to create, manage, and track email campaigns with clear analytics and contact organization—all without requiring technical expertise. Learn more at [fiona.mrphilip.cv](https://fiona.mrphilip.cv).

## The Agent Ecosystem

These agents extend Fiona's capabilities by automating intelligent research, problem discovery, and personalized outreach generation. They power the next generation of Fiona's targeting and campaign automation features.

### Agents Overview

#### 1. Career-Targeted Cold Outreach (Sequential Agents)
**File:** `career-outreach-sequential-agents.ipynb`

This workflow combines three specialized agents in a strict sequence:
- **Problem Finder Agent** - Identifies industry-specific challenges
- **Problem Solver Agent** - Maps how your career skills address those problems
- **Cold Outreach Message Agent** - Generates personalized LinkedIn messages

**How it fits Fiona:** When users want to launch targeted cold email campaigns, this agent automatically discovers relevant problems their audience faces and generates customized email templates. Users simply input their career and target industry, and the agent creates ready-to-send message templates directly compatible with Fiona's campaign creation system.

**Integration:** Output can be imported into Fiona as email templates or bulk contact lists with pre-generated subject lines.

---

#### 2. Multi-Channel Research & Email Generation (Parallel Agents)
**File:** `parallel-cold-email-outreach.ipynb`

This workflow runs three research agents simultaneously, then synthesizes findings:
- **Reddit Research Agent** - Gathers cold outreach tactics from discussions
- **Quora Research Agent** - Collects expert best practices
- **Freelance Niche Agent** - Identifies service opportunities
- **Email Aggregator Agent** - Creates 3-4 tailored email templates

**How it fits Fiona:** Speed is critical in email campaigns. By running research in parallel, this agent dramatically reduces analysis time. Users provide their career field once, and within seconds receive multiple email templates ready for use. This accelerates Fiona's campaign creation workflow.

**Integration:** Generated email templates integrate directly into Fiona's template library. The parallel execution model allows Fiona to offer near-instant email suggestions without user wait times.

---

#### 3. Personalized Lead Outreach (Agent Tools Pattern)
**File:** `personalized-lead-outreach.ipynb`

This notebook demonstrates the Agent Tools pattern where agents are used as tools within other agents:
- **Researcher Agent** - Conducts comprehensive lead research using Google Search
- **Main Outreach Agent** - Uses researcher as a tool to gather intelligence, then generates personalized emails

**Features:**
- Multi-step research gathering (role, company, background, social presence, achievements)
- Research-backed email personalization
- Clear separation of concerns (specialist agents)
- Reusable researcher agent for other workflows
- Simple two-variable input (career field + lead name)

**How it fits Fiona:** This demonstrates how agents can specialize and delegate work. Users input a lead name and career field, the researcher agent gathers intelligence, and the main agent produces highly personalized outreach emails ready for Fiona campaigns.

**Integration:** Generated emails can be imported directly into Fiona's template library or used as starting points for bulk campaigns.

---

#### 4. Iterative Problem Refinement (Loop Agents)
**File:** `loop-agent-problem-refinement.ipynb`

This workflow discovers and refines problems through iterative passes:
- **Problem Finder Agent** - Discovers 10-15 initial problems
- **Critic Agent** (Loop) - Iteratively eliminates weak/non-existent problems (up to 3 passes)
- **Final Output Agent** - Formats each problem as a one-sentence statement

**How it fits Fiona:** Quality of email lists matters. This agent validates that discovered problems are real and substantial, ensuring Fiona users build campaigns targeting genuine, location-specific opportunities. The loop refinement ensures data accuracy across multiple iterations.

**Integration:** Refined problem lists become targeting criteria in Fiona. Users can segment contact lists based on validated industry problems, improving campaign relevance and conversion rates.

---

#### 5. Human-in-the-Loop Lead Outreach (Approval & Regeneration)
**File:** `human_in_loop_lead_outreach.py` (Standalone Script)

This production-ready workflow implements intelligent lead research with human approval and AI regeneration:
- **Researcher Agent** - Conducts comprehensive lead research using Google Search
- **Outreach Agent** - Generates personalized cold outreach emails
- **Approval Agent** - Submits emails for human review (pausable workflow)
- **Delivery Agent** - Sends approved emails or triggers regeneration

**Features:**
-  Personalized lead research (company, role, achievements, social presence)
-  AI-generated customized emails (subject + body)
-  Human-in-the-loop approval workflow (approve/reject/edit/regenerate)
-  Automatic regeneration on rejection (up to 3 attempts)
-  Mock email sending (ready for Fiona/SendGrid integration)
-  Interactive command-line interface for approvals

**How it fits Fiona:** This script demonstrates production-quality workflows that maintain human oversight. Users can research leads, approve generated emails, and send through Fiona with confidence that each message has been reviewed. The regeneration loop ensures email quality meets user standards before sending.

**Integration:** 
- Output emails can be imported directly into Fiona campaigns
- Approval workflow integrates with Fiona's UI for user decisions
- Mock send can connect to Fiona backend or SendGrid
- Session state persists across long approval cycles

**Usage:**
```bash
python human_in_loop_lead_outreach.py
```

Then interact with the approval menu to review, edit, or regenerate emails before sending.

---

## Architecture & Workflow Patterns

These agents demonstrate three core ADK patterns that enhance Fiona:

### Sequential Pattern
Used when order matters and each step builds on the previous one.
- Problem discovery → Skill mapping → Message generation

### Parallel Pattern
Used when independent tasks can run simultaneously for speed.
- Reddit research + Quora research + Freelance research (all at once)

### Agent Tools Pattern
Used when agents need to specialize and delegate work to other agents.
- Researcher agent (finds data) + Main agent (uses research to craft output)

### Loop Pattern
Used for iterative refinement and quality assurance.
- Discover problems → Review & eliminate weak ones (repeat) → Format output

---

## How Agents Enhance Fiona

| Feature | Agent | Benefit |
|---------|-------|---------|
| Smart Campaign Targeting | Loop Agent (Problem Refinement) | Validated, location-specific targeting criteria |
| Template Generation | Sequential + Parallel Agents | Auto-generated email templates save hours |
| Multi-Source Research | Parallel Agent | Fast, comprehensive market research in seconds |
| Career-Based Segmentation | Sequential Agent | Target users by career field and industry skills |
| Rapid Prototyping | All Agents | Test campaign angles instantly before sending via Fiona |
| Agent Specialization | Personalized Lead Outreach (Agent Tools) | Researchers and outreach specialists work independently |
| Research-Backed Personalization | Personalized Lead Outreach (Agent Tools) | Authentic emails with genuine lead insights |
| Human-Approved Outreach | Human-in-the-Loop Script | AI generates, humans approve, regenerate until satisfied |
| Lead Intelligence | Human-in-the-Loop Script | Research-backed personalization increases engagement |

---

## Getting Started

### Prerequisites
- Python 3.8+
- Google API key (Gemini API)
- `.env` file with `GOOGLE_API_KEY`

### Installation

1. Clone or download this folder
2. Create a `.env` file in the mira directory:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running an Agent

1. Open any notebook in Jupyter or VS Code
2. Modify the input variables (career, industry, city as needed)
3. Run the cells to generate insights
4. Copy outputs directly into Fiona campaigns

---

## Agent Inputs & Outputs

### Career-Targeted Cold Outreach
- **Input:** Career background, target industry
- **Output:** Personalized LinkedIn messages for each opportunity

### Multi-Channel Research & Email Generation
- **Input:** Career field
- **Output:** 3-4 ready-to-send email templates with subject lines

### Personalized Lead Outreach
- **Input:** Career field, lead name
- **Output:** Lead research summary, personalized cold outreach email

### Iterative Problem Refinement
- **Input:** Career, industry, city
- **Output:** Validated list of problems (one sentence each)

### Human-in-the-Loop Lead Outreach
- **Input:** Career field, lead name, lead email
- **Output:** Researched lead profile, personalized email (subject + body), user approval status, sent message ID

---

## Integration with Fiona Backend

These agents are designed to integrate with Fiona's Django backend:

1. **Campaign Template Import** - Agents generate templates that import into Fiona's template library
2. **Contact List Segmentation** - Validated problems become targeting filters
3. **Bulk Email Generation** - Multi-template output enables A/B testing in Fiona
4. **Analytics Integration** - Track which agent-generated templates perform best

---

## File Structure

```
mira/
├── career-outreach-sequential-agents.ipynb      # Sequential workflow (notebook)
├── parallel-cold-email-outreach.ipynb           # Parallel workflow (notebook)
├── personalized-lead-outreach.ipynb             # Agent Tools pattern (notebook)
├── loop-agent-problem-refinement.ipynb          # Loop workflow (notebook)
├── human_in_loop_lead_outreach.py               # Human approval + regeneration (standalone script)
├── requirements.txt                              # Dependencies
├── .env                                          # API keys (gitignored)
├── .gitignore                                    # Excludes sensitive files
└── README.md                                     # This file
```

---

## What Gets Ignored

The `.gitignore` file excludes:
- `.env` (contains API keys)
- `day-1a-from-prompt-to-action.ipynb` (learning notebook)
- `day-1b-agent-architectures.ipynb` (learning notebook)

Only production agents are tracked.

---

## Roadmap: Future Integration

Planned enhancements to deepen Fiona integration:

- Real-time agent suggestions as users create campaigns
- Agent-powered contact list enrichment
- Automated A/B testing of agent-generated templates
- Performance scoring for agent outputs
- Multi-language agent support

---

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Gemini API](https://ai.google.dev/)
- [Fiona Platform](https://fiona.mrphilip.cv)

---

## License

These agents are part of the Fiona ecosystem. Use them to enhance your Fiona campaigns.

---

**Questions or feedback?** Reach out or visit [fiona.mrphilip.cv](https://fiona.mrphilip.cv) to learn more about how agents power intelligent email campaigns.
