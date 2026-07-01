import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import yfinance as yf

# Initialize the MCP Server
mcp = FastMCP("AlphaVantage_Finance")

# Define a tool using the decorator
@mcp.tool()
def get_ticker_news(symbol: str) -> str:
    """Fetch the latest news headlines and sentiment for a given stock symbol."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return f"No recent news found for {symbol}."
        
        # Format the top 3 headlines
        headlines = [f"- {item['title']}" for item in news[:3]]
        return f"Recent news for {symbol}:\n" + "\n".join(headlines)
    except Exception as e:
        return f"Error fetching data for {symbol}: {str(e)}"

# Initialize the web framework
app = FastAPI()

# Mount the MCP server to FastAPI to enable SSE transport
mcp.add_api_routes(app)

if __name__ == "__main__":
    # Railway passes the active port dynamically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)