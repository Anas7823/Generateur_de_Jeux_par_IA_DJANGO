from django.shortcuts import get_object_or_404, redirect
from django.urls import resolve, Resolver404
from games.models import Game

class ProjectOwnershipMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path.startswith('/games/') or request.path.startswith('/game/'):
                resolver_match = resolve(request.path)
                if resolver_match.url_name in ['game-detail', 'toggle-favorite']:
                    game_id = resolver_match.kwargs.get('game_id') or resolver_match.kwargs.get('pk')
                    if game_id:
                        game = get_object_or_404(Game, pk=game_id)
                        if game.owner != request.user:
                            return redirect('dashboard')
        except Resolver404:
            pass

        return self.get_response(request)