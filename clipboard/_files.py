"""File-list clipboard read with injectable backends (no Pillow needed)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, NoReturn
from urllib.parse import unquote, urlparse

from ._errors import ClipboardContentError, _call_content_backend


def _default_files_clipboard_reader() -> object:
    """Structure-only stub until platform file-list readers land.

    Raises rather than returning ``None`` so an unimplemented native path is
    not mistaken for ordinary file-list absence. Inject a fake via
    ``set_files_clipboard_reader`` for desktop-free tests.
    """
    raise ClipboardContentError(
        "paste_files native file-list reader is not available yet; "
        "inject a reader with set_files_clipboard_reader for tests"
    )


_files_clipboard_reader: Callable[[], object] = _default_files_clipboard_reader


def set_files_clipboard_reader(reader: Callable[[], object] | None) -> None:
    """Inject a file-list clipboard reader (tests / fakes).

    The reader returns a raw offer shape that ``paste_files`` normalizes:
    ``None`` / absence kinds → ``None``; path-list (``list[str]``) or structured
    ``uri-list`` / ``paths`` offers → ordered local paths; failures raise
    ``ClipboardContentError``. Platform adapters (later slices) can return the
    same shapes. Cut/move companion fields on structured offers are ignored.
    """
    global _files_clipboard_reader
    _files_clipboard_reader = (
        _default_files_clipboard_reader if reader is None else reader
    )


def _raise_files_failure(detail: str) -> NoReturn:
    raise ClipboardContentError(f"clipboard file-list read failed: {detail}")


def _local_path_from_file_uri(uri: str) -> str | None:
    """Decode one ``file://`` URI to a local path, or ``None`` if non-local.

    Non-``file`` schemes are skipped (not fetched). Malformed ``file://``
    references that cannot yield a trustworthy path raise
    ``ClipboardContentError``.
    """
    stripped = uri.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "\x00" in stripped:
        _raise_files_failure(f"malformed file URI {stripped!r}")

    parsed = urlparse(stripped)
    scheme = parsed.scheme.lower()
    if scheme != "file":
        # Remote / non-file URI: skip without fetching (ordinary non-local).
        return None

    host = parsed.netloc.lower()
    if host not in ("", "localhost", "localhost."):
        return None

    path = unquote(parsed.path)
    if not path or path == "/":
        _raise_files_failure(f"malformed file URI {stripped!r}")
    if "\x00" in path:
        _raise_files_failure(f"malformed file URI {stripped!r}")
    return path


def _paths_from_uri_list(payload: object) -> list[str] | None:
    """Decode a ``text/uri-list`` payload to ordered local paths, or ``None``."""
    if not isinstance(payload, str):
        _raise_files_failure(
            f"uri-list payload must be str, got {type(payload).__name__}"
        )
    if "\x00" in payload:
        _raise_files_failure("corrupt uri-list metadata")

    paths: list[str] = []
    for line in payload.splitlines():
        local = _local_path_from_file_uri(line)
        if local is not None:
            paths.append(local)
    return paths or None


def _paths_from_path_list(paths: object) -> list[str] | None:
    """Accept a CF_HDROP-style path list; empty → ordinary absence."""
    if not isinstance(paths, list):
        _raise_files_failure(f"path list must be list, got {type(paths).__name__}")
    if not paths:
        return None
    if not all(isinstance(item, str) for item in paths):
        _raise_files_failure("corrupt path-list metadata (entries must be str)")
    if any("\x00" in item for item in paths):
        _raise_files_failure("corrupt path-list metadata")
    # Return a new list so callers cannot mutate the offer through the result.
    return list(paths)


def _uri_list_payload(offer: Mapping[str, Any]) -> object:
    if "uri_list" in offer:
        return offer["uri_list"]
    if "uri-list" in offer:
        return offer["uri-list"]
    return offer.get("data")


def _paths_from_structured_offer(offer: Mapping[str, Any]) -> list[str] | None:
    """Normalize a structured fake / adapter offer to local paths or ``None``.

    Recognized kinds: ``uri-list`` / ``text/uri-list``, ``paths``, and absence
    kinds ``text`` / ``text/plain``, ``image``, ``html`` / ``text/html``,
    ``empty``. Cut/move companion fields are ignored for all library behavior
    (no move/delete and no cut reissue).
    """
    kind = offer.get("kind")

    if kind in ("corrupt", "invalid"):
        detail = (
            offer.get("message") or offer.get("detail") or "corrupt file-list metadata"
        )
        _raise_files_failure(str(detail))

    if kind in ("uri-list", "text/uri-list"):
        return _paths_from_uri_list(_uri_list_payload(offer))

    if kind == "paths":
        return _paths_from_path_list(offer.get("paths"))

    if kind in ("text", "text/plain", "image", "html", "text/html", "empty"):
        return None

    # kind missing: infer from payload keys (cut-only / empty → absence).
    if "uri_list" in offer or "uri-list" in offer:
        return _paths_from_uri_list(_uri_list_payload(offer))
    if "paths" in offer:
        return _paths_from_path_list(offer.get("paths"))
    if kind is None:
        return None

    _raise_files_failure(f"unrecognized file-list offer kind {kind!r}")


def _normalize_files_offer(offer: object) -> list[str] | None:
    """Map a raw reader result to ``list[str]`` local paths or ordinary ``None``."""
    if offer is None:
        return None

    if isinstance(offer, list):
        return _paths_from_path_list(offer)

    if isinstance(offer, Mapping):
        return _paths_from_structured_offer(offer)

    # Bare strings are plain-text (or other non-file-list) offers — never parse
    # path-looking text as a file-list success.
    if isinstance(offer, str):
        return None

    _raise_files_failure(f"unrecognized file-list offer type {type(offer).__name__}")


def paste_files() -> list[str] | None:
    """Return local filesystem paths from a file-list clipboard offer, or None.

    Does not require the optional ``clipboard[images]`` extra. Ordinary local
    file-list absence is ``None``. Failures other than ordinary absence raise
    ``ClipboardContentError`` (not ``ClipboardImageError``). The default reader
    is a structure-only stub that raises until platform adapters land; tests
    inject a fake via ``set_files_clipboard_reader``.

    Injected readers may return path lists, structured ``uri-list`` / ``paths``
    offers (optional ignored cut markers), or absence kinds; ``paste_files``
    normalizes them the same way platform adapters will.
    """
    raw = _call_content_backend("file-list read", _files_clipboard_reader)
    return _normalize_files_offer(raw)
