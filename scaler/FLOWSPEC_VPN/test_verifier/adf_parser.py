#!/usr/bin/env python3
"""
ADF Parser - Parse Atlassian Document Format (ADF) from Jira

This module parses Jira's Atlassian Document Format (ADF) from the
Test Description custom field (customfield_11772) and converts it
to markdown/text format for easier parsing.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def parse_adf_to_markdown(adf_doc: Dict[str, Any]) -> str:
    """
    Parse ADF document structure to markdown format
    
    Args:
        adf_doc: ADF document structure (from customfield_11772.value)
    
    Returns:
        Markdown-formatted string
    """
    if not isinstance(adf_doc, dict):
        return ""
    
    if adf_doc.get("type") != "doc":
        logger.warning(f"ADF document type is not 'doc': {adf_doc.get('type')}")
        return ""
    
    content = adf_doc.get("content", [])
    if not content:
        return ""
    
    markdown_parts = []
    _parse_content(content, markdown_parts, level=0)
    
    return "\n".join(markdown_parts)


def _parse_content(content: List[Dict], markdown_parts: List[str], level: int = 0):
    """Recursively parse ADF content nodes"""
    for node in content:
        node_type = node.get("type")
        
        if node_type == "paragraph":
            _parse_paragraph(node, markdown_parts)
        elif node_type == "heading":
            _parse_heading(node, markdown_parts)
        elif node_type == "orderedList":
            _parse_ordered_list(node, markdown_parts, level)
        elif node_type == "bulletList":
            _parse_bullet_list(node, markdown_parts, level)
        elif node_type == "listItem":
            _parse_list_item(node, markdown_parts, level)
        elif node_type == "codeBlock":
            _parse_code_block(node, markdown_parts)
        elif node_type == "hardBreak":
            markdown_parts.append("")
        elif node_type == "text":
            _parse_text(node, markdown_parts)
        else:
            # Unknown node type - try to extract text from content
            if "content" in node:
                _parse_content(node["content"], markdown_parts, level)


def _parse_paragraph(node: Dict, markdown_parts: List[str]):
    """Parse paragraph node"""
    if "content" in node:
        text_parts = []
        _extract_text_from_content(node["content"], text_parts)
        text = "".join(text_parts).strip()
        if text:
            markdown_parts.append(text)


def _parse_heading(node: Dict, markdown_parts: List[str]):
    """Parse heading node"""
    level = node.get("attrs", {}).get("level", 1)
    if "content" in node:
        text_parts = []
        _extract_text_from_content(node["content"], text_parts)
        text = "".join(text_parts).strip()
        if text:
            markdown_parts.append(f"{'#' * level} {text}")


def _parse_ordered_list(node: Dict, markdown_parts: List[str], level: int = 0):
    """Parse ordered list node"""
    if "content" in node:
        items = node["content"]
        for i, item in enumerate(items, 1):
            if item.get("type") == "listItem":
                text_parts = []
                _extract_text_from_content(item.get("content", []), text_parts)
                text = "".join(text_parts).strip()
                if text:
                    indent = "  " * level
                    markdown_parts.append(f"{indent}{i}. {text}")


def _parse_bullet_list(node: Dict, markdown_parts: List[str], level: int = 0):
    """Parse bullet list node"""
    if "content" in node:
        items = node["content"]
        for item in items:
            if item.get("type") == "listItem":
                text_parts = []
                _extract_text_from_content(item.get("content", []), text_parts)
                text = "".join(text_parts).strip()
                if text:
                    indent = "  " * level
                    markdown_parts.append(f"{indent}- {text}")


def _parse_list_item(node: Dict, markdown_parts: List[str], level: int = 0):
    """Parse list item node"""
    if "content" in node:
        text_parts = []
        _extract_text_from_content(node["content"], text_parts)
        text = "".join(text_parts).strip()
        if text:
            indent = "  " * level
            markdown_parts.append(f"{indent}- {text}")


def _parse_code_block(node: Dict, markdown_parts: List[str]):
    """Parse code block node"""
    if "content" in node:
        text_parts = []
        _extract_text_from_content(node["content"], text_parts)
        code = "".join(text_parts)
        if code:
            markdown_parts.append("```")
            markdown_parts.append(code)
            markdown_parts.append("```")


def _parse_text(node: Dict, markdown_parts: List[str]):
    """Parse text node with formatting"""
    text = node.get("text", "")
    if not text:
        return
    
    # Apply formatting marks
    marks = node.get("marks", [])
    for mark in marks:
        mark_type = mark.get("type")
        if mark_type == "strong":
            text = f"**{text}**"
        elif mark_type == "em":
            text = f"*{text}*"
        elif mark_type == "code":
            text = f"`{text}`"
        elif mark_type == "underline":
            # Markdown doesn't have underline, use emphasis
            text = f"*{text}*"
    
    # Append to last part or create new
    if markdown_parts and not markdown_parts[-1].endswith("\n"):
        markdown_parts[-1] += text
    else:
        markdown_parts.append(text)


def _extract_text_from_content(content: List[Dict], text_parts: List[str]):
    """Extract plain text from content array"""
    for item in content:
        if item.get("type") == "text":
            text = item.get("text", "")
            marks = item.get("marks", [])
            
            # Apply formatting
            for mark in marks:
                mark_type = mark.get("type")
                if mark_type == "strong":
                    text = f"**{text}**"
                elif mark_type == "em":
                    text = f"*{text}*"
                elif mark_type == "code":
                    text = f"`{text}`"
            
            text_parts.append(text)
        elif item.get("type") == "hardBreak":
            text_parts.append("\n")
        elif "content" in item:
            _extract_text_from_content(item["content"], text_parts)


def extract_text_from_adf(adf_doc: Dict[str, Any]) -> str:
    """
    Extract plain text from ADF document (simpler version, no markdown formatting)
    
    Args:
        adf_doc: ADF document structure
    
    Returns:
        Plain text string
    """
    if not isinstance(adf_doc, dict):
        return ""
    
    text_parts = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "text":
                text_parts.append(obj.get("text", ""))
            elif obj.get("type") == "hardBreak":
                text_parts.append("\n")
            elif "content" in obj:
                for item in obj["content"]:
                    extract_recursive(item)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
    
    if adf_doc.get("type") == "doc" and "content" in adf_doc:
        extract_recursive(adf_doc["content"])
    
    return "".join(text_parts)


if __name__ == "__main__":
    # Test with sample ADF
    sample_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Test Steps"}]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "1. First step"},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "2. Second step"}
                ]
            }
        ]
    }
    
    result = parse_adf_to_markdown(sample_adf)
    print("Parsed markdown:")
    print(result)
