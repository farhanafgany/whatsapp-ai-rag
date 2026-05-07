from dotenv import load_dotenv
from openai import OpenAI

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


def generate_response(phone_number: str, user_message: str) -> str:
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
