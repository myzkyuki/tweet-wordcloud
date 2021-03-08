# Tweet WordCloud
Twitter APIを使用して、Tweetを収集し、WordCloudを作成します。

# 使い方
## Tweetの収集
始めに、Twitter APIを使用して、Tweetを収集します。
Twitter APIを使用するためには、事前にTwitterのDeveloperアカウントの取得が必要です。
Developerアカウントから取得したAPI Key等を指定して以下のコマンドを実行します。
`--query`には検索キーワードを設定します。
実行すると、収集したTweetテキストが格納された`tweet_data.txt`が出力されます。

```bash
$ python tweet_collector.py \
    --api_key <Twitter API key> \
    --api_secret <Twitter API secret key> \
    --access_token <Accesss token> \
    --access_token_secret <Access token secret> \
    --query <Search query>
```

## WordCloudの作成
収集したTweetテキストを使用して、WordCloudを作成します。
以下のコマンドを実行すると、`wordcloud.png`が出力されます。

```bash
$ python wordcloud_gen.py
```

なお、WordCloudでは日本語フォントが必要となります。
`wordcloud_gen.py`の`FONT_PATH`に、環境に合わせてフォントパスを指定してください。