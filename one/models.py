from django.db import models


class Episode(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Word(models.Model):
    episode_id = models.ForeignKey(Episode, on_delete=models.CASCADE)
    surface = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
