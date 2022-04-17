# ディズニーレストラン 空き状況確認

ディズニーリゾート予約サイトのスクレイピング & LINE通知の実装方法については[こちらのサイト](https://tetoblog.org/2021/05/disney-scraping/)を参考にしています。

Dockerファイルやlambda_handlerの書き方は[こちらのサイト](https://taaaka.tokyo/blog/posts/lambda-selenium-webdriver)を参照しています。

## パラメータ

Lambdaで指定するパラメータは以下。

|パラメータ|概要|
|:---|:---|
|date|空き状況を見たい日付(`yyyymmdd`)|
|token|LINE notifyを使って通知を送るためのトークン。リストで複数指定可能。|
|ntfy_always|LINE notify通知をレストランの空きがなくても送信するかどうか。`Y`ならば常に通知を送り、`F`なら空きがある場合のみ送る。

```json
{
    "date": 20220501,
    "token":
        [
            "<トークン1>",
            "<トークン2>"
        ],
    "ntfy_always": "F"
}
```

## 注意点

- **イメージのPythonバージョンは3.7**  
  3.8以上だとseleniumが対応していないらしい([参考リンク](https://teratail.com/questions/325567?link=qa_related_pc))
- **M1 Macだとコンテナがまともに動かない**  
  Python3.7版イメージがARMじゃないのでコンテナの動作が重いし、Lambdaにアップしても動くか微妙
- **ユーザーエージェントを指定しないと弾かれる**  
  ディズニーリゾートの予約サイトは、ユーザーエージェントがないアクセスを許可していないみたい
- **chromedriverとHeadless Chromeのバージョンに注意**  
  Headless Chromeのバージョンが結構古いので、chromedriverのバージョンもそれに合わせる必要がある
