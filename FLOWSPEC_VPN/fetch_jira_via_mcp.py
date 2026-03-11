#!/usr/bin/env python3
"""
Fetch Jira Test Data via MCP - Uses MCP tools to fetch and cache Jira data

This script should be run by the AI assistant using MCP tools to fetch
Jira issues and save them to cache for the test verifier to use.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add test_verifier to path
sys.path.insert(0, str(Path(__file__).parent))

from test_verifier.jira_fetcher import CACHE_DIR, save_to_cache

CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_mcp_jira_data(issue_key: str, mcp_data: dict):
    """Save Jira data fetched via MCP tools to cache"""
    # Convert MCP format to our expected format
    cached_data = {
        "key": issue_key,
        "id": mcp_data.get("id"),
        "fields": {
            "summary": mcp_data.get("summary", ""),
            "description": mcp_data.get("description", ""),
            # Add other fields as needed
        },
        "source": "mcp_jira",
        "fetched_via": "mcp",
    }
    
    # If description is in a different format, extract it
    if "description" in mcp_data:
        cached_data["fields"]["description"] = mcp_data["description"]
    elif "fields" in mcp_data and "description" in mcp_data["fields"]:
        cached_data["fields"]["description"] = mcp_data["fields"]["description"]
    
    save_to_cache(issue_key, cached_data)
    print(f"✓ Cached {issue_key} from MCP")


if __name__ == "__main__":
    print("This script is meant to be called with MCP-fetched Jira data.")
    print("The AI assistant should use MCP tools to fetch Jira issues")
    print("and call save_mcp_jira_data() for each issue.")
