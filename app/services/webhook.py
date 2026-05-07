from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

from app.services.chat import generate_response
from app.services.database import init_db
from app.services.rag import get_vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_vectorstore()  # build & cache vector store on startup
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(Body: str = Form(), From: str = Form()):
    reply = generate_response(phone_number=From, user_message=Body)
    response = MessagingResponse()
    response.message(reply)
    return Response(content=str(response), media_type="application/xml")
