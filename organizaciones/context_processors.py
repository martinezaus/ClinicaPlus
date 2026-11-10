def clinica_navigation(request):
    if not request.user.is_authenticated:
        return {"navigation_items": []}

    return {
        "navigation_items": [
            {"label": "Inicio", "url": "organizaciones:inicio", "icon": "⌂"}
        ]
    }
