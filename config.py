from dotenv import load_dotenv
import os
import requests

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_llm(prompt: str) -> str:
    """Primary LLM calling function. Currently uses Groq (Llama 3.3)."""
    return call_groq(prompt)

def call_groq(prompt: str) -> str:
    from groq import Groq
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[GROQ ERROR]: {e}")
        return "Could not get response from Groq."
