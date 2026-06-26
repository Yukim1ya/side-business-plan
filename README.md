# 個人開発収益化プラン集

**作成日**: 2026-06-10  **最終更新**: 2026-06-26  
**目標**: エンジニアとしての技量向上 × 収益化の両立

## ドキュメント構成

| ファイル | 内容 |
|---------|------|
| [docs/01-evaluation.md](docs/01-evaluation.md) | プラン評価基準・比較マトリクス |
| [docs/02-plan-security-docs.md](docs/02-plan-security-docs.md) | プランA: セキュリティ文書自動生成サービス |
| [docs/03-plan-code-review-saas.md](docs/03-plan-code-review-saas.md) | プランB: AIコードレビュー SaaS |
| [docs/04-plan-tech-blog.md](docs/04-plan-tech-blog.md) | プランC: 技術ブログ自動生成×マネタイズ |
| [docs/05-risks.md](docs/05-risks.md) | リスク・注意事項 |
| [docs/06-pipeline-tech-blog.md](docs/06-pipeline-tech-blog.md) | プランC: MASパイプライン詳細手順 |
| [docs/07-plan-gallopia-saas.md](docs/07-plan-gallopia-saas.md) | プランD: 競馬AI予測SaaS（参考・保留中） |
| [docs/08-plan-bishoujo-game.md](docs/08-plan-bishoujo-game.md) | プランE: 美少女ゲーム開発（インディーVN） |
| [docs/09-plan-pm-sim-game.md](docs/09-plan-pm-sim-game.md) | **★現在注力** プランF: ITプロジェクト管理シミュレーションゲーム |

## プラン比較サマリー

| プラン | 月収目安 | 開始難易度 | スキルアップ効果 | 技術的モート |
|--------|---------|-----------|--------------|------------|
| A: セキュリティ文書生成 | 10〜30万円 | 低 | ★★☆☆☆ | ★★☆☆☆ |
| B: コードレビュー SaaS | 5〜20万円 | 高 | ★★★★☆ | ★★★☆☆ |
| C: 技術ブログ自動化 | 2〜10万円 | 低 | ★★☆☆☆ | ★☆☆☆☆ |
| D: 競馬AI予測SaaS | 5〜20万円 | 中 | ★★★★★ | ★★★★★ |
| E: 美少女ゲーム開発 | 1〜30万円+ | 中 | ★★★★★ | ★★★★☆ |
| **F: ITプロジェクト管理SIM** | **2〜100万円+** | **中** | **★★★★★** | **★★★★★** |

## 現在の推奨: プランF（ITプロジェクト管理シミュレーション）

```
Phase 1（今すぐ〜2ヶ月）: コアシステム実装
  → Unity C# でゲームロジック設計（ProjectState / SprintSystem / EventSystem）
  → まずテキストのみのプロトタイプでゲームループを動かす
  → UI Toolkit でパラメータダッシュボードを実装

Phase 2（3〜5ヶ月）: コンテンツ充実・α版
  → イベントカード50種・5ゲームモード実装
  → エンジニア仲間にプレイしてもらいフィードバック収集

Phase 3（6ヶ月〜）: Steam / itch.io リリース + B2B展開
  → Steam出品・X/Qiitaで「エンジニアが作ったPMゲーム」として発信
  → IT研修会社へのB2Bライセンス営業（月収30〜100万円目標）
```

---

## スクリプト

### `scripts/generate_article.py` — 技術記事生成（プランC用）

Claude API で技術ブログ記事のドラフトを半自動生成する。

**前提条件**:
```bash
pip install anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

**使い方**:
```bash
# Splunk 記事
python scripts/generate_article.py --topic "Splunk SPL チートシート" --type splunk

# AD攻撃検知 記事
python scripts/generate_article.py --topic "Kerberoasting 検知" --type ad_attack

# Nutanix 記事
python scripts/generate_article.py --topic "Nutanix CE セットアップ" --type nutanix

# カスタムテーマ
python scripts/generate_article.py --topic "カスタムテーマ" --audience "インフラエンジニア"
```

生成された記事は `output/YYYYMMDD_HHMMSS_<topic>.md` に保存される。

---

## タスク管理

[GitHub Issues](https://github.com/Yukim1ya/side-business-plan/issues) でロードマップのタスクを管理。
