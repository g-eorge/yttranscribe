# yttranscribe

Fetch YouTube video transcripts and metadata, saving them to structured markdown.

## Prerequisites

### uv

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and running.

Install uv:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Or with pip
pip install uv
```

See the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for more options.

### YouTube Data API key

Set `YOUTUBE_API_KEY` in your environment or in a `.env` file at the project root.

## Claude Code MCP setup

Add the MCP server to Claude Code (replace `/path/to/yttranscribe` with the actual path):

```bash
claude mcp add --scope user yttranscribe uv -- run --directory /path/to/yttranscribe python -m yttranscribe.mcp_server
```
