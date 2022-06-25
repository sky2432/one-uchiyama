# Generated by Django 4.0 on 2022-06-25 01:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveBigIntegerField(verbose_name='回')),
                ('audio_file', models.FileField(upload_to='audio_file', verbose_name='音声ファイル')),
                ('air_date', models.DateField(verbose_name='放送日')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
            ],
            options={
                'verbose_name': 'エピソード',
                'verbose_name_plural': 'エピソード',
            },
        ),
        migrations.CreateModel(
            name='Radio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='タイトル')),
                ('english_title', models.CharField(max_length=255, unique=True, verbose_name='英語タイトル')),
                ('image', models.ImageField(upload_to='radio_image', verbose_name='画像')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
            ],
            options={
                'verbose_name': 'ラジオ',
                'verbose_name_plural': 'ラジオ',
            },
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_form', models.CharField(max_length=255, verbose_name='原形')),
                ('pronunciation', models.CharField(max_length=255, verbose_name='読み')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('episode_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='one.episode', verbose_name='エピソードID')),
            ],
            options={
                'verbose_name': '単語',
                'verbose_name_plural': '単語',
            },
        ),
        migrations.AddField(
            model_name='episode',
            name='radio_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='one.radio', verbose_name='ラジオID'),
        ),
        migrations.AddConstraint(
            model_name='episode',
            constraint=models.UniqueConstraint(fields=('radio_id', 'number'), name='radio_id_number_unique'),
        ),
    ]
