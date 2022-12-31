import json
from google.cloud import speech, storage

from typing import Dict

import environ
env = environ.Env()
env.read_env('.env')


def get_gcs_uri(file_path: str) -> str:
    """
    Args:
        file_path (str): gcsのファイルパス

    Returns:
        str: GCSのファイルURI（例: 'gs://one-joqr-dev/audio_file/one-10s.flac'）
    """
    prefix = 'gs://'
    bucket_name = env.str('GS_BUCKET_NAME')
    return f'{prefix}{bucket_name}/{file_path}'


def transcribe_gcs(gcs_uri: str, output_file_path: str):
    """GCSにある音声ファイルを非同期で文字起こしする

    Args:
        gcs_uri (str): GCSにある音声ファイルのURI
        output_file_path (str): 文字起こしファイルを保存するGCSのパス
    """
    # Instantiates a client
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        language_code="ja-JP",
        audio_channel_count= 2,
        # 単語の時間を取得
        enable_word_time_offsets=True,
    )

    output_config = speech.TranscriptOutputConfig(
        gcs_uri=get_gcs_uri(output_file_path)
    )

    request = speech.LongRunningRecognizeRequest(
        config=config,
        audio=audio,
        output_config=output_config
    )

    # Detects speech in the audio file
    client.long_running_recognize(request=request)


def get_transcript_result(file_path: str) -> Dict:
    """GCSから文字起こし結果を取得する

    Args:
        file_name (str): GCSバケットのルートからのファイルパス

    Returns:
        Dict: 文字起こしファイルの内容
    """
    bucket = storage.Client().get_bucket(env.str('GS_BUCKET_NAME'))
    blob = storage.Blob(file_path, bucket)
    content = blob.download_as_string()
    return json.loads(content)
