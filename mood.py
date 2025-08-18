# mood.py

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_mood(text):
    """
    Identifierar grundläggande känslotillstånd i texten med OpenAI gpt-3.5-turbo.
    Returnerar ett enda ord som beskriver sinnesstämningen, t.ex. 'glad', 'ledsen', etc.
    """

    prompt = (
        "Vilket grundläggande känslotillstånd uttrycks i följande text?\n"
        "Svara med ETT enda ord (till exempel: glad, ledsen, arg, rädd, trött, tom, orolig, stressad, lugn).\n\n"
        f"Text: {text}\n\nSvar:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )

        mood = response.choices[0].message.content.strip().lower()

        # Validera att det bara är ett ord (inga meningar)
        if " " in mood or len(mood.split()) > 1:
            print("Svar innehöll fler ord:", mood)
            return "neutral"

        return mood

    except Exception as e:
        print("Mood detection error:", e)
        return "neutral"
