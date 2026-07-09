# gymlog-mcp

An MCP (Model Context Protocol) server that lets an AI assistant log workouts and manage a training programme directly, via natural language.

Built as a hands-on project to learn backend tool/API design using Anthropic's Model Context Protocol — SQLite-backed, connected to Claude Desktop over stdio.

## Tools

- **`ping`** — confirms the server is alive
- **`log_workout`** — logs a workout session (exercise, weight, reps, sets) to a given date
- **`get_day`** — returns all sets logged on a given date
- **`get_plan`** — reads the current training programme (optionally filtered by week)
- **`replace_day`** — replaces a single day of the programme with a new set of exercises, leaving other days untouched

Together, `get_plan` and `replace_day` support the core use case: telling the assistant "restructure Week B, Day 3" and having it read the existing plan, reason about the change, and write back just that day.

## Running it

Requires Python 3.10+ and the [`mcp`](https://pypi.org/project/mcp/) package.

\`\`\`bash
pip install mcp
python server.py
\`\`\`

The server communicates over stdio, so it's designed to be launched by an MCP client (e.g. Claude Desktop) rather than run standalone for interactive use. On first run it creates `gym.db` in the same directory with the required tables.

To connect it to Claude Desktop, add it to your `claude_desktop_config.json` as a stdio server pointing at this `server.py`.
