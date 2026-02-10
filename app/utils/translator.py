from deep_translator import GoogleTranslator


def translate_to_id(text: str) -> str:
    """
    Translate text ke Bahasa Indonesia.
    Kalau sudah Indonesia, hasilnya hampir sama.
    """
    try:
        translated = GoogleTranslator(
            source="auto",
            target="id"
        ).translate(text)
        return translated
    except Exception:
        # fallback: pakai teks asli
        return text
