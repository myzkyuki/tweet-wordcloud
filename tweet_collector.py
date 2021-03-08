import os
import re
import time
import socket
import argparse
from typing import Tuple

import requests_oauthlib

from logger import logger

MAX_ATTEMPTS = 10
WAIT_SEC = 30
MIN_CHARS = 2

BASE_TIMESTAMP = 1288834974657
RATE_LIMIT_URL = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
SEARCH_URL = 'https://api.twitter.com/1.1/search/tweets.json'

# Regex patterns to format text
screen_name_pattern = re.compile(r'@[\w_]+ *')
hash_tag_pattern = re.compile(r'#[^ ]+ *')
url_pattern = re.compile(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+ *')
valid_char_pattern = re.compile(r'[^、。!?ー〜1-9a-zA-Zぁ-んァ-ヶ亜-腕纊-黑一-鿕]')
space_pattern = re.compile(r'\s+')


class TweetCollector:
    def __init__(self, api_key: str, api_secret_key: str,
                 access_token: str, access_token_secret: str):
        self.session = requests_oauthlib.OAuth1Session(
            client_key=api_key, client_secret=api_secret_key,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret)

    @staticmethod
    def wait(sec: float):
        logger.info(f'Wait {sec:.3f} sec.')
        time.sleep(sec)

    def get_content(self, url: str, params: dict = {}) -> dict:
        for _ in range(MAX_ATTEMPTS):
            try:
                res = self.session.get(url, params=params)
            except socket.error as e:
                logger.error(f'Failed to connect socket for {url}: {e.errno}.')
                self.wait(WAIT_SEC)

            if res.status_code == 200:
                return res.json()
            else:
                logger.warning(f'Status code is {res.status_code} for {url}.')
                self.wait(WAIT_SEC)
        else:
            raise Exception(f'Failed to connect to {url} '
                            f'more than max attempts ({MAX_ATTEMPTS}).')

    def check_and_wait_rate_limit(self):
        def get_remaining_and_reset(resource: dict):
            return resource['remaining'], resource['reset']

        for _ in range(MAX_ATTEMPTS):
            content = self.get_content(RATE_LIMIT_URL)
            resources = content['resources']

            search_remaining, search_reset = get_remaining_and_reset(
                resources['search']['/search/tweets'])
            limit_remaining, limit_reset = get_remaining_and_reset(
                resources['application']['/application/rate_limit_status'])

            logger.info(f'Remaining counts: search: {search_remaining}, '
                        f'limit: {limit_remaining}')

            if min(search_remaining, limit_remaining) <= 1:
                reset = max(search_reset, limit_reset)
                self.wait(reset - int(time.time()) + WAIT_SEC)
            else:
                break
        else:
            raise Exception('Failed to wait rate limit')

    @staticmethod
    def status_id_to_timestamp(status_id: int) -> int:
        """Return ms timestamp from status id"""
        return (status_id >> 22) + BASE_TIMESTAMP

    @staticmethod
    def format_text(text: str):
        if text.startswith('RT '):
            return ''

        text = screen_name_pattern.sub('', text)
        text = hash_tag_pattern.sub('', text)
        text = url_pattern.sub('', text)
        text = space_pattern.sub(' ', text)
        text = valid_char_pattern.sub('', text)

        return text

    def search(self, query: str, start_timestamp: int) -> Tuple[int, list]:
        """Search tweets include `query` strings after `start_timestamp`
        """
        params = {'q': query, 'count': 100, 'tweet_mode': 'extended'}
        content = self.get_content(SEARCH_URL, params)
        texts = []
        latest_timestamp = start_timestamp
        for status in content['statuses']:
            status_id = status['id']
            tweet_timestamp = self.status_id_to_timestamp(status_id)
            if tweet_timestamp <= start_timestamp:
                # Ignore past status
                continue

            if latest_timestamp < tweet_timestamp:
                latest_timestamp = tweet_timestamp

            text = self.format_text(status['full_text'])
            if len(text) < MIN_CHARS:
                continue

            texts.append(text)

        return latest_timestamp, texts

    def search_and_save(self, query: str, num_searches: int,
                        interval_sec: int, output_path: str):
        start_timestamp = BASE_TIMESTAMP
        if os.path.isfile(output_path):
            total_lines = sum([1 for _ in open(output_path)])
        else:
            total_lines = 0

        for i in range(num_searches):
            process_start = time.time()
            self.check_and_wait_rate_limit()
            start_timestamp, texts = self.search(query, start_timestamp)
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(texts))

            total_lines += len(texts)
            logger.info(f'{i}: total: {total_lines}, current: {len(texts)}.')
            process_sec = time.time() - process_start
            if process_sec < interval_sec:
                self.wait(interval_sec - process_sec)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key', type=str, required=True,
                        help='Twitter API key.')
    parser.add_argument('--api_secret_key', type=str, required=True,
                        help='Twitter API secret key.')
    parser.add_argument('--access_token', type=str, required=True,
                        help='Twitter access token.')
    parser.add_argument('--access_token_secret', type=str, required=True,
                        help='Twitter access token secret.')
    parser.add_argument('--query', type=str, required=True,
                        help='Query to search tweets.')
    parser.add_argument('--num_searches', type=int, default=100,
                        help='Num searches on Twitter.')
    parser.add_argument('--interval_sec', type=int, default=30,
                        help='Seconds interval between searches.')
    parser.add_argument('--output_path', type=str, default="tweet_data.txt",
                        help='Path to output tweet texts')
    args = parser.parse_args()

    collector = TweetCollector(api_key=args.api_key,
                               api_secret_key=args.api_secret_key,
                               access_token=args.access_token,
                               access_token_secret=args.access_token_secret)
    collector.search_and_save(query=args.query,
                              num_searches=args.num_searches,
                              interval_sec=args.interval_sec,
                              output_path=args.output_path)
