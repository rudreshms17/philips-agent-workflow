from config import call_llm

def chat_with_report(report: str, question: str) -> str:
    prompt = f"""You are an expert analyst. 
A user has a question about this research report.
Answer ONLY based on the report content.
Be concise and clear.

Report:
{report}

User Question: {question}

Answer:"""
    return call_llm(prompt)
