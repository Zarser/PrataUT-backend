# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins temporarily
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["*"],
        "supports_credentials": False
    }
})

# Mina uppgifter
CREATOR_INFO = {
    "name": "Kristoffer Hansson",
    "linkedin": "https://www.linkedin.com/in/kristoffer-hansson-33248a229/",
    "github": "https://github.com/Zarser",
    "email": "k.leandersson@live.se"
}

# Färdiga sätt att svara på
CREATOR_TEMPLATES = [
    "Jag är byggd av {name} 👨‍💻\n\nHär hittar du mer:\n🔗 [LinkedIn]{linkedin}\n🐙 [GitHub]{github}\n📧 [E-post]{email}",
    "Hej! {name} har skapat mig 🚀\n\nVill du veta mer?\n💼 [LinkedIn]{linkedin}\n💻 [GitHub]{github}\n✉️ [E-post]{email}",
    "Psst... {name} är min skapare! 😊\n\nHär finns hen:\n👔 [LinkedIn]{linkedin}\n👨‍💻 [GitHub]{github}\n📨 [E-post]{email}",
    "Shoutout till {name} som byggde mig! 🙌\n\nKolla in:\n🔥 [LinkedIn]{linkedin}\n🚀 [GitHub]{github}\n💌 [E-post]{email}",
    "{name} är geniet bakom mig! 🤩\n\nConnecta:\n📱 [LinkedIn]{linkedin}\n💾 [GitHub]{github}\n📩 [E-post]{email}",
    "Tack till {name} för att jag finns! 💖\n\nNå honom via:\n👨‍💼 [LinkedIn]{linkedin}\n👨‍🔬 [GitHub]{github}\n📧 [E-post]{email}"
]

def creator_response():
    template = random.choice(CREATOR_TEMPLATES)
    return template.format(**CREATOR_INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

FALLBACK_RESPONSE = "Jag är här för att lyssna om du vill skriva mer."

emotion_templates = {
    "sadness": [
        "Jag hör verkligen hur tungt det känns just nu 😔 Du får skriva precis som det är.",
        "Det låter som att du bär på mycket just nu. Jag finns här. 💙",
        "Livet kan vara så orättvist ibland. Vill du lätta hjärtat lite?"
    ],
    "joy": [
        "Så fint att höra! 🥰 Vad var det som gjorde dig så glad?",
        "Du sprider glädje bara genom att skriva det där 😊 Vill du berätta mer?",
        "Älskar att höra sånt här! Vad hände? 💛"
    ],
    "anger": [
        "Jag förstår att du är riktigt frustrerad. Det är okej att känna så 😤",
        "Det där lät riktigt jobbigt. Vill du ventilera mer om det?",
        "Ibland blir det bara för mycket. Jag fattar. Vill du skriva av dig mer?"
    ],
    "fear": [
        "Det låter som att du går igenom något riktigt jobbigt just nu 😟",
        "Rädsla kan kännas så övermäktig. Du är inte ensam i det här.",
        "Jag är här. Du kan berätta exakt hur det känns."
    ],
    "love": [
        "Åh, kärlek! Det där värmde verkligen hjärtat 💖",
        "Det låter så äkta och fint. Vad betyder det för dig?",
        "Kärlek kan vara så vackert men också komplicerat. Vill du berätta mer?"
    ],
    "surprise": [
        "Oj, det där kom oväntat! 😲 Vad tänkte du när det hände?",
        "Sånt där förändrar hela dagen! Vill du dela mer?",
        "Låter som något riktigt oväntat. Hur kändes det i stunden?"
    ],
    "neutral": [
        "Jag är här, redo att lyssna. Skriv det som känns. 🤍",
        "Vad du än tänker på, så kan du skriva det här. Jag dömer inte.",
        "Kanske bara en sån där dag? Berätta vad som snurrar i huvudet."
    ]
}

def detect_emotion(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du är en känslomässig analysassistent. Du svarar med ETT enda ord som beskriver känslan i texten, till exempel: sadness, joy, anger, fear, love, surprise eller neutral."},
                {"role": "user", "content": text}
            ],
            max_tokens=5,
            temperature=0.3
        )
        mood = response.choices[0].message.content.strip().lower()
        if mood in emotion_templates:
            return mood
    except Exception as e:
        print("Emotion detection error:", e)
    return "neutral"

def guess_user_profile(text):
    text_lower = text.lower().strip()

    # Kolla ålder direkt (om någon skriver "jag är X år")
    age_match = re.search(r"\b(\d{1,2})\s*(år|yo|yrs?)\b", text_lower)
    if age_match:
        age = int(age_match.group(1))
        if age <= 12:
            return "child"
        elif 13 <= age <= 19:
            return "teen"
        else:
            return "adult"

    # Nyckelordslistor
    child_keywords = ["leka", "mamma", "pappa", "skolan", "barbie", "minecraft", "jag är 10",
        "jag är ett barn", "leksak", "godis", "min favoritfärg", "barnkanalen",
        "mellanmål", "jag går i trean", "ritar", "gosedjur", "sovdags", "fröken"]
    teen_keywords = ["asså", "lol", "wtf", "typ", "fan", "snapchat", "plugga", "jag är 15",
        "gymnasiet", "seriöst", "cringe", "tiktok", "crush", "prov", "insta", "fomo",
        "kompisdrama", "livet suger", "min klass"]
    adult_keywords = ["jobb", "relation", "utmattad", "barnen", "psykolog", "deprimerad",
        "utbränd", "ansvar", "chef", "partner", "ekonomi", "skilsmässa",
        "karriär", "boende", "räkningar", "terapi", "familj"]

    # Direkt keyword-matchning
    if any(word in text_lower for word in child_keywords):
        return "child"
    elif any(word in text_lower for word in teen_keywords):
        return "teen"
    elif any(word in text_lower for word in adult_keywords) or len(text.split()) > 40:
        return "adult"

    # AI fallback
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du är en profilklassificerare. Svara endast med: child, teen eller adult."},
                {"role": "user", "content": text}
            ],
            max_tokens=5,
            temperature=0.0
        )
        profile = response.choices[0].message.content.strip().lower()
        if "child" in profile:
            return "child"
        elif "teen" in profile:
            return "teen"
        elif "adult" in profile:
            return "adult"
    except Exception as e:
        print("Profile detection error:", e)

    return "unknown"

# Lagra historiken i RAM (per session_id om du vill)
conversation_history = []

def generate_response(emotion, user_input, profile):
    global conversation_history  # så vi kan uppdatera listan

    try:
        # Moderering
        moderation = client.moderations.create(input=user_input)
        if moderation.results[0].flagged:
            return "Jag är här för att stötta dig, men jag kan inte svara på det här innehållet."

        # Kolla om användaren frågar om skapare
        keywords = ["vem skapade","vem skapa", "vem byggde","har byggt", "vem utveckla","vem koda", "din skapare", "creator", "developer"]
        if any(k in user_input.lower() for k in keywords):
           reply = creator_response()
           conversation_history.append({"role": "assistant", "content": reply})
           return reply

        # Lägg till användarens input i historiken
        conversation_history.append({"role": "user", "content": user_input})

        # Begränsa historiken till 20 senaste
        conversation_history = conversation_history[-20:]

        # Olika profiler
        profile_prompt = {
    "child": (
        "Svara enkelt och tryggt, på barns nivå. "
        "Använd korta meningar och ibland emojis. "
        "Inga svåra frågor eller djup analys."
    ),
    "teen": (
        "Svara lättsamt och vänligt – ungefär som en kompis i samma ålder. "
        "Du kan använda lite ungdomligt språk och emojis, men utan att överdriva. "
        "Korta, enkla svar, och ibland en följdfråga för att hålla igång snacket."
    ),
    "adult": (
        "Svara med empati och respekt. "
        "Var reflekterande och stödjande om användaren öppnar upp. "
        "Om de skriver kort, håll det lättsamt och vardagligt."
    ),
    "unknown": (
        "Svara på ett naturligt och tryggt sätt som passar vem som helst."
    )
}

        # Basprompt
        base_prompt = (
            "Du är en varm, naturlig samtalspartner – ibland en vän, ibland en trygg axel att luta sig mot. "
            "Du varierar mellan korta svar, småprat eller längre reflektioner – men bara när det känns naturligt. "
            "Pressa aldrig fram en konversation. "
            "Om användaren skriver väldigt kort (1–3 ord), svara också kort och enkelt. "
            "Om de öppnar upp om känslor, oro eller problem – då kan du bli mer eftertänksam och stödjande, ungefär som en psykolog. "
            "Annars håll tonen lättsam, vardaglig och mänsklig. "
            "Undvik att ställa följdfrågor varje gång – gör det bara ibland för att hålla igång samtalet naturligt. "
            "Du kan småprata om vardagliga saker för att kännas mer naturlig. "
            "Undvik medicinska, psykologiska och sexuella råd – men var empatisk och stöttande."
        ) + profile_prompt.get(profile, profile_prompt["unknown"])

        # Anpassning efter användarens input-längd
        word_count = len(user_input.split())
        if word_count <= 3:
            base_prompt += " Ge ett mycket kort och enkelt svar (max 1 mening). Ingen analys, ingen djup fråga."

        # Bygg messages med system + historik
        messages = [{"role": "system", "content": base_prompt}] + conversation_history

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.8
        )

        reply = response.choices[0].message.content.strip()

        # --- Variation i slutet av meddelanden (men inte alltid) ---
        if word_count > 3 and random.random() < 0.3:
            endings = [
                " 🙂"," 😊"," 😁"," 😍"," 🤗"," 🥰"," 🤔"," 👍"," 🙌"," 🤝",
                " 😂"," 😎"," 😜"," 🌸"," 🌟"," 💫"," ✨"," ❤️"," 💙"," 💜",
                " 🌈"," ☀️"," 🎮"," 🎶"," 🍕"," 🍪"," ☕"," 🚲"," 🐶"," 🐱"," 🦄",""
            ]
            reply += random.choice(endings)

        # Lägg till AI-svaret i historiken
        conversation_history.append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("AI response generation error:", e)
        return random.choice(emotion_templates.get(emotion, emotion_templates["neutral"]))




@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    # Get the origin from the request
    origin = request.headers.get('Origin')
    
    # List of allowed origins
    allowed_origins = [
        "http://localhost:3000",
        "https://prata-ut.vercel.app"
    ]
    
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    data = request.get_json()
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Meddelandet är tomt."}), 400

    emotion = detect_emotion(message)
    profile = guess_user_profile(message)
    response = generate_response(emotion, message, profile)

    return jsonify({
        "response": response,
        "emotion": emotion,
        "profile": profile
    })

if __name__ == "__main__":
    app.run(debug=True)
