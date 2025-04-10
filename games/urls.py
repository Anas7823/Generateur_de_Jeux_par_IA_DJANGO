from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.GameListCreateAPIView.as_view(), name='game-list-create'),
    path('games/<int:pk>/', views.GameDetailAPIView.as_view(), name='game-detail'),
    path('games/<int:game_id>/characters/', views.CharacterListCreateAPIView.as_view(), name='character-list-create'),
    path('games/<int:game_id>/locations/', views.LocationListCreateAPIView.as_view(), name='location-list-create'),
]