from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.GameListCreateAPIView.as_view(), name='game-list-create'),
    path('games/<int:pk>/', views.GameDetailAPIView.as_view(), name='game-detail'),
    path('games/<int:game_id>/characters/', views.CharacterListCreateAPIView.as_view(), name='character-list-create'),
    path('games/<int:game_id>/locations/', views.LocationListCreateAPIView.as_view(), name='location-list-create'),

    # Front-end Views
    path('', views.list_games, name='dashboard'),  # Tableau de bord
    path('create/', views.guided_creation_view, name='guided_creation'),  # Création guidée
    path('<int:game_id>/', views.game_detail, name='game-detail'),  # Détail d'un jeu
    path('random/', views.random_game_view, name='random_game'),  # Nouvelle URL pour Exploration Libre

]