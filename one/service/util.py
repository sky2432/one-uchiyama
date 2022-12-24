import MeCab
import datetime
import re
import environ

from typing import List, Dict

env = environ.Env()
env.read_env('.env')

def parse(text: str) -> List[Dict[str, str]]:
    """mecabを用いて文章を形態素解析し、単語リストを取得する

    Args:
        text (str): 文章

    Returns:
        List[Dict[str, str]]: 単語の原型と読みで構成された辞書のリスト
    """
    # split[]
    # 表層形\t品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音
    # ['名詞', '固有名詞', '組織', '*', '*', '*', '文化放送', 'ブンカホウソウ', 'ブンカホーソー']
    words = []
    t = MeCab.Tagger(env.str('MECAB_DIC_PATH'))
    node = t.parseToNode(text)
    while node:
        f = node.feature
        splits = f.split(',')
        # 正しく解析できてないものはスキップ
        if len(splits) != 9:
            node = node.next
            continue

        # 変数用意
        part_of_speech = splits[0]
        part_of_speech_detail_1 = splits[1]
        original_form = splits[6]
        pronunciation = splits[7]

        # 原型が1文字はスキップ
        if len(original_form) == 1:
            node = node.next
            continue
        # 2文字の「ひらがな」はスキップ
        if len(original_form) == 2 and is_hiragana(original_form):
            node = node.next
            continue

        if part_of_speech == '名詞' and part_of_speech_detail_1 in ['一般', '固有名詞']:
            word = {'original_form': original_form,
                    'pronunciation': pronunciation}
            words.append(word)
        node = node.next
    return words


def now_datetime() -> str:
    """現在日時をフォーマットした文字列で返す

    Returns:
        str: 現在日時（Y-m-d-H-M-S）
    """
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def is_hiragana(text: str) -> bool:
    """対象の文字列が全て「ひらがな」か判定する

    Args:
        text (str): 文字列

    Returns:
        bool: ひらがな: True, ひらがな以外: False
    """
    p = re.compile('[\u3041-\u309F]+')
    return p.fullmatch(text) is not None
