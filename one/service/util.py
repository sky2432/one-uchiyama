import MeCab


def parse(text):
    words = []
    t = MeCab.Tagger('-d /opt/homebrew/lib/mecab/dic/mecab-ipadic-neologd')
    node = t.parseToNode(text)
    while node:
        f = node.feature
        split = f.split(',')
        p = split[0]
        p2 = split[1]
        if p == '名詞' and p2 in ['一般', '固有名詞']:
            word = {'original_form': split[6], 'pronunciation': split[7]}
            words.append(word)
        node = node.next
    return words
