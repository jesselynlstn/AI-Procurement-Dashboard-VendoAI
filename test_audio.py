from elevenlabs_tools import generate_voice

text = "Hello, this is a test from ElevenLabs voice synthesis. If you hear this audio, everything is working perfectly."
generate_voice(text, filename="outputs/test_audio.mp3")

