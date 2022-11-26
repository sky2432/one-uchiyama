import MeCab
import datetime

import environ

env = environ.Env()
env.read_env('.env')

def parse(text):
    # split[]
    # ['名詞', '固有名詞', '組織', '*', '*', '*', '文化放送', 'ブンカホウソウ', 'ブンカホーソー']
    words = []
    t = MeCab.Tagger(env.str('MECAB_DIC_PATH'))
    node = t.parseToNode(text)
    while node:
        f = node.feature
        split = f.split(',')
        if len(split) != 9:
            node = node.next
            continue
        if split[0] == '名詞' and split[1] in ['一般', '固有名詞']:
            word = {'original_form': split[6],
                    'pronunciation': split[7]}
            words.append(word)
        node = node.next
    return words


def now_datetime():
    """現在日時を返す

    Returns:
        string: 現在日時（Y-m-d-H-M-S）
    """
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
