import os
import secrets
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.services.database import delete_history, get_all_users, get_full_history

router = APIRouter(prefix="/admin")
_security = HTTPBasic()


def _check_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    ok = secrets.compare_digest(credentials.password.encode(), password.encode())
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


_STYLE = """
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#1a1a1a}
  header{background:#1e293b;color:white;padding:16px 24px}
  header h1{font-size:18px;font-weight:600}
  header p{font-size:13px;opacity:.55;margin-top:3px}
  .container{max-width:960px;margin:28px auto;padding:0 20px}
  .card{background:white;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden;margin-bottom:24px}
  .card-header{padding:14px 20px;border-bottom:1px solid #f0f0f0;font-weight:600;font-size:15px}
  table{width:100%;border-collapse:collapse}
  th{text-align:left;padding:10px 20px;font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;background:#f9fafb}
  td{padding:13px 20px;border-top:1px solid #f0f0f0;font-size:14px}
  tr:hover td{background:#fafafa}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;background:#ede9fe;color:#6d28d9}
  .btn{display:inline-block;padding:6px 14px;border-radius:6px;font-size:13px;text-decoration:none;border:none;cursor:pointer;font-family:inherit}
  .btn-view{background:#3b82f6;color:white;margin-right:6px}
  .btn-back{background:#6b7280;color:white;display:inline-block;margin-bottom:16px}
  .btn-clear{background:white;color:#ef4444;border:1px solid #fca5a5}
  .btn-clear:hover{background:#fef2f2}
  .empty{padding:60px;text-align:center;color:#9ca3af;font-size:14px}
  .ts{color:#9ca3af;font-size:12px}
  .chat{display:flex;flex-direction:column;gap:12px;padding:20px}
  .msg{max-width:75%}
  .msg.user{align-self:flex-end;text-align:right}
  .msg.assistant{align-self:flex-start}
  .bubble{display:inline-block;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
  .user .bubble{background:#3b82f6;color:white;border-bottom-right-radius:4px}
  .assistant .bubble{background:#f3f4f6;color:#1a1a1a;border-bottom-left-radius:4px}
  .msg-ts{font-size:11px;color:#9ca3af;margin-top:4px}
</style>
"""


@router.get("/", response_class=HTMLResponse)
async def dashboard(_: str = Depends(_check_auth)):
    users = get_all_users()

    if users:
        def _row(u: dict) -> str:
            phone = u["phone_number"]
            encoded = quote(phone, safe="")
            return (
                f"<tr>"
                f"<td>{phone}</td>"
                f"<td><span class='badge'>{u['msg_count']} pesan</span></td>"
                f"<td class='ts'>{u['last_active']}</td>"
                f"<td>"
                f"<a class='btn btn-view' href='/admin/history/{encoded}'>Lihat</a>"
                f"<form style='display:inline' method='post' action='/admin/clear/{encoded}'"
                f" onsubmit=\"return confirm('Hapus seluruh history {phone}?')\">"
                f"<button type='submit' class='btn btn-clear'>Hapus</button>"
                f"</form>"
                f"</td></tr>"
            )

        rows = "".join(_row(u) for u in users)
        table = (
            "<table><tr>"
            "<th>Nomor WhatsApp</th><th>Pesan</th><th>Terakhir Aktif</th><th>Aksi</th>"
            f"</tr>{rows}</table>"
        )
    else:
        table = '<div class="empty">Belum ada percakapan.</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — Nexora Electronics</title>{_STYLE}</head>
<body>
  <header><h1>Nexora Electronics — Admin Dashboard</h1><p>Manajemen percakapan WhatsApp</p></header>
  <div class="container">
    <div class="card">
      <div class="card-header">Pengguna ({len(users)})</div>
      {table}
    </div>
  </div>
</body></html>""")


@router.get("/history/{phone_number}", response_class=HTMLResponse)
async def view_history(phone_number: str, _: str = Depends(_check_auth)):
    phone = unquote(phone_number)
    messages = get_full_history(phone)

    if messages:
        bubbles = "".join(
            f"""<div class="msg {m['role']}">
              <div class="bubble">{m['content']}</div>
              <div class="msg-ts">{m['timestamp']}</div>
            </div>"""
            for m in messages
        )
        chat = f'<div class="chat">{bubbles}</div>'
    else:
        chat = '<div class="empty">Belum ada pesan.</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>History {phone} — Nexora Admin</title>{_STYLE}</head>
<body>
  <header><h1>History Percakapan</h1><p>{phone}</p></header>
  <div class="container">
    <a class="btn btn-back" href="/admin/">Kembali ke Dashboard</a>
    <form style="display:inline;margin-left:8px" method="post"
          action="/admin/clear/{quote(phone, safe='')}"
          onsubmit="return confirm('Hapus seluruh history {phone}?')">
      <button type="submit" class="btn btn-clear">Hapus History</button>
    </form>
    <div class="card" style="margin-top:16px">
      {chat}
    </div>
  </div>
</body></html>""")


@router.post("/clear/{phone_number}")
async def clear_history(phone_number: str, _: str = Depends(_check_auth)):
    delete_history(unquote(phone_number))
    return RedirectResponse(url="/admin/", status_code=303)
