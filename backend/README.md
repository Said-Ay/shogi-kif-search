# shogi-kif-search（backend）

## 開発環境のつくり方
1. uvの導入

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. セットアップ

```bash
git clone https://github.com/Said-Ay/shogi-kif-search.git # リポジトリのクローン
cd shogi-kif-search/backend
uv sync --locked                 # 依存のインストール
uv run pre-commit install        # Git にpre-commitのフックを登録
```

3. テストコマンド
```bash
uv run pytest --cov              # カバレッジ付きテスト
```

## kifファイルの扱いについて
テストデータのkifを`tests/data/`以下に置く。エンジン同士の対局をメインとし、リアルの対局では加えて相手の了承を、オンライン対局サービスではさらに利用規約などを確認すること。kifファイルには絶対に個人情報を残さない。
