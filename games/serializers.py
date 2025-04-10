from rest_framework import serializers
from .models import Game, Character, Location

class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class GameSerializer(serializers.ModelSerializer):
    characters = CharacterSerializer(many=True, read_only=True)
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = '__all__'
