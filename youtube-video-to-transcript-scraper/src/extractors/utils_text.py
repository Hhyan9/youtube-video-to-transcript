thonimport re
from typing import Dict, List

_WHITESPACE_RE = re.compile(r"\s+")
_INVISIBLE_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f]")

def strip_invisible_chars(text: str) -> str:
    """Remove zero-width and other invisible characters."""
    return _INVISIBLE_RE.sub("", text)

def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces."""
    text = strip_invisible_chars(text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()

def join_segments(segments: List[Dict[str, str]], separator: str = " ") -> str:
    """
    Join a list of transcript segments (from youtube-transcript-api)
    into a single string.

    Each segment is expected to have at least a "text" field.
    """
    texts: List[str] = []
    for seg in segments:
        txt = str(seg.get("text", "")).strip()
        if not txt:
            continue
        texts.append(txt)

    return normalize_whitespace(separator.join(texts))