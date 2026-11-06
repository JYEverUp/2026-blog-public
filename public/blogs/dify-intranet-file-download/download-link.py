import re
from typing import TypedDict
from urllib.parse import parse_qs, unquote_plus, urlsplit


class DownloadLink(TypedDict):
    ready: bool
    relative_url: str
    download_markdown: str
    notice: str


def main(status_code: int, files: list[dict[str, object]]) -> DownloadLink:
    result = DownloadLink(
        ready=False, relative_url="", download_markdown="",
        notice="下载链接缺失或不完整，请重新查询日报后再试。",
    )
    if status_code != 200 or not isinstance(files, list) or len(files) != 1:
        return result
    file = files[0]
    if not isinstance(file, dict):
        return result
    mime = str(file.get("mime_type", file.get("mimetype", ""))).split(";", 1)[0].strip().lower()
    if mime != "application/pdf":
        return result
    raw = file.get("url") or file.get("remote_url")
    if not isinstance(raw, str) or len(raw) > 8192:
        return result
    raw = raw.replace("&amp;", "&")
    if any(ord(character) <= 32 or ord(character) == 127 for character in raw):
        return result
    try:
        parsed = urlsplit(raw)
        if parsed.scheme not in ("", "http", "https") or parsed.fragment:
            return result
        if (parsed.netloc and not parsed.scheme) or parsed.username is not None:
            return result
        if parsed.scheme and not parsed.netloc:
            return result
        if not re.fullmatch(
            r"/files/tools/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.pdf", parsed.path
        ):
            return result
        params = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
        required = {"timestamp", "nonce", "sign"}
        if not required.issubset(params) or set(params) - required - {"as_attachment"}:
            return result
        if any(len(values) != 1 for values in params.values()):
            return result
        if not re.fullmatch(r"[0-9]{1,12}", params["timestamp"][0]):
            return result
        if not re.fullmatch(r"[0-9a-fA-F]{32}", params["nonce"][0]):
            return result
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}=", params["sign"][0]):
            return result
        # Preserve the original signed parameter bytes; only set download disposition.
        pairs = [pair for pair in parsed.query.split("&")
                 if unquote_plus(pair.partition("=")[0]) != "as_attachment"]
        relative = parsed.path + "?" + "&".join(pairs) + "&as_attachment=true"
    except (ValueError, TypeError):
        return result
    return {
        "ready": True, "relative_url": relative,
        "download_markdown": f"[点击下载 PDF]({relative})", "notice": "",
    }
