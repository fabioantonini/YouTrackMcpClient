# YouTrackLLM

**YouTrackLLM** is a Python application that lets you interact with **YouTrack using natural language**, powered by an LLM (OpenAI GPT) acting as an intelligent parser between the user and the YouTrack REST API.

With YouTrackLLM you can create projects, issues, epics, subtasks, update fields, change assignees, link issues, and visualize hierarchies — simply by typing commands in plain English or Italian.

---

## ✨ Main Features

* ✔ **Project creation** (`create_project`)
* ✔ **Issue creation** (`create_issue`)
* ✔ **Issue updates** (`update_issue`)
* ✔ **Assignee changes** (`change_issue_assignee`)
* ✔ **Issue deletion** (`delete_issue`)
* ✔ **Advanced issue listing** with smart filters (`list_issues`)
* ✔ **Automatic project summaries** (`summarize_project`)
* ✔ **Epic creation** (`create_epic`)
* ✔ **Epic with subtasks creation** (`create_epic_with_children`)
* ✔ **Add a new subtask to an existing Epic** (`add_subtask`)
* ✔ **Visualize Epic hierarchy** (`show_epic_hierarchy`)
* ✔ **Bidirectional issue linking** (`link_issues`)
* ✔ **LLM-powered natural language parser**
* ✔ **Dynamic override of YouTrack URL & Token via CLI**

---

## 🎯 How It Works

The application follows this pipeline:

```
User → Natural language command
     → GPTParser (LLM) → Structured JSON
     → Orchestrator → YouTrackClient
     → YouTrack REST API
```

Example:

```
> Create an Epic in project SUP titled "WiFi Refactoring" with three subtasks…

GPT → JSON:
{
  "action": "create_epic_with_children",
  "project": "SUP",
  ...
}

Orchestrator → YouTrack API → issues and links created
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-account>/YouTrackLLM.git
cd YouTrackLLM
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key

```bash
export OPENAI_API_KEY=sk-xxxx
```

### 4. Configure YouTrack

You can set environment variables:

```bash
export YT_BASE_URL="https://<org>.youtrack.cloud"
export YT_TOKEN="perm:xxx.yyy.zzz"
```

Or override from the command line:

```bash
python youtrack-mcp.py --yt-url https://<org>.youtrack.cloud --yt-token <token>
```

---

## 💬 Example Commands

YouTrackLLM understands natural language like:

```
Create a ticket in project SUP titled "Access error" with priority Critical.
```

```
Show me all issues assigned to admin in project SUP.
```

```
Create an Epic in project SUP with title "New WiFi Module" and subtasks "Driver", "GUI", "Tests".
```

```
Add a subtask to Epic SUP-17 titled "Additional RF analysis", priority Major.
```

```
Show the hierarchy of Epic SUP-17.
```

---

## 📌 Does this project actually use YouTrack’s MCP server?

**No.**

YouTrackLLM **does not use** the official **Model Context Protocol (MCP)** server provided by JetBrains.

Instead, this project uses:

* YouTrack’s **standard REST API**
* A custom **LLM-powered JSON action parser**
* A Python “orchestrator” that behaves similarly to an MCP agent, but **without using the MCP server endpoints**

### Why?

Because the YouTrack MCP server exposes tool definitions under:

```
/api/mcp/server
```

and requires a proper MCP client that invokes those tools.

In our project:

* The LLM generates structured JSON actions
* The Python application interprets these actions
* The YouTrackClient executes REST API calls manually

So this is essentially an **MCP-inspired architecture**, but not actual MCP.

### Can this project be extended to use the real MCP server?

✔ Yes — it’s completely possible.
We can add a new module acting as a **true MCP client** speaking the MCP protocol.
If you want, I can prepare a branch that does that.

---

## 🛣 Roadmap

* [x] Create Epic + subtasks
* [x] Show Epic hierarchy (tree view)
* [x] Add subtask to existing Epic
* [ ] Move subtask between Epics
* [ ] Delete Epic + cascade-delete subtasks
* [ ] Optional integration with real MCP server
* [ ] Agent mode for ChatGPT / OpenAI MCP

---

## 📜 License

MIT License.

---

## 🚀 Author

YouTrackLLM is developed by **Fabio**, with LLM support.
The goal is to provide a lightweight, powerful, and customizable **AI wrapper** for YouTrack.

