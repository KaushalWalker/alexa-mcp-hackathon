# DayPilot — Your Voice-First AI Day Planner

**Turn everyday requests into organized tasks and actionable daily plans.**

DayPilot is a voice-first personal productivity assistant designed to help people manage tasks, track deadlines, and plan their time using natural language. Instead of navigating multiple screens, users can tell DayPilot what they need to do, mark work as complete, and generate an updated schedule.

## The Problem

Keeping track of tasks is easy. Deciding what to work on, when to do it, and how to adjust when plans change is harder.

Traditional task managers often require users to manage tasks, priorities, and schedules manually. DayPilot aims to make this workflow more conversational and adaptive.

## The Solution

DayPilot brings task management and daily planning into one assistant experience.

- **Natural-language task management:** Create tasks and specify their estimated duration.
- **Voice-friendly interaction:** Use the browser interface to interact with the assistant.
- **Task completion:** Mark tasks complete using natural-language commands.
- **Adaptive replanning:** Generate an updated plan after task completion.
- **Date-aware planning:** Request a plan for today or tomorrow.
- **Preference management:** Configure working hours, focus duration, and break duration.
- **MCP integration:** Expose productivity tools through a Model Context Protocol server.

## Demo

**Demo video:** https://youtu.be/q-4WIDtiprA

**Screenshots:** *Add screenshots of the voice interface and a generated daily plan here.*

## How It Works

1. The user enters a natural-language request through the browser interface.
2. DayPilot identifies the requested action.
3. The voice API extracts relevant details, such as task title, duration, or requested planning date.
4. The assistant invokes the relevant task-management or planning functionality.
5. The user receives a response and, when applicable, an updated schedule.

## Architecture

```text
User
  |
  v
Browser Voice Interface
  |
  v
FastAPI Voice API
  |
  +--> Intent Detection
  |
  +--> Task and Date Extraction
  |
  +--> Assistant / Planning Engine
  |          |
  |          v
  |     Task Storage
  |
  v
Assistant Response

MCP Client --> MCP Server --> Productivity Tools
```

The browser interface and FastAPI service handle conversational requests. The planning and task-management components process those requests, while the MCP server exposes productivity tools to compatible clients.

## Tech Stack

- **Language:** Python
- **API:** FastAPI
- **Tool integration:** Model Context Protocol (MCP)
- **Interface:** HTML, CSS, JavaScript, browser speech capabilities
- **Data storage:** JSON
- **Testing:** pytest

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/KaushalWalker/alexa-mcp-hackathon.git
cd alexa-mcp-hackathon
```

### 2. Create and activate a virtual environment

Python 3.12 is recommended.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`. Use the mock LLM configuration for local testing without external model API costs. Configure any required credentials only if you intend to use the corresponding integration.

### 5. Start the voice API

```powershell
$env:DAYPILOT_MODE = "demo"
uvicorn app.voice_api:app --reload --port 8001
```

Open the browser interface:

http://127.0.0.1:8001/static/voice.html

### 6. Start the MCP server

In a separate terminal, activate the virtual environment and run:

```powershell
python app\server\mcp_server.py
```

The MCP server is configured to expose its endpoint at:

http://127.0.0.1:8000/mcp

## Example Commands

Try these commands in the browser interface:

- "Show my pending tasks."
- "Add a task to practice my demo for 15 minutes."
- "I finished preparing my AI project presentation."
- "Plan my remaining tasks for tomorrow."
- "Set my focus time to 25 minutes."

## Testing

Run the automated test suite:

```powershell
python -m pytest -q
```

The latest verified test run passed **61 tests**.

## Project Status

DayPilot has working task creation, pending-task listing, natural-language task completion, preference updates, and date-aware planning in its browser interface.

The local demo uses sample data to keep demonstrations repeatable. External model and speech integrations may require additional configuration.

## Built For

An Amazon developer hackathon, exploring voice-first productivity and MCP-powered task management.

## Author

**Kaushal Jambhale**

- GitHub: https://github.com/KaushalWalker
- LinkedIn: https://www.linkedin.com/in/kaushaljambhle/
