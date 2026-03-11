#!/usr/bin/env python3
"""
Jira Fetcher - Fetch test structure from Jira tickets

This module fetches test plan data from Jira tickets using MCP tools
or REST API, with fallback to local markdown files.

Note: MCP tools are only available to the AI assistant. This module
can work with pre-fetched/cached data or use Jira REST API directly.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

try:
    from .adf_parser import parse_adf_to_markdown, extract_text_from_adf
    ADF_PARSER_AVAILABLE = True
except ImportError:
    ADF_PARSER_AVAILABLE = False
    logger.warning("ADF parser not available")

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path("/home/dn/SCALER/FLOWSPEC_VPN/test_results/jira_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Jira issue keys
JIRA_KEYS = {
    "happy_flow": "SW-234158",
    "negative": "SW-234159",
    "topology": "SW-234160",
    "test_category": "SW-231823",
}

# Fallback markdown files
MARKDOWN_FILES = {
    "happy_flow": Path("/home/dn/SCALER/FLOWSPEC_VPN/SW-234158_HAPPY_FLOW.md"),
    "negative": Path("/home/dn/SCALER/FLOWSPEC_VPN/SW-234159_NEGATIVE_TESTING.md"),
    "topology": Path("/home/dn/SCALER/FLOWSPEC_VPN/SW-234160_TOPOLOGY_CREATION.md"),
}


def get_cache_path(issue_key: str) -> Path:
    """Get cache file path for a Jira issue"""
    return CACHE_DIR / f"{issue_key}.json"


def save_to_cache(issue_key: str, data: Dict[str, Any]) -> None:
    """Save fetched Jira data to cache"""
    cache_path = get_cache_path(issue_key)
    cache_data = {
        "issue_key": issue_key,
        "fetched_at": datetime.now().isoformat(),
        "data": data,
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f, indent=2)
    logger.info(f"Cached Jira data for {issue_key} to {cache_path}")


def load_from_cache(issue_key: str) -> Optional[Dict[str, Any]]:
    """Load cached Jira data"""
    cache_path = get_cache_path(issue_key)
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                logger.info(f"Loaded cached data for {issue_key} (fetched at {cache_data.get('fetched_at')})")
                return cache_data.get("data")
        except Exception as e:
            logger.warning(f"Failed to load cache for {issue_key}: {e}")
    return None


def fetch_from_jira_rest_api(issue_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch issue from Jira using REST API
    
    Note: This requires Jira credentials in environment variables:
    - JIRA_URL (e.g., https://drivenets.atlassian.net)
    - JIRA_EMAIL
    - JIRA_API_TOKEN
    
    IMPORTANT: Fetches customfield_11772 (Test Description) which contains test cases.
    """
    import requests
    from requests.auth import HTTPBasicAuth
    
    jira_url = os.getenv("JIRA_URL", "https://drivenets.atlassian.net")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not jira_email or not jira_token:
        logger.warning("Jira credentials not found in environment variables")
        return None
    
    try:
        # Fetch with Test Description custom field (customfield_11772)
        url = f"{jira_url}/rest/api/3/issue/{issue_key}"
        auth = HTTPBasicAuth(jira_email, jira_token)
        headers = {"Accept": "application/json"}
        params = {
            "fields": "summary,description,customfield_11772,comment"
        }
        
        response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Fetched {issue_key} from Jira REST API (with Test Description field)")
        return data
    except ImportError:
        logger.warning("requests library not installed. Install with: pip install requests")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch {issue_key} from Jira REST API: {e}")
        return None


def load_from_markdown(issue_type: str) -> Optional[str]:
    """Load test data from local markdown file"""
    markdown_path = MARKDOWN_FILES.get(issue_type)
    if markdown_path and markdown_path.exists():
        try:
            with open(markdown_path, "r") as f:
                content = f.read()
                logger.info(f"Loaded markdown file: {markdown_path}")
                return content
        except Exception as e:
            logger.error(f"Failed to load markdown file {markdown_path}: {e}")
    return None


def fetch_issue(issue_key: str, use_cache: bool = True, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch Jira issue data
    
    Priority:
    1. Cache (if use_cache=True and not force_refresh)
    2. Jira REST API
    3. Markdown file (fallback)
    
    Args:
        issue_key: Jira issue key (e.g., "SW-234158")
        use_cache: Use cached data if available
        force_refresh: Force refresh from Jira (ignore cache)
    
    Returns:
        Dict with issue data, or None if all methods fail
    """
    # Try cache first
    if use_cache and not force_refresh:
        cached_data = load_from_cache(issue_key)
        if cached_data:
            return cached_data
    
    # Try Jira REST API
    jira_data = fetch_from_jira_rest_api(issue_key)
    if jira_data:
        save_to_cache(issue_key, jira_data)
        return jira_data
    
    # Fallback to markdown
    issue_type = None
    for key, value in JIRA_KEYS.items():
        if value == issue_key:
            issue_type = key
            break
    
    if issue_type:
        markdown_content = load_from_markdown(issue_type)
        if markdown_content:
            # Convert markdown to structured format
            return {
                "key": issue_key,
                "fields": {
                    "description": markdown_content,
                    "summary": f"FlowSpec VPN {issue_type.replace('_', ' ').title()}",
                },
                "source": "markdown",
            }
    
    logger.error(f"Failed to fetch {issue_key} from all sources")
    return None


def fetch_all_test_issues() -> Dict[str, Dict[str, Any]]:
    """Fetch all test-related Jira issues"""
    results = {}
    for issue_type, issue_key in JIRA_KEYS.items():
        logger.info(f"Fetching {issue_key} ({issue_type})...")
        data = fetch_issue(issue_key)
        if data:
            results[issue_type] = data
        else:
            logger.warning(f"Failed to fetch {issue_key}")
    return results


def get_issue_description(issue_data: Dict[str, Any]) -> str:
    """
    Extract description from Jira issue data
    
    Priority:
    1. Test Description custom field (customfield_11772) - PRIMARY for test issues
       - Handles ADF format (Atlassian Document Format)
    2. Standard description field
    """
    # Helper to extract and parse ADF
    def extract_adf_value(test_desc_field):
        """Extract ADF document from test description field"""
        if isinstance(test_desc_field, dict):
            # Check if it's ADF format (has "type": "doc")
            if test_desc_field.get("type") == "doc":
                # This is ADF format - parse it
                if ADF_PARSER_AVAILABLE:
                    try:
                        markdown = parse_adf_to_markdown(test_desc_field)
                        if markdown:
                            return markdown
                    except Exception as e:
                        logger.warning(f"Failed to parse ADF: {e}, falling back to text extraction")
                        return extract_text_from_adf(test_desc_field)
                else:
                    # Fallback to text extraction
                    return extract_text_from_adf(test_desc_field)
            # May be {"value": {...}} format with ADF inside
            elif "value" in test_desc_field:
                value = test_desc_field["value"]
                if isinstance(value, dict) and value.get("type") == "doc":
                    if ADF_PARSER_AVAILABLE:
                        try:
                            return parse_adf_to_markdown(value)
                        except Exception as e:
                            logger.warning(f"Failed to parse ADF from value: {e}")
                            return extract_text_from_adf(value)
                    else:
                        return extract_text_from_adf(value)
                elif isinstance(value, str):
                    return value
            # Plain dict, try to extract text
            return str(test_desc_field)
        elif isinstance(test_desc_field, str):
            return test_desc_field
        return ""
    
    if "fields" in issue_data:
        # FIRST: Try Test Description custom field (customfield_11772)
        test_desc = issue_data["fields"].get("customfield_11772")
        if test_desc:
            result = extract_adf_value(test_desc)
            if result:
                return result
        
        # FALLBACK: Standard description field
        description = issue_data["fields"].get("description", "")
        if isinstance(description, dict):
            # Jira API v3 returns description as object with "content" array
            return _extract_text_from_jira_content(description)
        return description
    
    # Also check top-level customfield_11772 (from MCP direct fetch)
    if "customfield_11772" in issue_data:
        result = extract_adf_value(issue_data["customfield_11772"])
        if result:
            return result
    
    return ""


def _extract_text_from_jira_content(content: Dict) -> str:
    """Extract plain text from Jira content structure"""
    text_parts = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "text":
                text_parts.append(obj.get("text", ""))
            elif obj.get("type") == "paragraph":
                if "content" in obj:
                    for item in obj["content"]:
                        extract_recursive(item)
            elif "content" in obj:
                for item in obj["content"]:
                    extract_recursive(item)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
    
    extract_recursive(content)
    return "\n".join(text_parts)


def get_test_categories_from_cache() -> List[Dict[str, Any]]:
    """
    Get test categories from cache
    
    Note: Categories should be fetched via MCP and cached first.
    This function reads from cache.
    
    Returns:
        List of test category issues
    """
    categories_cache = CACHE_DIR / "test_categories.json"
    if categories_cache.exists():
        try:
            with open(categories_cache, "r") as f:
                data = json.load(f)
                return data.get("categories", [])
        except Exception as e:
            logger.warning(f"Failed to load categories cache: {e}")
    return []


def save_test_categories_to_cache(categories: List[Dict[str, Any]]) -> None:
    """Save test categories to cache"""
    categories_cache = CACHE_DIR / "test_categories.json"
    cache_data = {
        "fetched_at": datetime.now().isoformat(),
        "categories": categories,
    }
    with open(categories_cache, "w") as f:
        json.dump(cache_data, f, indent=2)
    logger.info(f"Cached {len(categories)} test categories")


def get_category_tests_from_cache(category_key: str) -> List[Dict[str, Any]]:
    """
    Get child tests for a category from cache
    
    Args:
        category_key: Test category issue key (e.g., "SW-231823")
    
    Returns:
        List of child test issues
    """
    tests_cache = CACHE_DIR / f"category_{category_key}_tests.json"
    if tests_cache.exists():
        try:
            with open(tests_cache, "r") as f:
                data = json.load(f)
                return data.get("tests", [])
        except Exception as e:
            logger.warning(f"Failed to load tests cache for {category_key}: {e}")
    return []


def save_category_tests_to_cache(category_key: str, tests: List[Dict[str, Any]]) -> None:
    """Save category child tests to cache"""
    tests_cache = CACHE_DIR / f"category_{category_key}_tests.json"
    cache_data = {
        "category_key": category_key,
        "fetched_at": datetime.now().isoformat(),
        "tests": tests,
    }
    with open(tests_cache, "w") as f:
        json.dump(cache_data, f, indent=2)
    logger.info(f"Cached {len(tests)} tests for category {category_key}")


def get_all_test_categories() -> List[Dict[str, Any]]:
    """
    Get all test categories from cache
    
    Returns:
        List of test category issues with key, summary, etc.
    """
    categories = get_test_categories_from_cache()
    if not categories:
        logger.warning("No test categories found in cache. Categories should be fetched via MCP first.")
    return categories


def get_tests_for_category(category_key: str) -> List[Dict[str, Any]]:
    """
    Get child tests for a category from cache
    
    Args:
        category_key: Test category issue key (e.g., "SW-231823")
    
    Returns:
        List of child test issues
    """
    tests = get_category_tests_from_cache(category_key)
    if not tests:
        logger.warning(f"No tests found in cache for category {category_key}. Tests should be fetched via MCP first.")
    return tests


# Note: Functions to fetch via MCP are called by AI assistant.
# The fetched data is then cached and can be read by these helper functions.
# Example MCP calls (done by AI):
# - mcp_dn-mcp-server_atlassian_jira_search(jql='project = SW AND issuetype = "Test Category" AND summary ~ "FlowSpec VPN"')
# - mcp_dn-mcp-server_atlassian_jira_search(jql='project = SW AND (parent = SW-231823 OR "Test Category" = SW-231823)')


if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    print("Fetching all test issues...")
    results = fetch_all_test_issues()
    print(f"Fetched {len(results)} issues")
    for issue_type, data in results.items():
        print(f"\n{issue_type}: {data.get('key', 'N/A')}")
        description = get_issue_description(data)
        print(f"Description length: {len(description)} characters")
