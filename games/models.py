from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Game(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    title = models.CharField(max_length=100)
    genre = models.CharField(max_length=50)
    ambiance = models.TextField()
    keywords = models.TextField()
    references = models.TextField(blank=True, null=True)
    universe = models.TextField()
    story = models.TextField()
    image_character = models.ImageField(upload_to="games/characters/", null=True, blank=True)
    image_environment = models.ImageField(upload_to="games/environments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Character(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    background = models.TextField()
    abilities = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.game.title})"

class Location(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.game.title})"
