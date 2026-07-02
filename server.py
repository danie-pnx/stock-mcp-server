import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import yfinance as yf

# Initialize the MCP Server with cloud-ready security settings
mcp = FastMCP(
    "AlphaVantage_Finance",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False, 
        allowed_hosts=["*"] # Trust the Railway reverse proxy
    )
)

@mcp.tool()
def get_ticker_news(symbol: str) -> str:
    """Fetch the latest news headlines and sentiment for a given stock symbol."""
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

# Initialize the web framework
app = FastAPI()

# --- CLOUD PROXY BUFFERING FIX (ASGI Middleware) ---
class DisableProxyBufferingMiddleware:
    """
    Intersects downstream communication with Railway's reverse proxy.
    Tells Nginx/Cloudflare to flush bytes immediately instead of buffering.
    """
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
# ---------------------------------------------------

# Mount the MCP server's SSE application to the root of FastAPI
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    # Railway passes the active port dynamically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)