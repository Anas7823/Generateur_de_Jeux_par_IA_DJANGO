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
import random
from .api_limiter import api_limiter  # Ajouter cette ligne en haut du fichier
from django.http import JsonResponse
from django.shortcuts import redirect
 

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
        can_use, wait_time = api_limiter.check_limit(request.META.get('REMOTE_ADDR'))
        if not can_use:
            return render(request, 'games/api_limit.html', {
                'wait_time': wait_time,
                'cooldown_minutes': api_limiter.cooldown_minutes,
                'max_attempts': api_limiter.max_attempts
            })

        genre = request.POST.get('genre')
        ambiance = request.POST.get('ambiance')
        keywords = request.POST.get('keywords')
        references = request.POST.get('references')

        # Préparer le prompt pour l'histoire
        story_prompt = f"""Tu es un créateur de jeux vidéo innovant.
        
Ta mission : imaginer un **concept de jeu vidéo original et captivant** en t'appuyant sur les éléments suivants :

- **Genre** : {genre}  
- **Ambiance** : {ambiance}  
- **Mots-clés** : {keywords}  
- **Références d'inspiration** : {references}  

Inspire-toi librement des références mentionnées, mais propose une création inédite, immersive, et scénaristiquement forte. Tu dois **créer un univers, un scénario en 3 actes, des personnages profonds, et des lieux marquants**.

**Attention** : Tous les noms (jeu, personnages, lieux) doivent être **originaux** et **imaginatifs**. Rédige de manière fluide et structurée, comme si tu préparais une présentation officielle du jeu.

---

### Format de réponse attendu :

# 🎮 Titre du jeu  
[Un titre fort, original, accrocheur et évocateur du thème du jeu]

# 🌍 Univers  
[Décris le monde du jeu : époque, lieux, technologies, société, enjeux. Sois immersif.]

# 🎭 Scénario en 3 actes  
## Acte 1 – Introduction  
[Pose les bases : contexte, protagoniste(s), début de la quête]

## Acte 2 – Montée en tension / Twist  
[Développement des enjeux, obstacles, révélations, retournement narratif majeur]

## Acte 3 – Dénouement  
[Climax et résolution. Donne une vraie fin : ouverte, tragique, heureuse, etc.]

# 🧙 Personnages principaux (2 à 4)  
## [Nom du personnage 1]  
- **Classe/Type** : [ex. Chasseur cybernétique, Mage errant…]  
- **Rôle dans l’histoire** : [héros, antagoniste, mentor, etc.]  
- **Passé et motivations** : [background et traits de caractère]  
- **Gameplay** : [style de jeu, mécaniques spécifiques, capacités]  

## [Nom du personnage 2]  
[Même structure]

# 🗺️ Lieux emblématiques  
## [Nom du lieu 1]  
[Décris ce lieu comme s’il s’agissait d’un décor de film ou de roman]

## [Nom du lieu 2]  
[Idem : une ambiance forte, une importance narrative ou de gameplay]

---

N'oublie pas : ton objectif est de **faire rêver** un joueur ou un investisseur potentiel. Sois créatif, riche et cohérent.
"""        
        try:
            # Appel à l'API Hugging Face pour générer l'histoire
            headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
            payload = {
                "inputs": story_prompt,
                "parameters": {
                    "max_length": 800,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "return_full_text": False,
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


@login_required
def random_game_view(request):
    # Vérifier la limite d'utilisation
    can_use, wait_time = api_limiter.check_limit(request.META.get('REMOTE_ADDR'))
    if not can_use:
        return render(request, 'games/api_limit.html', {
            'wait_time': wait_time,
            'cooldown_minutes': api_limiter.cooldown_minutes,
            'max_attempts': api_limiter.max_attempts
        })
    # Générer des valeurs aléatoires pour le jeu
    genres = ["RPG", "FPS", "Aventure", "Simulation", "Stratégie", "Survie"]
    ambiances = ["Fantasy", "Cyberpunk", "Post-apocalyptique", "Horreur", "Science-fiction", "Historique", "Steampunk", "Moderne"]
    keywords = ["exploration", "combat", "magie", "technologie", "survie", "énigmes", "quête", "aventure", "mystère"]
    references = ["Zelda", "Fallout", "Mass Effect", "Dark Souls", "Minecraft", "The Witcher", "Skyrim", "Half-Life", "Portal", "GTA", "Detroit become human"]

    genre = random.choice(genres)
    ambiance = random.choice(ambiances)
    selected_keywords = ", ".join(random.sample(keywords, 3))
    selected_references = random.choice(references)

    try:
        # Générer le titre
        title_prompt = f"""Génère un titre unique et accrocheur pour un jeu vidéo avec ces éléments :
Genre : {genre}
Ambiance : {ambiance}
Mots-clés : {selected_keywords}
Références : {selected_references}

Le titre doit être court (maximum 3-4 mots), créatif et mémorable. Donne uniquement le titre, sans explication."""

        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        title_payload = {
            "inputs": title_prompt,
            "parameters": {
                "max_length": 50,
                "temperature": 0.9,
                "top_p": 0.9,
                "return_full_text": False,
            }
        }

        # Appel à l'API pour le titre
        title_response = requests.post(settings.TEXT_GEN_ENDPOINT, headers=headers, json=title_payload)
        title_response.raise_for_status()
        title_result = title_response.json()
        generated_title = title_result[0]["generated_text"].strip().split('\n')[0]
        
        # Limiter la longueur du titre
        if len(generated_title) > 100:
            generated_title = generated_title[:97] + "..."

        # Générer l'histoire
        story_prompt = f"""Tu es un créateur de jeux vidéo innovant.
Ta mission : imaginer un concept de jeu vidéo original et captivant en t'appuyant sur les éléments suivants :

- Genre : {genre}
- Ambiance : {ambiance}
- Mots-clés : {selected_keywords}
- Références : {selected_references}

Crée une histoire structurée avec :
- Un univers immersif
- Un scénario en 3 actes
- Des personnages mémorables
- Des lieux emblématiques"""

        story_payload = {
            "inputs": story_prompt,
            "parameters": {
                "max_length": 800,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False,
            }
        }

        # Appel à l'API pour l'histoire
        story_response = requests.post(settings.TEXT_GEN_ENDPOINT, headers=headers, json=story_payload)
        story_response.raise_for_status()
        story_result = story_response.json()
        universe = story_result[0]["generated_text"]

        # Générer l'image
        image_prompt = f"{genre} game with {ambiance} ambiance. Keywords: {selected_keywords}. References: {selected_references}."
        image_headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "multipart/form-data",
            "Accept": "image/*",
        }
        image_payload = {"prompt": image_prompt}

        # Appel à l'API pour l'image
        image_response = requests.post(
            settings.IMAGE_GEN_ENDPOINT,
            headers=image_headers,
            data=image_payload
        )
        image_response.raise_for_status()
        image_bytes = image_response.content

        # Sauvegarder l'image
        image_file = ContentFile(image_bytes, "generated_image.png")

        # Créer le jeu
        game = Game.objects.create(
            owner=request.user,
            title=generated_title,
            genre=genre,
            ambiance=ambiance,
            keywords=selected_keywords,
            references=selected_references,
            universe=universe,
            story=universe,  # Utiliser le contenu généré comme histoire
            image_environment=image_file
        )

        return render(request, 'games/generation_success.html', {'game': game})

    except requests.exceptions.RequestException as e:
        return render(request, 'games/create_game.html', {'error': f"Erreur API : {str(e)}"})
    except Exception as e:
        return render(request, 'games/create_game.html', {'error': f"Erreur : {str(e)}"})
    
    
@login_required
def toggle_favorite(request, game_id):
    try:
        game = get_object_or_404(Game, pk=game_id)
        is_favorite = game.toggle_favorite(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'is_favorite': is_favorite,
                'count': game.favorites.count()
            })
        
        return redirect('game-detail', game_id=game_id)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        return redirect('game-detail', game_id=game_id)

@login_required
def favorite_games(request):
    favorite_games = request.user.favorite_games.all()
    return render(request, 'games/favorite_games.html', {'games': favorite_games})