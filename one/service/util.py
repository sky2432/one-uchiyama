import MeCab
import datetime
import re

import environ

env = environ.Env()
env.read_env('.env')

def parse(text):
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


def now_datetime():
    """現在日時を返す

    Returns:
        string: 現在日時（Y-m-d-H-M-S）
    """
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def is_hiragana(text):
    p = re.compile('[\u3041-\u309F]+')
    return p.fullmatch(text) is not None
