import requests


class OpenAIClientError(Exception):
    pass


def extract_output_text(response_json):
    if response_json.get("output_text"):
        return response_json["output_text"]

    output_items = response_json.get("output", [])
    for item in output_items:
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            text = content.get("text")
            if text:
                return text

    raise OpenAIClientError("The API response did not contain output text.")


def generate_text(api_key, model, api_base, instructions, user_input):
    if not api_key:
        raise OpenAIClientError("OPENAI_API_KEY is not configured.")

    url = api_base.rstrip("/") + "/responses"
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "instructions": instructions,
        "input": user_input,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as error:
        raise OpenAIClientError("Failed to connect to OpenAI API: " + str(error))

    if response.status_code >= 400:
        raise OpenAIClientError(
            "OpenAI API returned status {0}: {1}".format(
                response.status_code,
                response.text,
            )
        )

    return extract_output_text(response.json())
