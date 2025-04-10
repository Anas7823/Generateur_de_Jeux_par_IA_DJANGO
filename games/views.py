import requests
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from .models import Game, Character, Location
from .serializers import GameSerializer, CharacterSerializer, LocationSerializer
from django.conf import settings

# API Views

class GameListCreateAPIView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class GameDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Game.objects.filter(owner=self.request.user)

class CharacterListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CharacterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Character.objects.filter(game_id=self.kwargs['game_id'])

    def perform_create(self, serializer):
        game = get_object_or_404(Game, pk=self.kwargs['game_id'], owner=self.request.user)
        serializer.save(game=game)

class LocationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Location.objects.filter(game_id=self.kwargs['game_id'])

    def perform_create(self, serializer):
        game = get_object_or_404(Game, pk=self.kwargs['game_id'], owner=self.request.user)
        serializer.save(game=game)

# Form-based Views

def create_game(request):
    if request.method == 'POST':
        # Process the form data and create a new game
        pass
    else:
        # Render the game creation form
        return render(request, 'games/create_game.html')

def list_games(request):
    # Fetch the list of games from the database
    games = Game.objects.filter(owner=request.user)
    return render(request, 'games/list_games.html', {'games': games})

def game_detail(request, game_id):
    # Fetch the game details from the database using game_id
    game = get_object_or_404(Game, pk=game_id, owner=request.user)
    return render(request, 'games/game_detail.html', {'game': game})

def guided_creation_view(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        genre = request.POST.get('genre')
        ambiance = request.POST.get('ambiance')
        keywords = request.POST.get('keywords')
        references = request.POST.get('references')

        # Préparer les données pour l'appel API
        prompt = f"Créer un jeu vidéo de genre {genre} avec une ambiance {ambiance}. Mots-clés : {keywords}. Références : {references}."
        api_url = "https://api-inference.huggingface.co/models/gpt-3.5-turbo"
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
        }
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 500, "num_return_sequences": 1}
        }

        # Effectuer l'appel API
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            # Extraire le texte généré
            result = response.json()
            universe = result[0]['generated_text']

            # Sauvegarder les résultats dans la base de données
            Game.objects.create(
                owner=request.user,
                title=f"Jeu généré ({genre})",
                genre=genre,
                ambiance=ambiance,
                keywords=keywords,
                references=references,
                universe=universe,
                story="Scénario généré automatiquement."
            )
            return render(request, 'games/generation_success.html', {'universe': universe})
        else:
            # Gérer les erreurs de l'API
            error_message = response.json().get("error", "Une erreur est survenue lors de la génération.")
            return render(request, 'games/guided_creation.html', {'error': error_message})

    return render(request, 'games/guided_creation.html')
