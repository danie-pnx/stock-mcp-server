import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import yfinance as yf

# Initialize the MCP Server
mcp = FastMCP("AlphaVantage_Finance")

@mcp.tool()
def get_ticker_news(symbol: str) -> str:
    """Fetch the latest news headlines and sentiment for a given stock symbol."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        # ADD THIS LINE to see what Yahoo Finance is actually giving us
        print(f"RAW NEWS DATA: {news}") 
        
        if not news:
            return f"No recent news found for {symbol}."
        
        # We will comment this out temporarily until we know the right key
        headlines = [f"- {item['content']['title']}" for item in news[:3]]
        
        return f"Recent news for {symbol}:\n" + "\n".join(headlines)
        
        # return "Check your Python terminal for the raw data!"
        
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