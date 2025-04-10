import requests
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from .models import Game, Character, Location
from .serializers import GameSerializer, CharacterSerializer, LocationSerializer
from django.conf import settings
from django.contrib.auth.decorators import login_required
from io import BytesIO
from django.core.files.base import ContentFile
from transformers import pipeline
from diffusers import DiffusionPipeline

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

@login_required
def list_games(request):
    games = Game.objects.filter(owner=request.user)
    return render(request, 'games/dashboard.html', {'games': games})

@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, pk=game_id, owner=request.user)
    return render(request, 'games/game_details.html', {'game': game})


def generate_image_with_api(prompt):
    api_url = "https://api.stability.ai/v1/generate"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
    payload = {"prompt": prompt, "width": 512, "height": 512}

    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.content  # Retourne l'image sous forme de bytes


@login_required
def guided_creation_view(request):
    if request.method == 'POST':
        genre = request.POST.get('genre')
        ambiance = request.POST.get('ambiance')
        keywords = request.POST.get('keywords')
        references = request.POST.get('references')

        # Préparer le prompt pour l'histoire
        story_prompt = f"""Créer un concept de jeu vidéo orignal avec les éléments suivants :
Genre : {genre}
Ambiance : {ambiance}
Mots-clés : {keywords}
Références : {references}.

Fais preuve d'imagination concernant le scénario du jeu. Ton but est de créer une histoire attrayante et invente les différents noms demandés.

Format requis :

# Univers
[Décrire l'univers du jeu de manière structurée et immersive]

# Scénario en 3 actes
## Acte 1 : L'introduction
[Décrire le début de l'histoire]

## Acte 2 : Le développement et le retournement
[Décrire le développement et le twist majeur]

## Acte 3 : Le dénouement
[Décrire la conclusion]

# Personnages principaux (2-4)
## [Nom du personnage 1]
- Classe/Type : [préciser]
- Rôle narratif : [préciser]
- Background : [histoire du personnage]
- Gameplay : [style de jeu et capacités]

## [Nom du personnage 2]
[Même structure]

# Lieux emblématiques
## [Nom du lieu 1]
[Description immersive]

## [Nom du lieu 2]
[Description immersive]
"""
        
        try:
            # Appel à l'API Hugging Face pour générer l'histoire
            headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
            payload = {
                "inputs": story_prompt,
                "parameters": {
                    "max_length": 800,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }

            response = requests.post(settings.TEXT_GEN_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()  # Lève une exception si le statut HTTP est une erreur
            story_result = response.json()
            universe = story_result[0]["generated_text"]

            # Préparer le prompt pour l'image
            image_prompt = f"{genre} game with {ambiance} ambiance. Keywords: {keywords}. References: {references}."
            image_payload = {
                "prompt": image_prompt,
                # "mode": "text-to-image",
                # "aspect_ratio": "16:9",  # Optional, defaults to 1:1
                # "model": "sd3.5-large",  # Optional, defaults to sd3.5-large
                # "output_format": "png",  # Optional, defaults to png
                # "cfg_scale": 7,  # Optional, controls adherence to the prompt
                # "negative_prompt": "low quality, blurry"  # Optional
            }
            image_headers = {
                "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
                "Content-Type": "multipart/form-data",
                "Accept": "image/*",
            }

            # Appel à l'API StabilityAI pour générer l'image
            try:
                print("URL:", settings.IMAGE_GEN_ENDPOINT)
                print("Headers:", image_headers)
                print("Payload:", image_payload)
                print("Response Status Code:", response.status_code)
                print("Response Text:", response.text)
                image_response = requests.post(
                    settings.IMAGE_GEN_ENDPOINT,
                    headers=image_headers,
                    data=image_payload  # Use `data` for form fields
                )
                image_response.raise_for_status()
                image_bytes = image_response.content  # Directly get the image bytes
                
                # Sauvegarder l'image
                image_file = ContentFile(image_bytes, "generated_image.png")
            except requests.exceptions.RequestException as e:
                return render(request, 'games/create_game.html', {'error': f"Erreur API (image) : {str(e)}"})

            

            # Créer le jeu
            game = Game.objects.create(
                owner=request.user,
                title=f"Jeu généré ({genre})",
                genre=genre,
                ambiance=ambiance,
                keywords=keywords,
                references=references,
                universe=universe,
                story="Scénario généré automatiquement.",
                image_environment=image_file
            )

            return render(request, 'games/generation_success.html', {'game': game})

        except requests.exceptions.RequestException as e:
            return render(request, 'games/create_game.html', {'error': f"Erreur API : {str(e)}"})
        except KeyError:
            return render(request, 'games/create_game.html', {'error': "Erreur dans la réponse de l'API."})

    return render(request, 'games/create_game.html')
