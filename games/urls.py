from django.urls import path
from . import views
from users.views import splash_view

urlpatterns = [
    # API endpoints
    path('games/', views.GameListCreateAPIView.as_view(), name='game-list-create'),
    path('games/<int:pk>/', views.GameDetailAPIView.as_view(), name='game-detail'),
    path('games/<int:game_id>/characters/', views.CharacterListCreateAPIView.as_view(), name='character-list-create'),
    path('games/<int:game_id>/locations/', views.LocationListCreateAPIView.as_view(), name='location-list-create'),
    
    # Front-end Views
    path('dashboard', views.list_games, name='dashboard'),
    path('create/', views.guided_creation_view, name='guided_creation'),
    path('game/<int:game_id>/', views.game_detail, name='game-detail'),
    path('game/<int:game_id>/favorite/', views.toggle_favorite, name='toggle-favorite'),
    path('favorites/', views.favorite_games, name='favorite-games'),
    path('random/', views.random_game_view, name='random_game'),
    path('', splash_view, name='splash'),
]