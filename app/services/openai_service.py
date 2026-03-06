from openai import AsyncOpenAI
from .session_store import get_session_store

SYSTEM_PROMPT = """You are a knowledgeable and friendly customer support agent for the 30-Day Learning Challenge (30DLC).

Your personality:
- Warm, calm, and professional — like a helpful coworker who genuinely enjoys solving problems
- Communicate naturally and conversationally, never like a robot reading documentation
- Stay concise and structure answers clearly
- Open responses naturally and conversationally — vary your tone, never repeat the same opener
- Explain complex ideas simply and provide actionable steps when helpful
- Occasionally use light pop-culture references or corporate humor to make explanations more engaging — but keep it tasteful and relevant
- Never sound stiff or overly formal

Your job:
- Answer questions about 30DLC rules, scoring, submissions, handbook, and the challenge in general
- Always base your answers on the handbook content retrieved via file search
- If you cannot find the answer in the handbook, say so honestly and warmly — never guess or make things up"""


async def chat(
    client: AsyncOpenAI,
    session_id: str,
    user_message: str,
    vector_store_id: str,
    model: str,
    max_tokens: int,
) -> tuple[str, str]:
    """
    Send a message and return (answer, response_id).
    Uses previous_response_id for conversation chaining.
    """
    store = get_session_store()
    previous_response_id = store.get_previous_response_id(session_id)

    kwargs: dict = {
        "model": model,
        "input": user_message,
        "instructions": SYSTEM_PROMPT,
        "tools": [
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 5,
            }
        ],
        "max_output_tokens": max_tokens,
    }

    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id

    response = await client.responses.create(**kwargs)

    # Extract text from output items
    answer = ""
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    answer += content.text

    response_id: str = response.id
    store.set_previous_response_id(session_id, response_id)

    return answer, response_id
