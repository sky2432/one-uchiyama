from django.contrib import admin
from django.db.models import Q
from django.contrib import messages
from .models import Radio, Episode, Word
from .service.util import parse, now_datetime, is_hiragana
from .service.google import transcribe_gcs, get_gcs_uri, get_transcript_result
from google.api_core.exceptions import NotFound

from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query import QuerySet
from typing import List, Dict

import environ
env = environ.Env()
env.read_env('.env')

class EpisodeAdmin(admin.ModelAdmin):
    actions = ['store_words_action', 'store_words_again_action']
    readonly_fields = ['word_stored']

    def save_model(self, request: WSGIRequest, obj: Episode, form, change: bool) -> None:
        """管理画面でエピソードを保存する。

        新規保存のとき
        またはオーディオファイルが変更された場合は、文字起こしを行う。

        Args:
            request (WSGIRequest): Djangoリクエスト
            obj (Episode): Episodeモデル
            form (EpisodeForm): フォームのhtml
            change (bool): 変更があるかどうか
        """
        episode = Episode.objects.filter(id=obj.id)
        is_store = False
        is_edit = False

        if len(episode) == 0:
            print('new model')
            is_store = True
        elif obj.audio_file != episode[0].audio_file:
            print('edit model')
            is_edit = True

        super().save_model(request, obj, form, change)

        if is_edit:
            # 単語保存フラグをリセット
            set_word_stored(episode[0], False)
            # 単語をリセット
            Word.objects.filter(episode_id=episode[0].id).delete()

        # 文字起こし実行
        if is_store or is_edit:
            start_transcript_job(obj)


    def store_words_action(self, request: WSGIRequest, queryset: QuerySet) -> None:
        """単語未保存のエピソードに単語を保存する

        Args:
            request (WSGIRequest): Djangoリクエスト
            queryset (QuerySet): Episodeオブジェクト
        """
        # 単語保存済みエピソードが含まれていれば実行しない
        for episode in queryset:
            if episode.word_stored:
                messages.warning(request, '単語保存済みのエピソードがあります。')
                return
        # 単語保存
        for episode in queryset:
            if transcribe(episode, request):
                messages.success(request, '単語の保存が完了しました')

    def store_words_again_action(self, request: WSGIRequest, queryset: QuerySet) -> None:
        """単語を再保存する

        Args:
            request (WSGIRequest): Djangoリクエスト
            queryset (QuerySet): Episodeオブジェクト
        """
        # 単語未保存のエピソードが含まれていれば実行しない
        for episode in queryset:
            if not episode.word_stored:
                messages.warning(request, '単語未保存のエピソードがあります。')
                return
        for episode in queryset:
            # 既存の単語を削除
            Word.objects.filter(episode_id=episode.id).delete()
            # 単語保存
            if transcribe(episode, request):
                messages.success(request, '単語の再保存が完了しました')


    store_words_action.short_description = '初回単語保存'
    store_words_again_action.short_description = '再単語保存'


def set_word_stored(episode: Episode, stored: bool) -> None:
    """エピソードの単語保存ステータスを変更する

    Args:
        episode (Episode): Episodeモデル
        stored (bool): 保存済み: True, 未保存: False
    """
    episode.word_stored = stored
    episode.save()


def start_transcript_job(episode: Episode) -> None:
    """非同期で文字起こし処理を開始する

    Args:
        episode (Episode): Episodeモデル
    """
    audio_gcs_uri = get_gcs_uri(episode.audio_file)
    file_path = get_transcript_file_path(episode)
    transcribe_gcs(audio_gcs_uri, file_path)
    # ジョブ名を保存
    store_job_name(episode.id, file_path)


def get_transcript_file_path(episode: Episode) -> str:
    """GCSバケットルートからの文字起こしファイルパスを取得する

    Args:
        episode (Episode): Episodeモデル

    Returns:
        str: 文字起こしファイルパス
    """
    file_name = str(episode.number) + '_' + now_datetime() + '.json'
    sub_folder_name = episode.radio_id.english_title
    transcript_folder_name = 'transcript_file/' + sub_folder_name
    file_path = transcript_folder_name + '/' + file_name
    return file_path


def store_job_name(episodeId: int, job_name: str) -> None:
    """対象エピソードに文字起こしジョブ名を保存する

    Args:
        episodeId (int): エピソードID
        job_name (str): transcribeジョブ名
    """
    episode = Episode.objects.get(id=episodeId)
    episode.job_name = job_name
    episode.save()


def transcribe(episode: Episode, request: WSGIRequest) -> bool:
    """Google speech-to-textで文字起こししたファイルをmecabで解析し単語として保存する

    Args:
        episode (Episode): Episodeモデル
        request (WSGIRequest): Djangoリクエスト
    Returns:
        bool: 成功かどうか
    """
    episode = Episode.objects.get(id=episode.id)

    # GSからjsonファイルを取得
    try:
        transcript_json = get_transcript_result(episode.job_name)
    except NotFound:
        messages.warning(request, '文字起こしが未完了です。時間を置いてから再度実行してください')
        return False
    except Exception:
        messages.warning(request, '文字起こしでエラーが発生しました')
        return False
    # 文字起こし本文と単語の開始時間リストを取得
    alternative = transcript_json['results'][0]['alternatives'][0]
    transcript = alternative['transcript']
    items = alternative['words']

    # 文字起こし文を形態素解析し、単語として保存する
    words = parse(transcript)
    store_words(words, episode)
    # 単語に開始時間を設定
    store_start_time(items, episode.id)

    # エピソードを「単語保存済み」にする
    set_word_stored(episode , True)
    return True

def store_words(words: List[Dict[str, str]], episode: Episode) -> None:
    """エピソードに単語を保存する

    Args:
        words (List[Dict[str, str]]): 形態素解析で取得した単語リスト
        episode (Episode): Episodeモデル
    """
    for word in words:
        Word.objects.create(
            episode_id=episode,
            original_form=word['original_form'],
            pronunciation=word['pronunciation'],
        )


def store_start_time(items: List[Dict[str, str]], episode_id: int) -> None:
    """単語に開始時間を保存する

    Args:
        items (List[Dict[str, str]]): 単語のjsonファイル
        episode_id (int): エピソードID
    """
    for item in items:
        # start_timeのキーがなければスキップ
        if 'startTime' not in item:
            continue

        # 単語を取得
        word_split = item['word'].split('|')
        original_word = word_split[0]
        # 発音はない可能性あり
        pronunciation = word_split[1] if len(word_split) == 2 else original_word

        # 2文字以下の「ひらがな」はスキップ
        if (len(original_word) <= 2 and is_hiragana(original_word)):
            continue

        # 原型または読みに部分一致
        words = Word.objects.order_by('id').filter(
            episode_id=episode_id,
            start_time__isnull=True
        ).filter(
            Q(original_form__contains=original_word) |
            Q(pronunciation__contains=pronunciation)
        )
        # 一致する最初の単語に開始時間を設定する
        if len(words):
            # 開始時間からsを除去（例: 0s -> 0）
            words[0].start_time = item['startTime'].replace('s', '')
            words[0].save()


admin.site.register(Radio)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Word)
