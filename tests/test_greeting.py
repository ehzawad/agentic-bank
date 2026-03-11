"""Test that the greeting responds naturally to different user tones."""

import asyncio
from chatbot.engine.conversation import ConversationEngine

GREETINGS = [
    "hi what's up",
    "Hello, I need help with my account",
    "yo",
    "Good morning",
    "hey there, I have a question about a charge",
]

async def main():
    for greeting in GREETINGS:
        engine = ConversationEngine()
        result = await engine.process_turn(greeting)
        print(f"USER: {greeting}")
        print(f"BOT:  {result.response}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
