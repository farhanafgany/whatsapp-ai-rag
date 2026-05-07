import os

from dotenv import load_dotenv
from openai import OpenAI
from twilio.rest import Client as TwilioClient

from app.services.database import get_history, save_message
from app.services.rag import retrieve

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = """\
Kamu adalah Nex, asisten customer service virtual Nexora Electronics — toko spesialis aksesoris komputer dan gadget.

Tugasmu membantu pelanggan dengan:
- Informasi produk (spesifikasi, harga, ketersediaan stok)
- Kebijakan toko (pengiriman, retur, garansi)
- Pertanyaan umum seputar toko
- Rekomendasi produk sesuai kebutuhan pelanggan

Panduan menjawab:
- Gunakan bahasa yang sama dengan pelanggan (Indonesia atau Inggris)
- Jawab dengan ramah, sopan, dan ringkas
- Hanya gunakan informasi dari konteks yang diberikan
- Jika informasi tidak tersedia dalam konteks, jujur katakan dan arahkan ke support@nexoraelectronics.com atau www.nexoraelectronics.com
- Jangan mengarang harga, stok, atau kebijakan yang tidak ada di konteks
- Untuk pembelian, arahkan pelanggan ke www.nexoraelectronics.com\
"""


HANDOFF_KEYWORDS = [
    "bicara dengan cs", "bicara dengan admin", "bicara dengan manusia",
    "hubungi cs", "hubungi admin", "sambungkan ke cs", "sambungkan ke admin",
    "minta tolong cs", "speak to human", "talk to human", "human agent",
    "talk to agent", "connect to agent", "real person",
]

HANDOFF_REPLY = (
    "Baik, permintaan kamu sudah saya teruskan ke tim CS kami. "
    "Mohon tunggu sebentar, tim kami akan segera menghubungimu. "
    "Ada yang bisa saya bantu sementara menunggu?"
)


def _is_handoff_request(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in HANDOFF_KEYWORDS)


def _notify_admin(phone_number: str, user_message: str) -> None:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    admin = os.getenv("ADMIN_WHATSAPP_NUMBER", "")
    from_num = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")

    if not admin:
        print(f"[handoff] ADMIN_WHATSAPP_NUMBER not set — skip notification for {phone_number}")
        return

    if not from_num.startswith("whatsapp:"):
        from_num = f"whatsapp:{from_num}"

    try:
        TwilioClient(sid, token).messages.create(
            from_=from_num,
            to=f"whatsapp:{admin}",
            body=(
                f"[ESKALASI CS]\n\n"
                f"Nomor: {phone_number}\n"
                f'Pesan: "{user_message}"\n\n'
                f"User meminta dihubungkan dengan human agent."
            ),
        )
    except Exception as exc:
        print(f"[handoff] Failed to notify admin: {exc}")


def generate_response(phone_number: str, user_message: str) -> str:
    if _is_handoff_request(user_message):
        _notify_admin(phone_number, user_message)
        save_message(phone_number, "user", user_message)
        save_message(phone_number, "assistant", HANDOFF_REPLY)
        return HANDOFF_REPLY

    context = retrieve(user_message)
    history = get_history(phone_number)

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nKonteks informasi toko:\n{context}"},
        *history,
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )

    answer = response.choices[0].message.content

    save_message(phone_number, "user", user_message)
    save_message(phone_number, "assistant", answer)

    return answer
