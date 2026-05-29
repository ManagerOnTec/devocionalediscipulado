"""
Context processors do app Accounts.

dark_mode → injeta `dark_mode_active` (bool) e `dark_mode_theme` (str)
            em todos os templates do projeto.

Para usuários autenticados: lê o campo User.dark_mode salvo no banco.
Para usuários anônimos: retorna light (JS no cliente lê localStorage).
"""


def dark_mode(request):
    """
    Injeta o tema ativo no contexto de todos os templates.

    Retorna:
        dark_mode_active (bool): True se dark mode estiver ativo
        dark_mode_theme  (str):  'dark' ou 'light' para data-bs-theme
    """
    is_dark = (
        hasattr(request, "user")
        and request.user.is_authenticated
        and request.user.dark_mode
    )
    return {
        "dark_mode_active": is_dark,
        "dark_mode_theme": "dark" if is_dark else "light",
    }
