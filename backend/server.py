from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
import random
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    language: str

@api_router.get("/")
async def root():
    return {"message": "AUREN - AI Healing & Self-Reflection"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat(input: ChatMessage):
    user_message = input.message.strip()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        detected_language = "en"
        french_indicators = ["je", "tu", "il", "elle", "nous", "vous", "ils", "elles", 
                           "suis", "es", "est", "sommes", "êtes", "sont",
                           "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
                           "le", "la", "les", "un", "une", "des", "ça", "où", "été",
                           "ai", "as", "a", "avons", "avez", "ont",
                           "me", "te", "se", "ce", "de", "ne", "que", "qui",
                           "mais", "pour", "avec", "sans", "dans", "sur", "très", "bien",
                           "bonjour", "bonsoir", "merci", "comment", "quoi", "quand"]
        
        message_lower = user_message.lower()
        words = message_lower.split()
        french_word_count = sum(1 for word in words if word in french_indicators)
        
        if french_word_count >= 1:
            detected_language = "fr"
        
        system_message = """
You are Thoth, a calm, wise, and deeply insightful guide for emotional healing and self-reflection.

Your purpose:
- Help users reflect and understand themselves
- Ask powerful, open-ended questions that invite deeper thought
- Avoid generic advice or clichés
- Be honest but never harsh
- Keep responses concise and meaningful (2-4 sentences maximum)
- Do not give medical or clinical advice
- Listen deeply and respond with wisdom

Your tone:
- Calm and grounded
- Deep and thoughtful
- Human and empathetic
- Warm and conversational
- Slightly spiritual but practical

Writing style:
- Never use em dashes in your responses
- Use commas, periods, or colons instead
- Make your writing feel natural, elegant, and reflective
- Avoid robotic or overly formal language

IMPORTANT:
- If the user writes in French, respond ONLY in French
- If the user writes in English, respond ONLY in English
- Match their language naturally and fluently
- Never mix languages in a single response
"""
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        chat_instance = LlmChat(
            api_key=api_key,
            session_id="auren_reflection",
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        user_msg = UserMessage(text=user_message)
        ai_response = await chat_instance.send_message(user_msg)
        
        return ChatResponse(response=ai_response, language=detected_language)
    
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/daily-reflection")
async def get_daily_reflection():
    reflections_en = [
        "What part of yourself are you still learning to accept?",
        "When do you feel most alive?",
        "What would you do if you trusted yourself completely?",
        "Which emotion are you avoiding right now?",
        "What story about yourself are you ready to release?",
        "What does your body need that your mind keeps ignoring?",
        "If your younger self could see you now, what would surprise them most?",
        "What truth have you been whispering to yourself lately?",
        "Where do you feel most at peace with who you are?",
        "What are you carrying that no longer serves you?"
    ]
    
    reflections_fr = [
        "Quelle partie de vous acceptez-vous encore difficilement?",
        "Quand vous sentez-vous le plus vivant?",
        "Que feriez-vous si vous vous faisiez totalement confiance?",
        "Quelle émotion évitez-vous en ce moment?",
        "Quelle histoire sur vous êtes-vous prêt à abandonner?",
        "De quoi votre corps a-t-il besoin que votre esprit ignore?",
        "Si votre jeune moi vous voyait maintenant, que trouverait-il de surprenant?",
        "Quelle vérité vous murmurez-vous dernièrement?",
        "Où vous sentez-vous le plus en paix avec qui vous êtes?",
        "Que portez-vous qui ne vous sert plus?"
    ]
    
    return {
        "en": random.choice(reflections_en),
        "fr": random.choice(reflections_fr)
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()