import os
from config import Config


class AIProvider:
    """Абстракція над Claude / Groq для легкого перемикання"""

    def __init__(self):
        if Config.USE_GROQ:
            from groq import Groq
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            self.model = Config.GROQ_MODEL
            self.provider = 'groq'
        else:
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.CLAUDE_MODEL
            self.provider = 'anthropic'

    def chat(self, system_prompt: str, user_message: str, context: dict = None) -> str:
        messages = []
        if context and context.get('conversation_history'):
            messages.extend(context['conversation_history'])
        messages.append({"role": "user", "content": user_message})

        if self.provider == 'groq':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        else:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text


ai = AIProvider()
