import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import yfinance as yf

# 1. Initialize the MCP Server
mcp = FastMCP(
    "AlphaVantage_Finance",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False, # Disble for Reverse Proxy
        allowed_hosts=["*"] # Railway Reverse Proxy
    )
)

# 2. Defining the Stock News Tool
@mcp.tool()
def get_ticker_news(symbol: str) -> str:
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return f"No recent news found for {symbol}."
        
        # Traverse into the 'content' dictionary to grab the title
        headlines = [f"- {item['content']['title']}" for item in news[:3]]
        
        return f"Recent news for {symbol}:\n" + "\n".join(headlines)
        
    except Exception as e:
        return f"Error fetching data for {symbol}: {str(e)}"

# 3. Initialize the Web Application Instance
app = FastAPI()

# 4. Injecting Middleware for SSE
class DisableProxyBufferingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/sse":
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Convert headers list to a dictionary for easy manipulation
                    headers = dict(message.get("headers", []))
                    
                    # Force response streaming and prevent reverse proxy choking
                    headers[b"x-accel-buffering"] = b"no"
                    headers[b"cache-control"] = b"no-cache"
                    headers[b"connection"] = b"keep-alive"
                    
                    # Re-assign modified headers back to the original message payload
                    message["headers"] = list(headers.items())
                await send(message)
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Apply the middleware wrapper around the primary FastAPI app
app.add_middleware(DisableProxyBufferingMiddleware)

# 5. Mount the MCP Application
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)