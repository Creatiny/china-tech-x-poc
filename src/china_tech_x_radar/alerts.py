from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


class FeishuSender:
    def __init__(self) -> None:
        self.base = os.environ.get("FEISHU_API_BASE", "https://open.feishu.cn").rstrip("/")
        self.app_id = os.environ.get("FEISHU_APP_ID", "")
        self.app_secret = os.environ.get("FEISHU_APP_SECRET", "")
        self.receive_id = os.environ.get("CHINA_TECH_FEISHU_RECEIVE_ID", "")
        self.receive_id_type = os.environ.get("CHINA_TECH_FEISHU_RECEIVE_ID_TYPE", "open_id")
        self._token: str | None = None

    def available(self) -> bool:
        return bool(self.app_id and self.app_secret and self.receive_id)

    def _tenant_token(self) -> str:
        if self._token:
            return self._token
        req = urllib.request.Request(
            self.base + "/open-apis/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": self.app_id, "app_secret": self.app_secret}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        token = data.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"Feishu token error code={data.get('code')} msg={data.get('msg')}")
        self._token = token
        return token

    def send_text(self, text: str) -> str:
        if not self.available():
            raise RuntimeError("Feishu channel is not fully configured")
        token = self._tenant_token()
        payload = {
            "receive_id": self.receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        req = urllib.request.Request(
            self.base + f"/open-apis/im/v1/messages?receive_id_type={self.receive_id_type}",
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        if data.get("code") != 0:
            raise RuntimeError(f"Feishu send error code={data.get('code')} msg={data.get('msg')}")
        return str((data.get("data") or {}).get("message_id") or "")


def format_alert(signal: dict[str, Any]) -> str:
    published = signal.get("published_at") or "unknown"
    lines = [
        f"[{signal['priority']}] China Tech X signal #{signal['id']}",
        "",
        signal.get("title") or "",
        "",
        f"Source: {signal.get('source_name')} | Published: {published}",
        f"Why: {signal.get('reason')}",
        f"Source link: {signal.get('canonical_url') or 'N/A'}",
        f"X target: {signal.get('target_mode')}",
        f"X live search: {signal.get('x_search_url') or 'N/A'}",
        "",
        signal.get("suggested_angle") or "",
        "",
        "Action: find a strong target post, reply only if you can add a non-generic China-specific fact or implication. X publishing remains manual.",
    ]
    return "\n".join(lines)
