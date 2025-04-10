from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pseudonyme = models.CharField(max_length=150, unique=True)
    avatar = models.ImageField(upload_to='avatars/')
    must_change_password = models.BooleanField(default=True)

    def __str__(self):
        return self.pseudonyme

# Création automatique du profil lors de l'inscription
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
