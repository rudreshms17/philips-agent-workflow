from config import call_llm

print("=" * 40)
print("TESTING GROQ API (LLAMA 3.3)...")
result = call_llm("Say hello and confirm you are working in one sentence.")
print(f"Response: {result}")
print("=" * 40)
print("GROQ TEST COMPLETE!")
