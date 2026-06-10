# Claude Code で自動化する副業プラン集

**作成日**: 2026-06-10  
**対象**: Claude Code（Claude API）を活用して自動化・効率化できる副業

## ドキュメント構成

| ファイル | 内容 |
|---------|------|
| [docs/01-evaluation.md](docs/01-evaluation.md) | プラン評価基準・比較マトリクス |
| [docs/02-plan-security-docs.md](docs/02-plan-security-docs.md) | **★推奨** セキュリティ文書自動生成サービス |
| [docs/03-plan-code-review-saas.md](docs/03-plan-code-review-saas.md) | AIコードレビュー SaaS |
| [docs/04-plan-tech-blog.md](docs/04-plan-tech-blog.md) | 技術ブログ自動生成×マネタイズ |
| [docs/05-risks.md](docs/05-risks.md) | リスク・注意事項 |
| [docs/06-pipeline-tech-blog.md](docs/06-pipeline-tech-blog.md) | **プランC** MASパイプライン詳細手順 |

## 推奨プランサマリー

| プラン | 月収目安 | 開始難易度 | Claude Code活用度 |
|--------|---------|-----------|-----------------|
| **A: セキュリティ文書生成** | **10〜30万円** | **低** | **★★★★★** |
| B: コードレビュー SaaS | 5〜15万円 | 高 | ★★★★★ |
| C: 技術ブログ自動化 | 2〜10万円 | 低 | ★★★☆☆ |

**最優先推奨: プランA**（情報処理安全確保支援士資格 × Claude Code の組み合わせが最大の差別化要因）

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
