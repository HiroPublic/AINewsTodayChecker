# AI News Today Verifier

GitHub Actions を正式な起動トリガーにした、Python 3.12 ベースの AI ニュース検証 MVP です。ポッドキャスト「最新AI情報 AIニューストゥデイ」の RSS feed から最新回を取得し、概要欄を Perplexity API で評価し、結果を Slack Incoming Webhook に通知します。

## 特徴

- GitHub Actions の `schedule` と `workflow_dispatch` を正式トリガーとして利用
- `.state/last_run.json` を `actions/cache` で保持し、`content_hash` ベースで同一エピソードの重複通知を防止
- FastAPI API と CLI (`scripts/run_daily.py`) の両方を提供
- Slack 通知は `app/notifier/slack.py` を facade にして疎結合化
- Podcast source は RSS 実装。将来スクレイピングや別 source に差し替え可能
- Perplexity API を優先利用し、未設定や失敗時はルールベース判定にフォールバック

## ディレクトリ構成

```text
ai-news-verifier/
├─ .github/workflows/daily.yml
├─ .codex/config.toml
├─ app/
├─ scripts/
├─ tests/
├─ .env.example
├─ Dockerfile
├─ docker-compose.yml
├─ pyproject.toml
└─ README.md
```

## ローカル起動方法

1. Python 3.12 を用意します。
2. `.env.example` を元に `.env` を作成します。
3. 依存関係をインストールします。

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
```

4. API を起動します。

```bash
uvicorn app.main:app --reload
```

5. ヘルスチェックを確認します。

```bash
curl http://127.0.0.1:8000/health
```

## 手動実行方法

GitHub Actions と同じ日次処理をローカルで実行できます。

```bash
mkdir -p .state
python scripts/run_daily.py
```

`SLACK_WEBHOOK_URL` が未設定の場合、通知処理は失敗し exit code 1 になります。Perplexity API を使う場合は `PERPLEXITY_API_KEY` も設定してください。未設定時はルールベースで継続します。
`PODCAST_RSS_URL` はデフォルトで `https://podcasts.loudandfound.com/ainewstoday/podcast.xml` を参照します。

## テスト方法

```bash
pytest
```

## GitHub Actions の設定方法

ワークフローは [`.github/workflows/daily.yml`](/Users/hiro/Library/CloudStorage/OneDrive-個人用/VS%20code/AINewsTodayChecker/.github/workflows/daily.yml) にあります。

- `schedule`: 毎日 06:20 JST 相当の `20 21 * * *` で起動
- `workflow_dispatch`: GitHub UI から手動実行
- `.state` を cache restore / save 対象に設定
- `python scripts/run_daily.py` を実行
- job success 時だけ cache save を実施

## GitHub Secrets の登録方法

GitHub repository の `Settings > Secrets and variables > Actions` で以下を登録します。

必須:
- `SLACK_WEBHOOK_URL`

任意:
- `PERPLEXITY_API_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`

## workflow の動作概要

1. Repository を checkout
2. Python 3.12 をセットアップ
3. `.state` cache を restore
4. `pip install -e .[dev]`
5. `python scripts/run_daily.py`
6. 通知成功を含む job success 時のみ `.state` cache を save

アプリ側でも、通知成功時のみ `StateStore.save_success()` を呼ぶため、通知失敗時に state が更新されることはありません。

## 重複通知防止の仕組み

- 最新エピソード取得後に `content_hash` を計算
- `.state/last_run.json` の `last_episode_hash` と比較
- 同一 hash の場合は正常終了コード 0 でスキップ
- 新規エピソードは毎回 Slack 通知し、成功時のみ state を更新

## Perplexity 評価

- `PERPLEXITY_API_KEY` が設定されていれば、記事評価は Perplexity API を使います
- `PERPLEXITY_MODEL` の既定値は `sonar` です
- API 呼び出しが失敗した場合は、ローカルのルールベース判定にフォールバックします

## API

最低限の MVP endpoint:

- `GET /health`
- `POST /jobs/run-daily`

将来拡張用 placeholder:

- `POST /jobs/fetch-latest`
- `POST /jobs/analyze-latest`
- `POST /jobs/notify-latest`
- `POST /jobs/preview-latest`

## Slack 通知文の事前確認

実送信前に、実際に送られる 3 通の文面をプレビューできます。プレビューでは Slack 送信も state 更新も行いません。

CLI:

```bash
python scripts/run_daily.py --preview
```

特定のエピソード番号を指定してプレビュー:

```bash
python scripts/run_daily.py --preview --episode-number 98
```

API:

```bash
curl -X POST http://127.0.0.1:8000/jobs/preview-latest
```

特定のエピソード番号を指定してプレビュー:

```bash
curl -X POST "http://127.0.0.1:8000/jobs/preview-latest?episode_number=98"
```

レスポンスの `preview_messages` に、実送信される予定のメッセージ 3 通が入ります。

## まず動作確認するコマンド

```bash
pip install -e .[dev]
pytest
mkdir -p .state
python scripts/run_daily.py
```

## 今後の拡張ポイント

- `PodcastClient` を別 RSS / HTML scraping / podcast API に差し替え
- `verify_claim()` を evidence 収集付きの verifier に置換
- `EpisodeService` を Repository 経由の DB 永続化に置換
- `SlackNotifier` を FreeeKotsugu と同じ webhook 通知方針で拡張
- OpenAI client を claim 正規化・理由要約補助へ限定利用

## TODO

- claim ごとの外部根拠収集 client を追加
- Slack 向け通知整形の改善
- claim parser の日付・主体抽出精度向上
