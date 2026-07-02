import requests


class LLMClientError(Exception):
    pass


def extract_chat_content(response_json):
    choices = response_json.get("choices", [])
    if not choices:
        raise LLMClientError("The API response did not contain choices.")

    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise LLMClientError("The API response did not contain message content.")

    return content


def generate_text(api_key, model, api_base, system_prompt, user_input):
    if not api_key:
        raise LLMClientError("DEEPSEEK_API_KEY is not configured.")

    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "thinking": {"type": "disabled"},
        "stream": False,
        "max_tokens": 300,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as error:
        raise LLMClientError("Failed to connect to DeepSeek API: " + str(error))

    if response.status_code >= 400:
        raise LLMClientError(
            "DeepSeek API returned status {0}: {1}".format(
                response.status_code,
                response.text,
            )
        )

    return extract_chat_content(response.json())
