# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://prata-ut.vercel.app", "http://localhost:3000"], supports_credentials=True)

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
            "child": "Svara med ett enkelt, tryggt och mjukt språk. Tänk att du pratar med ett barn.",
            "teen": "Svara på ett avslappnat, peppande och vänligt sätt. Anpassa dig till någon i tonåren.",
            "adult": "Svara med eftertänksamhet, empati och respektfull ton. Tänk dig en vuxen som söker stöd.",
            "unknown": "Svara med en neutral och trygg ton som passar alla åldrar."
        }

        base_prompt = (
            "Du är en varm och naturlig samtalspartner – som en blandning av en förstående vän och en trygg axel att luta sig mot."
            " Ibland svarar du lättsamt och med emojis 😊, ibland med mer eftertanke beroende på vad personen skriver."
            " Du dömer aldrig, du pressar inte, och du anpassar tonen efter stämningen i samtalet."
            " Om någon verkar nedstämd, orolig eller arg så svarar du med omtanke – men du behöver inte låta som en psykolog hela tiden."
            " Du kan ställa följdfrågor, ge stödjande svar, skämta lite varsamt, eller bara finnas där som ett tryggt bollplank. ❤️"
            " Om någon uttrycker farliga tankar, avråd varsamt från självskadebeteende eller självmord utan att låta dömande."
            " Påminn i så fall lugnt att du inte kan ge medicinsk, psykologisk eller sexuell rådgivning, men att du gärna finns här att prata med."
        ) + profile_prompt.get(profile, profile_prompt["unknown"])

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("AI response generation error:", e)
        return random.choice(emotion_templates.get(emotion, emotion_templates["neutral"]))

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
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
