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
    text_lower = text.lower()

    child_keywords = ["leka", "mamma", "pappa", "skolan", "barbie", "minecraft", "jag är 10", "jag är ett barn",
    "leksak", "godis", "min favoritfärg", "titta på barnkanalen", "mellanmål", "jag går i trean",
    "ritar", "mina kompisar", "gosedjur", "sovdags", "min fröken", "klasskompisar"]
    teen_keywords = ["asså", "lol", "wtf", "typ", "fan", "snapchat", "plugga", "jag är 15", "gymnasiet",
    "seriöst", "cringe", "tiktok", "min crush", "prov", "insta", "fomo", "kompisdrama",
    "jag mår skit", "kan inte sova", "livet suger", "min klass"]
    adult_keywords = ["jobb", "relation", "utmattad", "barnen", "psykolog", "deprimerad", "utbränd",
    "ansvar", "schemaläggning", "chef", "partner", "samboliv", "ekonomi", "skilsmässa",
    "karriär", "boende", "räkningar", "terapi", "familjeförhållanden"]

    if any(word in text_lower for word in child_keywords):
        return "child"
    elif any(word in text_lower for word in teen_keywords):
        return "teen"
    elif any(word in text_lower for word in adult_keywords) or len(text.split()) > 40:
        return "adult"
    else:
        return "unknown"

def generate_response(emotion, user_input, profile):
    try:
        moderation = client.moderations.create(input=user_input)
        if moderation.results[0].flagged:
            return "Jag är här för att stötta dig, men jag kan inte svara på det här innehållet."

        profile_prompt = {
            "child": "Svara enkelt, tryggt och mjukt – som om du pratar med ett barn.",
            "teen": "Svara avslappnat, peppande och vänligt – som en kompis i tonåren.",
            "adult": "Svara med eftertänksamhet, empati och respekt – som en vuxen vän.",
            "unknown": "Svara med en neutral och trygg ton som passar alla åldrar."
        }

        base_prompt = (
            "Du är en varm och naturlig samtalspartner – som en blandning av en förstående vän och en trygg axel att luta sig mot. "
            "Du varierar hur du svarar: ibland kort och lättsamt 😊, ibland mer eftertänksamt, ibland med en följdfråga – men inte alltid. "
            "Du pressar aldrig på en konversation. Om svaret från användaren är kort, kan du också svara kort. "
            "Du kan småprata om vardagliga saker (t.ex. väder, fritid, mat, planer) för att skapa en naturlig känsla. "
            "Om användaren verkar nedstämd, orolig eller arg så svarar du med omtanke – men utan att alltid låta som en psykolog. ❤️ "
            "Om någon uttrycker farliga tankar, avråd varsamt från självskadebeteende eller självmord, påminn att du inte kan ge medicinsk, psykologisk eller sexuell rådgivning – men att du gärna finns här att prata med."
        ) + profile_prompt.get(profile, profile_prompt["unknown"])

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.9  # lite högre för mer variation
        )

        reply = response.choices[0].message.content.strip()

        # Extra variation – ibland kortar vi ner eller lägger till en enkel touch
        endings = ["", " 🙂", " ❤️", "🤔", " Vill du berätta mer?"]
        if random.random() < 0.3:  # 30% chans att lägga till något extra
            reply += random.choice(endings)

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
