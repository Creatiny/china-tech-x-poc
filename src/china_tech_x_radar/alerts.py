from __future__ import annotations

import json
import mimetypes
import os
import uuid
import urllib.request
from pathlib import Path
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

    def _send(self, msg_type: str, content: dict[str, Any]) -> str:
        if not self.available():
            raise RuntimeError("Feishu channel is not fully configured")
        token = self._tenant_token()
        payload = {"receive_id": self.receive_id, "msg_type": msg_type, "content": json.dumps(content, ensure_ascii=False)}
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

    def send_text(self, text: str) -> str:
        return self._send("text", {"text": text})

    def upload_image(self, path: str | Path) -> str:
        path = Path(path)
        token = self._tenant_token()
        boundary = "----ChinaTech" + uuid.uuid4().hex
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        file_bytes = path.read_bytes()
        parts = []
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image_type\"\r\n\r\nmessage\r\n".encode())
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n".encode())
        parts.append(file_bytes)
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(
            self.base + "/open-apis/im/v1/images",
            data=body,
            headers={"Authorization": "Bearer " + token, "Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        if data.get("code") != 0 or not (data.get("data") or {}).get("image_key"):
            raise RuntimeError(f"Feishu image upload error code={data.get('code')} msg={data.get('msg')}")
        return str(data["data"]["image_key"])

    def send_image(self, path: str | Path) -> str:
        image_key = self.upload_image(path)
        return self._send("image", {"image_key": image_key})


def format_publish_packet(signal: dict[str, Any], packet: dict[str, Any], *, has_asset: bool) -> str:
    decision = str(packet.get("decision") or "SKIP").upper()
    priority = str(signal.get("priority") or "P1").upper()
    urgency = int(packet.get("urgency_minutes") or 0)
    action_short = "POST" if decision == "POST" else "REPLY"
    action_cn = "发 ORIGINAL POST" if decision == "POST" else "去目标帖 REPLY"
    confidence = packet.get("confidence")
    content_group = str(packet.get("content_group") or "").upper()
    group_labels = {
        "A_NEWS_FACT": "A 新闻/事实型",
        "B_OPINION_VALUE": "B 观点/价值型",
    }
    group_label = group_labels.get(content_group)
    if priority == "P0":
        priority_head = "🔥 P0"
        priority_desc = "最高优先级：优先于其他候选处理"
        urgency_head = "立即" if not urgency or urgency <= 60 else f"{urgency}分钟内"
    else:
        priority_head = "P1"
        priority_desc = "高价值机会：已通过 P1 推送门槛"
        urgency_head = f"{urgency}分钟内" if urgency else "尽快"

    lines = [
        f"【{priority_head}｜{action_short}{'｜' + group_label if group_label else ''}｜{urgency_head}】",
        f"信号：{signal.get('title') or ''}",
        f"级别：{priority}｜{priority_desc}",
        f"结论：{action_cn}" + (f"｜置信度 {confidence:.0%}" if isinstance(confidence, (int, float)) else ""),
        f"时效：{'尽快，约 ' + str(urgency) + ' 分钟内' if urgency else '尽快处理'}",
        "",
        f"为什么：{packet.get('reason') or ''}",
    ]
    if group_label:
        lines += [f"实验分组：{group_label}"]
    if packet.get("core_position"):
        lines += [f"核心观点：{packet.get('core_position')}"]
    if decision == "REPLY":
        lines += [f"目标帖：{packet.get('target_url') or 'N/A'}", f"目标账号：{packet.get('target_account') or 'N/A'}"]
    lines += [
        "",
        "【最终文案｜直接复制】",
        str(packet.get("final_copy") or ""),
        "",
        f"配图：{'已附原创数据卡，直接保存后随帖发布' if has_asset else ('不建议配图，纯文本更适合这条' if decision == 'REPLY' else '这条不需要为了配图硬加图')}",
        f"发布提示：{packet.get('publish_note') or '按上面文案直接发布。'}",
        "",
        f"来源：{packet.get('source_url') or signal.get('canonical_url') or 'N/A'}",
        f"实验标签：{packet.get('angle_type') or 'OTHER'}",
    ]
    lines += [
        "",
        "发布后把 X 链接发给 ChatGPT，我会继续追踪 impressions → followers 并纳入增长公式。",
    ]
    return "\n".join(lines)
