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
* ✔ **NEW: Full support for YouTrack’s MCP Server via the OpenAI Responses API**

---

## 🎯 How It Works

The application can operate in **two modes**:

---

### **1. Classic GPT Parsing Mode (default)**

```
User → Natural language
     → GPTParser → JSON action
     → Orchestrator → YouTrack REST API
```

Example:

```
> Create an Epic in project SUP titled "WiFi Refactoring"...

GPT → JSON:
{
  "action": "create_epic_with_children",
  "project": "SUP",
  ...
}

Orchestrator → YouTrack API → issues created
```

This mode uses your existing code to map LLM-generated JSON into REST API calls.

---

### **2. MCP Mode (Model Context Protocol) — NEW**

In this mode, the OpenAI **Responses API** connects directly to the **YouTrack MCP server**, allowing the LLM to:

* discover the tools exposed by YouTrack
* call them autonomously
* chain multiple tools to perform complex operations
* retrieve structured data directly from YouTrack
* summarize or transform results without hand-written parsing logic

The flow becomes:

```
User → Natural language
     → OpenAI Responses API
     → MCP Tool Calls (YouTrack)
     → Direct results from YouTrack MCP Server
```

This unlocks YouTrack-native operations such as:

* `search_issues`
* `get_issue`
* `create_issue`
* `update_issue`
* `add_issue_comment`
* `link_issues`
* and more, depending on your instance configuration.

To enable MCP mode:

```
python youtrack-mcp.py --use-mcp
```

Or:

```
export USE_MCP=1
python youtrack-mcp.py
```

---

## 🔌 MCP Mode (Model Context Protocol)

When MCP mode is enabled, YouTrackLLM becomes a **true MCP client**.

The application automatically configures a tool connection pointing to:

```
<YT_BASE_URL>/mcp
```

with authentication provided via:

```
Authorization: Bearer <YT_TOKEN>
```

The OpenAI model is then allowed to autonomously call MCP tools.
For example, a user prompt such as:

```
MCP> Show all open issues assigned to me in project SUP and summarize them.
```

may trigger internally:

```
[tool_call] search_issues
[tool_call] get_issue
[tool_call] link_issues
...
```

The assistant aggregates and summarizes the results with no manual JSON parsing.

MCP mode provides:

* more natural dialog
* richer queries
* deeper YouTrack integration
* tool auto-discovery
* schema-enforced output

Your existing CLI and configuration system remain fully compatible.

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

### 5. Optional: enable MCP mode

```
python youtrack-mcp.py --use-mcp
```

---

## 💬 Example Commands

YouTrackLLM understands natural language like:

```
Create a ticket in project SUP titled "Access error" with priority Critical.
Show me all issues assigned to admin in project SUP.
Create an Epic in project SUP titled "New WiFi Module" with subtasks Driver, GUI, Tests.
Add a subtask to Epic SUP-17 titled "Additional RF analysis".
Show the hierarchy of Epic SUP-17.
```

In **MCP mode**, you can ask even more complex queries, for example:

```
MCP> Summarize all high-priority bugs from the last 30 days.
MCP> Create a task in SUP titled “Test build pipeline” and assign it to admin.
MCP> Analyze the status of release 3.4 and generate a risk report.
```

---

## 📌 Does this project now use YouTrack’s MCP server?

**Yes — fully.**

The project now includes:

* a complete MCP client implementation
* automatic tool registration for OpenAI
* authenticated requests to the YouTrack MCP endpoint
* full support for MCP tool discovery and invocation
* an integrated CLI for MCP interaction

Both modes (classic & MCP) coexist, and you can choose the one you prefer.

---

## 🛣 Roadmap

* [x] Create Epic + subtasks
* [x] Show Epic hierarchy (tree view)
* [x] Add subtask to existing Epic
* [x] **MCP client integration**
* [ ] Move subtask between Epics
* [ ] Delete Epic + cascade-delete subtasks
* [ ] Automatic MCP tool usage with chain-of-thought suppression
* [ ] Agent mode for ChatGPT / OpenAI MCP

---

## 📜 License

MIT License.

---

## 🚀 Author

YouTrackLLM is developed by **Fabio**, with AI-assisted support.
The goal is to provide a lightweight, powerful, and extensible **AI-powered interface for YouTrack**.
