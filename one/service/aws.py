import time
import boto3
import environ
import requests


env = environ.Env()
env.read_env('.env')


def getS3PathFromUrl(url):
    domain = 's3.amazonaws.com'
    start_index = url.find(domain) + len(domain)
    end_index = url.find('?')
    return 's3://' + env.str('AWS_STORAGE_BUCKET_NAME') + url[start_index:end_index]


def transcribe_file(job_name, file_uri, vocabulary_name):
    transcribe_client = boto3.client('transcribe')

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp3',
        LanguageCode='ja-JP',
        Settings={'VocabularyName': vocabulary_name},
    )

    max_tries = 1000
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name)
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
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)


def get_transcript(file_url):
    r = requests.get(file_url, stream=True).json()
    return r['results']['transcripts'][0]['transcript']
