import os
import argparse
from typing import List
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud

# Please change the font path to suit your environment.
FONT_PATH = '/System/Library/Fonts/ヒラギノ角ゴシック W2.ttc'

STOPWORDS = ['ある', 'いい', 'いる', '思う', 'くる', 'くれる', 'こと', 'これ',
             'さん', 'する', 'せる', 'そう', 'てる', 'ない', 'なる', 'の',
             'みたい', 'やる', 'よい', 'よう', 'られる', 'れる', 'ん']


def parse(texts: List[str]) -> List[str]:
    t = Tokenizer()
    words = []
    for text in texts:
        tokens = t.tokenize(text)
        for token in tokens:
            pos = token.part_of_speech.split(',')[0]
            if pos in ['形容詞', '動詞', '名詞']:
                words.append(token.base_form)

    return words


def generate_wordcloud(words: List[str], output_path: str):
    if not os.path.isfile(FONT_PATH):
        raise FileNotFoundError(
            f'Font file is not found. Please set correct path to `FONT_PATH`.')

    wordcloud = WordCloud(background_color='white', font_path=FONT_PATH,
                          stopwords=STOPWORDS)
    wordcloud.generate(' '.join(words))
    wordcloud.to_file(output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, default='tweet_data.txt',
                        help='Path to input tweet texts.')
    parser.add_argument('--output_path', type=str, default='wordcloud.png',
                        help='Path to output wordcloud image.')
    args = parser.parse_args()

    with open(args.input_path, mode='r') as f:
        texts = f.readlines()
    words = parse(texts)
    generate_wordcloud(words, args.output_path)
