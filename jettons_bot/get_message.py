async def get_text(filename: str) -> str:
    with open(f"jettons_bot/messages/{filename}.txt", 'r', encoding='utf-8') as file:
        return file.read()