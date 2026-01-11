def escape_markdown(text: str) -> str:
    """Escapes markdown characters in a string."""
    return text.replace("*", "\\*").replace("_", "\\_").replace("~", "\\~").replace("|", "\\|")