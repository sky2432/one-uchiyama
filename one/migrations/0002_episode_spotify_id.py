# Generated by Django 4.0 on 2022-07-09 00:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('one', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='episode',
            name='spotify_id',
            field=models.CharField(max_length=255, null=True, verbose_name='SpotifyID'),
        ),
    ]
