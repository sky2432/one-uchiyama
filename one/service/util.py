import MeCab


def parse(text):
    # split[]
    # ['名詞', '固有名詞', '組織', '*', '*', '*', '文化放送', 'ブンカホウソウ', 'ブンカホーソー']
    words = []
    t = MeCab.Tagger('-d /opt/homebrew/lib/mecab/dic/mecab-ipadic-neologd')
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
