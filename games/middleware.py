from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from games.models import Game

class ProjectOwnershipMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifie si l'URL correspond à un projet spécifique
        if request.path.startswith('/games/') and 'game-detail' in request.resolver_match.url_name:
            game_id = request.resolver_match.kwargs.get('pk')  # Récupère l'ID du projet depuis l'URL
            game = get_object_or_404(Game, pk=game_id)

            # Vérifie si l'utilisateur connecté est l'auteur du projet
            if game.owner != request.user:
                return redirect(reverse('dashboard'))  # Redirige vers le tableau de bord si non autorisé

        return self.get_response(request)