# -*- coding: utf-8 -*-

import CaboCha

# オレオレTokenラッパークラス
class Token:
  def __init__(self, token):
    self.chunk = token.chunk
    self.features = token.feature.split(',')
    self.surface = token.surface

  # 名詞かどうか
  def is_noun(self):
    return self.features[0] == '名詞'

  # 動詞かどうか
  def is_verb(self):
    return self.features[0] == '動詞'

  # 形容詞かどうか
  def is_adjective(self):
    return self.features[0] == '形容詞'

  # サ変するかどうか
  def is_sahen(self):
    return self.features[4] == 'サ変・スル'

  # 名詞接続かどうか (「お星様」の「お」など)
  def is_noun_connection(self):
    return self.features[0] == '接頭詞' and self.features[1] == '名詞接続'

  # サ変接続かどうか (掃除する 洗濯する など)
  def is_sahen_connection(self):
    return self.features[0] == '名詞' and self.features[1] == 'サ変接続'

  # 基本形へ
  def get_base(self):
    if 6 < len(self.features) and self.features[6] != "*":
      return self.features[6]
    else:
      return self.surface

# オレオレChunkラッパークラス
class Chunk:
  def __init__(self, chunk, tree):
    self.link = chunk.link
    self.tokens = [Token(tree.token(i)) for i in xrange(chunk.token_pos, chunk.token_pos + chunk.token_size)]

  # 形容詞かどうか
  def is_adjective(self):
    return self.tokens[0].is_adjective()

  # 名詞サ変接続+スルかどうか
  def is_verb_sahen(self):
    return (1 < len(self.tokens) and self.tokens[0].is_sahen_connection() and self.tokens[1].is_sahen())

  # 名詞かどうか
  def is_noun(self):
    return (not self.is_verb_sahen() and (self.tokens[0].is_noun() or self.tokens[0].is_noun_connection()))

  # 動詞かどうか
  def is_verb(self):
    return self.tokens[0].is_verb() or self.is_verb_sahen()

  # 主語っぽいかどうか
  def is_subject(self):
    if not any([ch == self.tokens[-1].surface for ch in ['は', 'って', 'も', 'が']]):
      return False
    return self.is_noun() or self.is_adjective() or self.is_verb()

  # 基本形へ変換
  def get_base(self):
    tokens = self.tokens

    if self.is_noun():
      # 連続する名詞、・_や名詞接続をくっつける
      base = ""
      for token in tokens:
        if token.is_noun_connection():
          base += token.get_base()
        elif token.is_noun():
          base += token.get_base()
        elif "_" in token.surface or "・" in token.surface:
          base += token.get_base()
        elif 0 < len(base):
          break
      return base
    elif self.is_verb_sahen():
      ret = tokens[0].get_base() + tokens[1].get_base()
      if self.is_negative(tokens):
        ret += 'ない'
      return ret
    elif self.is_verb():
      ret = tokens[0].get_base()
      if self.is_negative(tokens):
        ret += 'ない'
      return ret
    elif self.is_adjective():
      ret = tokens[0].get_base()
      if self.is_negative(tokens):
        ret += 'ない'
      return ret
    else:
      return ''.join([token.surface for token in tokens])

  # 元の形へ変換
  def get_surface(self):
    tokens = self.tokens

    if self.is_noun():
      # 連続する名詞、・_や名詞接続をくっつける
      surface = ""
      for token in tokens:
        if token.is_noun_connection():
          surface += token.surface
        elif token.is_noun():
          surface += token.surface
        elif "_" in token.surface or "・" in token.surface:
          surface += token.surface
        elif 0 < len(surface):
          break
      return surface
    elif self.is_verb_sahen():
      # 名詞サ変接続 + スル
      ret = tokens[0].surface
      if self.is_negative(tokens):
        ret += tokens[1].surface + 'ない'
      else:
        ret += 'する'
      return ret
    elif self.is_verb():
      ret = ''
      if self.is_negative(tokens):
        # 否定の直前までカウント
        count = 0
        for token in tokens:
          if token.features[6] == 'ない':
            break
          count += 1
        ret = ''.join([tokens[i].surface for i in xrange(count)]) + 'ない'
      else:
        ret = tokens[0].get_base()
      return ret
    elif self.is_adjective():
      ret = ''
      if self.is_negative(tokens):
        # 否定の直前までカウント
        count = 0
        for token in tokens:
          if token.features[6] == 'ない':
            break
          count += 1
        ret = ''.join([tokens[i].surface for i in xrange(count)]) + 'ない'
      else:
        ret = tokens[0].get_base()
      return ret
    else:
      return ''.join([token.surface for token in tokens])

  def is_negative(self, tokens):
    count = 0
    for token in tokens:
      if token.features[6] == 'ない':
        count += 1
    return count % 2 == 1

# 対象の文章
sentences = ['ソクラテスは人間です。',
    '福沢諭吉は1万円札に出てる人間です。',
    '僕も普通の人間。',
    '鳥が空を飛んでいる。',
    '馬ってたぶんうまい。',
    '飛ぶのは飛行機です。',
    'かわいいは正義。',
    'お星様はとてもまぶしい。',
    '拙者は時々切腹するでござる。',
    '私は走らない。',
    '今日は暑くない。',
    '今日は暑くなくはない。',
    'あなたは絵を描きたくないんだね。',
    'あなたは絵を描きたくなくもないんだね。']


if __name__ == '__main__':
  parser = CaboCha.Parser('-f1')
  for sentence in sentences:
    print '+', sentence
    tree = parser.parse(sentence)
    chunk_dic = {}
    chunk_id = 0
    # 全てのchunkに対して
    for i in range(0, tree.size()):
      token = Token(tree.token(i))
      chunk = token.chunk
      if chunk:
        chunk_dic[chunk_id] = Chunk(chunk, tree)
        chunk_id += 1

    for chunk_id, chunk in chunk_dic.items():
      # 接続先があるかどうか
      if 0 < chunk.link:
        to_chunk = chunk_dic[chunk.link]
        # 主語っぽくて接続先の接続先がないチャンクを抽出
        if (chunk.is_subject() and to_chunk.link < 0):
          # 主語 => 述語を表示
          print "- proto: {} => {}".format(chunk.get_base(), to_chunk.get_base())
          print "- org:   {} => {}".format(chunk.get_base(), to_chunk.get_surface())