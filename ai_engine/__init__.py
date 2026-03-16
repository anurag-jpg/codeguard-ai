async def _llm_call(self, system, user, temperature=None, max_tokens=None):
    import asyncio
    model = self._genai.GenerativeModel(
        model_name=self._settings.LLM_MODEL,
        system_instruction=system
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(user)
    )
    return response.text if response.text is not None else ""