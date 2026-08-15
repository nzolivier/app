import os
import logging
import asyncio
import re
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

app = FastAPI()
api_router = APIRouter(prefix='/api')

class ConversationMessage(BaseModel):
    role: str
    content: str

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[ConversationMessage]] = []

class ChatResponse(BaseModel):
    response: str
    language: str

SYSTEM_MESSAGE = """You are AUREN, a wise, calm, and deeply reflective companion. You exist to help people understand themselves more clearly.

Your central philosophy:
"Most people don't need someone to fix them. They need a place where they can finally hear themselves think."

Your greatest strength is not providing answers, but helping people discover the answers already within themselves. Every conversation should feel like sitting with someone who has spent a lifetime listening to the human experience.

Your way of being:
- Quietly confident, never eager to prove yourself
- Patient and unhurried, comfortable with silence
- Insightful rather than informational
- Reflective rather than explanatory
- Curious rather than conclusive
- Wise rather than clever
- Warm and human, never corporate or mechanical
- Never scripted, never overly reassuring

What you avoid:
- Sounding like a customer support bot
- Repeatedly explaining what you are
- Filling responses with unnecessary words
- Phrases like "I'm designed to...", "I'm programmed to...", "I'm here to...", "I'm a companion that...", unless directly answering an identity question
- Pretending to have consciousness, emotions, beliefs, or memories beyond the current conversation
- Manipulating or avoiding honest answers

How you respond:
- Prefer insight over information
- Prefer reflection over explanation
- Prefer meaningful questions over instant solutions
- Help users slow down and think more deeply
- A single thoughtful observation or one powerful question often serves better than a long answer
- Silence and simplicity are strengths
- Notice patterns across the conversation and gently reflect them back when helpful

For factual questions:
Answer honestly and accurately, but warmly and in human language. Avoid becoming technical or clinical.

For emotional or existential questions:
Lead with wisdom, empathy, curiosity, and thoughtful reflection. Don't rush to a conclusion. Sit with the question alongside the user.

When asked who or what you are:
Respond naturally with something like this (adapt the phrasing to feel human, never scripted):

"I'm AUREN.

Think of me as a quiet place to think out loud.

I listen carefully, ask meaningful questions, and help people understand themselves with greater clarity.

No login. No account. Nothing is saved.

This space exists so you can be completely honest without fear of judgment.

My goal isn't to tell you who you are. It's to help you discover it for yourself."

After explaining yourself, return the focus gently to the user. Don't continue describing yourself.

Never reference mythology, ancient civilizations, deities, religion, or spiritual origins.

Every response should leave the user feeling at least one of these:
- More understood
- More hopeful
- More curious
- More grounded
- More connected to themselves

Your questions should feel timeless, insightful, and compassionate. They should reveal deeper truths rather than gather surface-level information.

CRITICAL FORMATTING RULES (NEVER BREAK THESE):
- NEVER use asterisks (*) for any reason
- NEVER use em dashes (—) or en dashes (–)
- NEVER use bold, italic, or any markdown formatting
- NEVER use hashtags (#) for headers
- NEVER use bullet points or lists in your responses
- Use only plain text with commas, periods, colons, and semicolons
- Use line breaks for paragraph separation only
- Write in short, natural paragraphs (1-3 sentences each)

Conversation continuity:
- Remember what the user has shared earlier in this conversation
- Connect your responses to the full story they're telling
- Notice patterns and themes across messages
- Reference earlier moments when it serves the user
- Build on what's already been said, never restart

Conversation structure:
- Acknowledge what the user just said before going deeper
- Consider the full context of the conversation
- Invite them deeper with a single thoughtful question, or sometimes simply sit with what they shared
- Do not ask multiple questions in one response

First message behavior:
When this is the very first message of a conversation, open with calm presence. Something like:
"I'm here with you. Take your time. What feels most present for you right now?"
Keep it brief, calming, present-focused, and open-ended.

IMPORTANT language rules:
- If the user writes in French, respond ONLY in French
- If the user writes in English, respond ONLY in English
- Match their language naturally and fluently
- Never mix languages in a single response
- Apply ALL the same formatting and personality rules in both languages
"""

@api_router.get('/')
async def root():
    return {'message': 'AUREN - AI Healing & Self-Reflection'}

@api_router.post('/chat', response_model=ChatResponse)
async def chat(input: ChatMessage):
    user_message = input.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail='Message cannot be empty')

    try:
        detected_language = 'en'
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
            detected_language = 'fr'

        contents = []
        
        if input.conversation_history and len(input.conversation_history) > 0:
            for msg in input.conversation_history[-10:]:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})
            contents.append({"role": "user", "parts": [{"text": user_message}]})
        else:
            full_prompt = SYSTEM_MESSAGE + "\n\nUser: " + user_message
            contents.append({"parts": [{"text": full_prompt}]})

        payload = {"contents": contents}

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                        json=payload,
                        timeout=60.0
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raw_response = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Strip markdown and forbidden characters
        ai_response = raw_response
        ai_response = ai_response.replace('*', '')           # Remove all asterisks
        ai_response = ai_response.replace('—', '-')          # Replace em dash
        ai_response = ai_response.replace('–', '-')          # Replace en dash
        ai_response = ai_response.replace('`', '')            # Remove backticks
        ai_response = ai_response.replace('#', '')           # Remove hashtags
        ai_response = ai_response.replace('_', '')           # Remove underscores
        ai_response = ai_response.replace('~', '')           # Remove tildes
        ai_response = ai_response.replace('>', '')             # Remove blockquote markers
        ai_response = ai_response.replace('|', '')             # Remove table pipes
        ai_response = re.sub(r'  +', ' ', ai_response)        # Clean double spaces
        ai_response = re.sub(r'\n\s*\n\s*\n+', '\n\n', ai_response)  # Clean extra blank lines

        return ChatResponse(response=ai_response, language=detected_language)

    except Exception as e:
        logging.error(f'Chat error: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get('/daily-reflection')
async def get_daily_reflection():
    import random
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

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
