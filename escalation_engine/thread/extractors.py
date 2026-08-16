import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any


@dataclass(frozen=True)
class ExtractedMessageContent:
    """The new, human-authored portion extracted from one email message."""

    text: str
    source: str
    quoted_content_removed: bool = False
    signature_removed: bool = False


_HTML_QUOTE_MARKER = re.compile(
    r"""
    <(?:
        blockquote\b
        |
        div\b[^>]*(?:id|class)\s*=\s*["'][^"']*(?:
            appendonsend|divrplyfwdmsg|gmail_quote|gmail_extra|
            yahoo_quoted|protonmail_quote
        )[^"']*["']
    )
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE
)
_HTML_SIGNATURE_MARKER = re.compile(
    r"""
    <(?:div|span|table)\b[^>]*(?:id|class)\s*=\s*["'][^"']*(?:
        email[-_]?signature|signature
    )[^"']*["']
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE
)
_TEXT_QUOTE_MARKERS = (
    re.compile(r"(?im)^\s*_{5,}\s*$"),
    re.compile(
        r"(?im)^\s*-{2,}\s*(?:original|forwarded|mensaje original|"
        r"mensaje reenviado)[^\n]*-{2,}\s*$"
    ),
    re.compile(r"(?im)^\s*on\s+.+\s+wrote:\s*$"),
    re.compile(r"(?im)^\s*el\s+.+\s+escribi[oó]:\s*$"),
    re.compile(
        r"(?im)^\s*(?:from|de):\s*[^\n]+\n\s*"
        r"(?:sent|date|enviado|fecha):\s*"
    ),
)
_TEXT_SIGNATURE_MARKERS = (
    re.compile(r"(?m)^\s*--\s*$"),
    re.compile(
        r"(?im)^\s*(?:sent from my|enviado desde mi|"
        r"get outlook for (?:ios|android))\b"
    ),
)
_BLOCK_TAGS = {
    "address", "article", "br", "div", "footer", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "hr", "li", "p", "section", "table",
    "td", "th", "tr"
}
_IGNORED_HTML_TAGS = {"head", "script", "style"}


class _HTMLToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_tag: str | None = None
        self._parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        normalized_tag = tag.lower()

        if self._ignored_tag is not None:
            return

        if normalized_tag in _IGNORED_HTML_TAGS:
            self._ignored_tag = normalized_tag
            return

        if normalized_tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()

        if self._ignored_tag is not None:
            if normalized_tag == self._ignored_tag:
                self._ignored_tag = None
            return

        if normalized_tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_tag is None:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def get_subject(message: dict[str, Any]) -> str:
    value = message.get("subject")

    return value if isinstance(value, str) else ""


def get_preview(message: dict[str, Any]) -> str:
    value = message.get("bodyPreview")

    return value if isinstance(value, str) else ""


def get_sender_address(message: dict[str, Any]) -> str | None:
    sender = message.get("from")

    if not isinstance(sender, dict):
        return None

    email_address = sender.get("emailAddress")

    if not isinstance(email_address, dict):
        return None

    address = email_address.get("address")

    return address if isinstance(address, str) else None


def get_headers(
    message: dict[str, Any]
) -> dict[str, Any] | list[Any] | str | None:
    value = message.get("headers")

    if value is None:
        value = message.get("internetMessageHeaders")

    return value if isinstance(value, (dict, list, str)) else None


def get_received_datetime(message: dict[str, Any]) -> str | None:
    value = message.get("receivedDateTime")

    return value if isinstance(value, str) else None


def parse_received_datetime(message: dict[str, Any]) -> datetime | None:
    """Parse a message timestamp and normalize it to naive UTC."""
    value = get_received_datetime(message)

    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed


def get_message_content(message: dict[str, Any]) -> ExtractedMessageContent:
    """
    Extract only the new content authored in one email.

    Graph's ``uniqueBody`` is preferred when available. Otherwise ``body`` is
    cleaned of HTML, signatures, and quoted reply history. ``bodyPreview`` is
    a safe fallback for legacy/test payloads and is cleaned with the same
    plain-text reply markers.
    """
    candidates = (
        ("uniqueBody", message.get("uniqueBody")),
        ("body", message.get("body")),
    )

    for source, value in candidates:
        raw_content, content_type = _read_body_value(value)

        if not raw_content.strip():
            continue

        extracted = _clean_message_content(raw_content, content_type)

        if extracted.text:
            return ExtractedMessageContent(
                text=extracted.text,
                source=source,
                quoted_content_removed=extracted.quoted_content_removed,
                signature_removed=extracted.signature_removed
            )

    preview = get_preview(message)

    if preview.strip():
        extracted = _clean_plain_text(preview)
        return ExtractedMessageContent(
            text=extracted.text,
            source="bodyPreview",
            quoted_content_removed=extracted.quoted_content_removed,
            signature_removed=extracted.signature_removed
        )

    return ExtractedMessageContent(text="", source="none")


def get_message_body_text(message: dict[str, Any]) -> str:
    """Return the cleaned, newly-authored body text for one message."""
    return get_message_content(message).text


def get_message_text(message: dict[str, Any]) -> str:
    """Return subject plus the cleaned, newly-authored body text."""
    return f"{get_subject(message)} {get_message_body_text(message)}".strip()


def _read_body_value(value: Any) -> tuple[str, str]:
    if isinstance(value, str):
        return value, "text"

    if not isinstance(value, dict):
        return "", "text"

    content = value.get("content")
    content_type = value.get("contentType")

    if not isinstance(content, str):
        return "", "text"

    normalized_type = (
        content_type.lower()
        if isinstance(content_type, str)
        else "html" if _looks_like_html(content) else "text"
    )

    return content, normalized_type


def _clean_message_content(
    content: str,
    content_type: str
) -> ExtractedMessageContent:
    if content_type == "html" or _looks_like_html(content):
        return _clean_html(content)

    return _clean_plain_text(content)


def _clean_html(content: str) -> ExtractedMessageContent:
    quote_match = _HTML_QUOTE_MARKER.search(content)
    signature_match = _HTML_SIGNATURE_MARKER.search(content)
    cut_positions = [
        match.start()
        for match in (quote_match, signature_match)
        if match is not None
    ]
    current_html = content[:min(cut_positions)] if cut_positions else content
    parser = _HTMLToTextParser()

    try:
        parser.feed(current_html)
        parser.close()
        plain_text = parser.text()
    except (AssertionError, ValueError):
        # HTMLParser is deliberately forgiving, but malformed payloads should
        # still fall back to tag removal instead of failing the Function.
        plain_text = re.sub(r"<[^>]+>", " ", current_html)

    cleaned_text = _clean_plain_text(plain_text)

    return ExtractedMessageContent(
        text=cleaned_text.text,
        source="",
        quoted_content_removed=(
            quote_match is not None or cleaned_text.quoted_content_removed
        ),
        signature_removed=(
            signature_match is not None or cleaned_text.signature_removed
        )
    )


def _clean_plain_text(content: str) -> ExtractedMessageContent:
    decoded = html.unescape(content).replace("\r\n", "\n").replace("\r", "\n")
    quote_position = _first_match_position(decoded, _TEXT_QUOTE_MARKERS)
    signature_position = _first_match_position(decoded, _TEXT_SIGNATURE_MARKERS)
    cut_positions = [
        position
        for position in (quote_position, signature_position)
        if position is not None
    ]
    current_text = decoded[:min(cut_positions)] if cut_positions else decoded

    return ExtractedMessageContent(
        text=_normalize_whitespace(current_text),
        source="",
        quoted_content_removed=quote_position is not None,
        signature_removed=signature_position is not None
    )


def _first_match_position(
    value: str,
    patterns: tuple[re.Pattern[str], ...]
) -> int | None:
    positions = [
        match.start()
        for pattern in patterns
        if (match := pattern.search(value)) is not None
    ]

    return min(positions) if positions else None


def _normalize_whitespace(value: str) -> str:
    normalized_lines = []
    previous_blank = False

    for line in value.replace("\xa0", " ").split("\n"):
        normalized_line = re.sub(r"[ \t\f\v]+", " ", line).strip()

        if not normalized_line:
            if normalized_lines and not previous_blank:
                normalized_lines.append("")
            previous_blank = True
            continue

        normalized_lines.append(normalized_line)
        previous_blank = False

    return "\n".join(normalized_lines).strip()


def _looks_like_html(value: str) -> bool:
    return bool(re.search(r"<\s*(?:html|body|div|p|br|table|span)\b", value, re.I))
