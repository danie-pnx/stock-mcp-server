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

# Mount the MCP server's SSE application to the root of FastAPI
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    # Railway passes the active port dynamically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)