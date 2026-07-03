# Automated Stock News & Sentiment Aggregator System: MCP Server Script.

## Abstract

This project implements a Model Context Protocol (MCP) server that acts as a financial intelligence datasource, dynamically exposing stock news query capabilities to an orchestrator system over Server-Sent Events (SSE).

Serving as the server instance defined in [server.py](file:///c:/Projects/stock-mcp-server/server.py), this project:
1. Connects over Server-Sent Events (SSE) to dynamically expose real-time market data tools to the client.
2. Integrates with the `yfinance` API to retrieve live headlines and news content for a requested ticker symbol.
3. Employs a custom middleware layer (`DisableProxyBufferingMiddleware`) to disable downstream proxy buffering on cloud hosting platforms (like Railway) for immediate SSE packet delivery.

This server acts as the data provider for the automated daily stock brief workflow executed by the orchestrator agent.

> Related Repository : [Autonomous Finance Agent Orchestrator](https://github.com/danie-pnx/autonomous-finance-agent).

## Tech Stack

- **Runtime:** Python `3.14.4`
- **MCP Server Framework:** `mcp` (v1.28.1)
- **Web & Streaming Framework:** `fastapi` (v0.138.2) and `uvicorn` (v0.49.0)
- **Financial Data Integration:** `yfinance` (v1.5.1)
- **LLM Client Library:** `groq` (v1.5.0)
- **Environment Management:** `python-dotenv` (v1.2.2)

## How the System Works

### MCP Server Lifecycle and Request Handling

The server lifecycle and request processing pipeline are implemented within [server.py](file:///c:/Projects/stock-mcp-server/server.py). The pipeline consists of the following 5 phases:

1. **Server Initialization and Security Configuration:**
   Instantiates the `FastMCP` server with custom security settings, disabling DNS rebinding protection and permitting all hosts (`*`) to ensure compatibility with reverse proxy routes.
2. **Tool Registration (yfinance Integration):**
   Defines and registers the [get_ticker_news](file:///c:/Projects/stock-mcp-server/server.py#L18) tool with the `@mcp.tool()` decorator, allowing it to accept a ticker symbol and query `yfinance` to retrieve stock headlines.
3. **Web Framework Setup:**
   Initializes a standard `FastAPI` application instance to serve as the web application interface for hosting the server.
4. **SSE Proxy Buffering Bypass:**
   Wraps the application in [DisableProxyBufferingMiddleware](file:///c:/Projects/stock-mcp-server/server.py#L38) to intercept downstream SSE packets. The middleware injects `x-accel-buffering: no`, `cache-control: no-cache`, and `connection: keep-alive` headers to prevent cloud proxies (e.g. Nginx or Cloudflare) from buffering real-time tool communications.
5. **FastMCP Mounting and Execution:**
   Mounts the Server-Sent Events (SSE) server application onto the FastAPI root using `app.mount("/", mcp.sse_app())` and starts hosting using `uvicorn` on a port dynamically supplied by the environment.

## How To Setup

1. **Clone this repository:**
   Clone the repository to your local machine or fork it to your GitHub account:
   ```bash
   git clone https://github.com/danie-pnx/stock-mcp-server.git
   ```
2. **Deploy to Railway:**
   Sign up for a [Railway](https://railway.app/) account, create a new project, and add a Railway server instance by deploying your GitHub repository.
3. **Configure the Orchestrator:**
   Get the public URL of the deployed Railway server and set it as the `RAILWAY_MCP_URL` environment variable in your local configuration (e.g. `.env` file) or in GitHub Secrets for your orchestrator pipeline.