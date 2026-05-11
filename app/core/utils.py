"""
Utilitários gerais para GoJohnny.
"""


def normalize_apelido(apelido: str) -> str:
    """
    Normaliza apelido para lowercase e strip.
    Garante consistência entre endpoints que usam apelido como path param vs body.
    """
    return (apelido or "").strip().lower()
