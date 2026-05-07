import json
import os
import secrets
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.services.database import delete_history, get_all_users, get_full_history, get_stats

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
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; min-height: 100vh; }

  header { background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%); padding: 20px 32px; color: white; box-shadow: 0 4px 20px rgba(79,70,229,.25); }
  header h1 { font-size: 20px; font-weight: 700; letter-spacing: -.3px; }
  header p { font-size: 13px; opacity: .7; margin-top: 4px; }

  .container { max-width: 1100px; margin: 32px auto; padding: 0 24px; }

  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
  .stat-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 1px 6px rgba(0,0,0,.06); display: flex; align-items: center; gap: 16px; }
  .stat-icon { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
  .stat-icon.purple { background: #ede9fe; }
  .stat-icon.blue   { background: #dbeafe; }
  .stat-icon.green  { background: #dcfce7; }
  .stat-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
  .stat-value { font-size: 34px; font-weight: 700; color: #0f172a; margin-top: 4px; line-height: 1; }

  .card { background: white; border-radius: 16px; box-shadow: 0 1px 6px rgba(0,0,0,.06); overflow: hidden; margin-bottom: 24px; }
  .card-header { padding: 18px 24px; border-bottom: 1px solid #f1f5f9; font-weight: 600; font-size: 15px; display: flex; align-items: center; justify-content: space-between; }
  .card-header span { font-size: 13px; color: #94a3b8; font-weight: 400; }

  .chart-wrap { padding: 20px 24px 16px; }

  table { width: 100%; border-collapse: collapse; }
  thead { background: #f8fafc; }
  th { text-align: left; padding: 12px 24px; font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .08em; }
  td { padding: 15px 24px; border-top: 1px solid #f1f5f9; font-size: 14px; }
  tr:hover td { background: #f8fafc; }
  .phone { font-weight: 500; color: #0f172a; }
  .ts { color: #64748b; font-size: 13px; }

  .badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .badge-purple { background: #ede9fe; color: #6d28d9; }

  .btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; text-decoration: none; border: none; cursor: pointer; font-family: inherit; transition: opacity .15s; }
  .btn:hover { opacity: .85; }
  .btn-primary { background: #4f46e5; color: white; }
  .btn-back { background: #e2e8f0; color: #475569; margin-bottom: 20px; }
  .btn-danger { background: white; color: #ef4444; border: 1px solid #fecaca; }
  .btn-danger:hover { background: #fef2f2; opacity: 1; }

  .chat { display: flex; flex-direction: column; gap: 14px; padding: 24px; }
  .msg { max-width: 72%; }
  .msg.user { align-self: flex-end; text-align: right; }
  .msg.assistant { align-self: flex-start; }
  .bubble { display: inline-block; padding: 10px 16px; border-radius: 18px; font-size: 14px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
  .user .bubble { background: #4f46e5; color: white; border-bottom-right-radius: 4px; }
  .assistant .bubble { background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 4px; }
  .msg-ts { font-size: 11px; color: #94a3b8; margin-top: 5px; }

  .empty { padding: 64px; text-align: center; color: #94a3b8; font-size: 14px; }
  .empty-icon { font-size: 40px; margin-bottom: 12px; }

  @media (max-width: 640px) { .stats { grid-template-columns: 1fr; } }
</style>
"""


@router.get("/", response_class=HTMLResponse)
async def dashboard(_: str = Depends(_check_auth)):
    users = get_all_users()
    stats = get_stats()

    stat_cards = f"""
    <div class="stats">
      <div class="stat-card">
        <div class="stat-icon purple">&#128101;</div>
        <div><div class="stat-label">Total Pengguna</div><div class="stat-value">{stats['total_users']}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue">&#128172;</div>
        <div><div class="stat-label">Total Pesan</div><div class="stat-value">{stats['total_messages']}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">&#128197;</div>
        <div><div class="stat-label">Pesan Hari Ini</div><div class="stat-value">{stats['today_messages']}</div></div>
      </div>
    </div>
    """

    labels_json = json.dumps(stats["chart_labels"])
    values_json = json.dumps(stats["chart_values"])
    chart_card = f"""
    <div class="card">
      <div class="card-header">Aktivitas Pesan <span>14 hari terakhir</span></div>
      <div class="chart-wrap"><canvas id="activityChart" height="80"></canvas></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
    <script>
      new Chart(document.getElementById('activityChart'), {{
        type: 'bar',
        data: {{
          labels: {labels_json},
          datasets: [{{
            label: 'Pesan',
            data: {values_json},
            backgroundColor: 'rgba(79,70,229,.12)',
            borderColor: '#4f46e5',
            borderWidth: 2,
            borderRadius: 6,
          }}]
        }},
        options: {{
          responsive: true,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            y: {{ beginAtZero: true, ticks: {{ stepSize: 1, precision: 0 }}, grid: {{ color: '#f1f5f9' }} }},
            x: {{ grid: {{ display: false }} }}
          }}
        }}
      }});
    </script>
    """

    if users:
        def _row(u: dict) -> str:
            phone = u["phone_number"]
            encoded = quote(phone, safe="")
            return (
                f"<tr>"
                f"<td class='phone'>{phone}</td>"
                f"<td><span class='badge badge-purple'>{u['msg_count']} pesan</span></td>"
                f"<td class='ts'>{u['last_active']}</td>"
                f"<td>"
                f"<a class='btn btn-primary' href='/admin/history/{encoded}'>Lihat History</a> "
                f"<form style='display:inline' method='post' action='/admin/clear/{encoded}'"
                f" onsubmit=\"return confirm('Hapus seluruh history {phone}?')\">"
                f"<button type='submit' class='btn btn-danger'>Hapus</button>"
                f"</form>"
                f"</td></tr>"
            )
        rows = "".join(_row(u) for u in users)
        table = (
            "<table><thead><tr>"
            "<th>Nomor WhatsApp</th><th>Pesan</th><th>Terakhir Aktif</th><th>Aksi</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>"
        )
    else:
        table = '<div class="empty"><div class="empty-icon">&#128172;</div>Belum ada percakapan.</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin — Nexora Electronics</title>
  {_STYLE}
</head>
<body>
  <header>
    <h1>&#9889; Nexora Electronics</h1>
    <p>Admin Dashboard &mdash; Manajemen Percakapan WhatsApp</p>
  </header>
  <div class="container">
    {stat_cards}
    {chart_card}
    <div class="card">
      <div class="card-header">Pengguna <span>{len(users)} akun</span></div>
      {table}
    </div>
  </div>
</body>
</html>""")


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
        chat = '<div class="empty"><div class="empty-icon">&#128172;</div>Belum ada pesan.</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>History {phone} &mdash; Nexora Admin</title>
  {_STYLE}
</head>
<body>
  <header>
    <h1>&#9889; Nexora Electronics</h1>
    <p>History Percakapan &mdash; {phone}</p>
  </header>
  <div class="container">
    <div>
      <a class="btn btn-back" href="/admin/">&#8592; Kembali ke Dashboard</a>
      <form style="display:inline;margin-left:8px" method="post"
            action="/admin/clear/{quote(phone, safe='')}"
            onsubmit="return confirm('Hapus seluruh history {phone}?')">
        <button type="submit" class="btn btn-danger">Hapus History</button>
      </form>
    </div>
    <div class="card" style="margin-top:20px">
      {chat}
    </div>
  </div>
</body>
</html>""")


@router.post("/clear/{phone_number}")
async def clear_history(phone_number: str, _: str = Depends(_check_auth)):
    delete_history(unquote(phone_number))
    return RedirectResponse(url="/admin/", status_code=303)
