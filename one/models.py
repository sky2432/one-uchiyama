from django.db import models


class Radio(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.title)


class Episode(models.Model):
    radio_id = models.ForeignKey(Radio, on_delete=models.CASCADE)
    number = models.PositiveBigIntegerField()
    audio_file = models.FileField(upload_to='audio_file')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["radio_id", "number"],
                name="radio_id_number_unique"
            )
        ]

    def __str__(self):
        return str(self.id)


class Word(models.Model):
    episode_id = models.ForeignKey(Episode, on_delete=models.CASCADE)
    surface = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.surface
