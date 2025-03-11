import requests

def generate_voice(text, filename="outputs/voice_output.mp3"):
    api_key = "sk_cbce49d6c483948611d98d27a08a490b66df3712e98d5237"  # Replace with your actual API key
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Default voice: Rachel

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Voice saved as: {filename}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print("Voice generation failed:", e)

