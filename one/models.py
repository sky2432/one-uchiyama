from django.db import models


class Radio(models.Model):
    title = models.CharField(verbose_name="タイトル", max_length=255, unique=True)
    english_title = models.CharField(
        verbose_name="英語タイトル", max_length=255, unique=True)
    image = models.ImageField(verbose_name="画像", upload_to='radio_image')
    created_at = models.DateTimeField(verbose_name="作成日時", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新日時", auto_now=True)

    class Meta:
        verbose_name = "ラジオ"
        verbose_name_plural = "ラジオ"

    def __str__(self):
        return str(self.title)


class Episode(models.Model):
    radio_id    = models.ForeignKey(Radio, verbose_name="ラジオID", on_delete=models.CASCADE)
    number      = models.PositiveBigIntegerField(verbose_name="回",)
    audio_file  = models.FileField(verbose_name="音声ファイル", upload_to='audio_file')
    air_date    = models.DateField(verbose_name="放送日")
    spotify_id  = models.CharField(verbose_name="SpotifyID", max_length=255, null=True, blank=True)
    job_name    = models.CharField(verbose_name="ジョブ名", max_length=255, null=True, blank=True)
    word_stored = models.BooleanField(verbose_name="単語保存済み", default=False)
    created_at  = models.DateTimeField(verbose_name="作成日時", auto_now_add=True)
    updated_at  = models.DateTimeField(verbose_name="更新日時", auto_now=True)

    class Meta:
        verbose_name = "エピソード"
        verbose_name_plural = "エピソード"
        constraints = [
            models.UniqueConstraint(
                fields=["radio_id", "number"],
                name="radio_id_number_unique"
            )
        ]

    def __str__(self):
        word_stored_str = '保存済み' if self.word_stored else '未保存'
        return f'{str(self.radio_id.title)}#{str(self.number)} 単語：{word_stored_str}'


class Word(models.Model):
    episode_id = models.ForeignKey(
        Episode, verbose_name="エピソードID", on_delete=models.CASCADE)
    original_form = models.CharField(verbose_name="原形", max_length=255)
    pronunciation = models.CharField(verbose_name="読み", max_length=255)
    start_time = models.FloatField(
        verbose_name="開始時間", max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="作成日時", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新日時", auto_now=True)

    class Meta:
        verbose_name = "単語"
        verbose_name_plural = "単語"

    def __str__(self):
        episode = self.episode_id
        radio = episode.radio_id
        return f'{radio.title}#{str(episode.number)}：{self.original_form}'
