import boto3
import environ
import json

from typing import Union, Dict

env = environ.Env()
env.read_env('.env')


def get_s3_path_from_url(url: str) -> str:
    """S3URLからS3パスを取得する

    Args:
        url (str) :S3URL

    Returns:
        str: S3パス
    """
    domain = 's3.amazonaws.com'
    start_index = url.find(domain) + len(domain)
    end_index = url.find('?')
    return 's3://' + env.str('AWS_STORAGE_BUCKET_NAME') + url[start_index:end_index]


def transcribe_file(job_name: str, file_uri: str, vocabulary_name: str) -> None:
    """音声ファイルを文字起こしする

    Args:
        job_name (str): ジョブ名
        file_uri (str): 対象音声ファイルのs3ファイルパス
        vocabulary_name (str): ボキャブラリー名
    """
    transcribe_client().start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp3',
        LanguageCode='ja-JP',
        Settings={'VocabularyName': vocabulary_name},
        OutputBucketName=env.str('AWS_TRANSCRIBE_OUTPUT_BUCKET_NAME'),
        OutputKey=env.str('AWS_TRANSCRIBE_OUTPUT_KEY'),
    )


def get_transcript_file_url(job_name: str) -> Union[str, None]:
    """文字起こしファイルURLを取得する

    Args:
        job_name (str): transcribeジョブ名

    Returns:
        Union[str, None]: ファイルがある時: URL, ファイルがないとき: None
    """
    job = transcribe_client().get_transcription_job(TranscriptionJobName=job_name)
    job_status = job['TranscriptionJob']['TranscriptionJobStatus']

    if job_status in ['COMPLETED', 'FAILED']:
        print(f"Job {job_name} is {job_status}.")
        if job_status == 'COMPLETED':
            file_url = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
            print(
                f"Download the transcript from\n"
                f"\t{file_url}."
            )
            return file_url
    else:
        print(f"Waiting for {job_name}. Current status is {job_status}.")
    return None


def transcribe_client():
    # region_nameの指定はNoRegionError対策
    return boto3.client('transcribe', region_name=env.str('AWS_REGION_NAME'))


def get_transcript_json_from_s3(url: str) -> Dict[str, str]:
    """s3から文字起こしファイルをjsonとして取得する

    Args:
        url (str): s3ファイルURL

    Returns:
        Dict[str, str]: 文字起こし結果のjson
    """
    s3 = boto3.resource('s3')
    key = get_s3_file_key_from_s3_url(url)
    object = s3.Object(env.str('AWS_TRANSCRIBE_OUTPUT_BUCKET_NAME'), key)
    body = object.get()['Body'].read()
    return json.loads(body)


def get_s3_file_key_from_s3_url(url: str) -> str:
    """S3URLからファイルキーを取得する

    example:
    url = 'https://s3.ap-northeast-1.amazonaws.com/one-uchiyama/transcribe_file/one-uchiyama_0_a12bf05c-81a8-4afd-8f71-b0088ecc8cff.json'

    return 'transcribe_file/one-uchiyama_0_a12bf05c-81a8-4afd-8f71-b0088ecc8cff.json'

    Args:
        url (str): S3URL

    Returns:
        str: S3ファイルキー
    """
    bucket_name = env.str('AWS_TRANSCRIBE_OUTPUT_BUCKET_NAME') + '/'
    start_index = url.find(bucket_name) + len(bucket_name)
    return url[start_index:]


def get_transcript_from_json(json: Dict[str, str]) -> str:
    """文字行し結果jsonから文字起こし文章を取得する

    Args:
        json (Dict[str, str]): 文字行し結果json

    Returns:
        str: 文字起こし文章
    """
    return json['results']['transcripts'][0]['transcript']
