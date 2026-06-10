# プランC 記事作成パイプライン（multi-agent-shogun連携）

**対象**: プランC（技術ブログ自動化）を multi-agent-shogun で実行する手順

---

## なぜパイプラインを使うのか

`scripts/generate_article.py` は1回のAPI呼び出しで記事を生成するが、品質担保ができない。
パイプラインでは複数の足軽・軍師が段階的にレビューするため、**投稿できる品質の記事**が出力される。

| | スクリプト単発 | パイプライン |
|---|---|---|
| 生成時間 | 1〜2分 | 30〜60分 |
| 品質チェック | なし | 足軽×2回 + 軍師×2回 |
| 企画の妥当性確認 | なし | 軍師がSEO・差別化を評価 |
| GitHubアップロード | 手動 | 家老が自動実行 |

---

## 前提条件

- `multi-agent-shogun` が起動していること（`./shutsujin_departure.sh` で起動）
- 家老・軍師・足軽が少なくとも1名ずつ待機中であること
- `multi-agent-shogun/context/tech_blog.md` が存在すること（各エージェントの参照先）

---

## パイプライン全体図

```
将軍: cmd_XXX.yaml を作成 → 家老に送信
        │
        ▼
【Phase 1: 企画】
家老 → 足軽A: 企画案作成
             ↓
        足軽B: 一次レビュー（NG → 足軽Aに差し戻し）
             ↓ OK
        軍師: 企画レビュー（revision_needed → 足軽Aに再依頼）
             ↓ approved
【Phase 2: 執筆】
家老 → 足軽C: 記事執筆
             ↓
        足軽D: 一次レビュー（NG → 足軽Cに差し戻し）
             ↓ OK
        軍師: 記事レビュー（revision_needed → 足軽Cに再依頼）
             ↓ approved
【Phase 3: アップロード】
家老: articles/ にコミット → GitHub Push
        │
        ▼
   dashboard.md に完了URL記録
```

---

## 使い方（将軍視点）

### Step 1: コマンドYAMLを作成する

`multi-agent-shogun` リポジトリで以下を実行:

```bash
# テンプレートをコピー
cp templates/cmd_tech_blog.yaml queue/tasks/cmd_050.yaml
```

### Step 2: YAMLの `article_request` を埋める

```yaml
article_request:
  topic: "Splunk で Kerberoasting を検知する"
  topic_area: "ad_attack"
  target_reader: "Blue Team のセキュリティエンジニア（Splunk導入済み環境）"
  notes: "EventID 4769 を中心に解説。SPLクエリを必ず含める。"
```

### Step 3: 家老に送信する

```bash
bash scripts/inbox_write.sh karo "cmd_050を書いた。実行せよ。" cmd_new shogun
```

### Step 4: 完了を待つ

家老が `dashboard.md` を更新したら完了。`github_url` に記事のURLが記録される。

---

## コマンドYAML フィールド解説

```yaml
cmd_id: cmd_050           # 連番。既存のcmdと被らないように

article_request:
  topic:        # 記事テーマ。具体的に書くほど品質が上がる
  topic_area:   # splunk / ad_attack / nutanix / riss / general から選ぶ
  target_reader: # 誰向けか。「エンジニア一般」は不可。具体的に書く
  notes:        # 特に含めたい内容・禁止事項など。なければ空文字 ""
```

### `topic_area` の選び方

| 値 | 使う場面 |
|---|---|
| `splunk` | SPLクエリ・検知ルール・ダッシュボード |
| `ad_attack` | Kerberoasting・Pass-the-Hash・Golden Ticket 等の検知と対策 |
| `nutanix` | Nutanix CE の構築・運用・トラブルシュート |
| `riss` | RISS試験対策・過去問解説・午後問の解き方 |
| `general` | 上記に当てはまらない汎用セキュリティ・IT話題 |

---

## 各フェーズの詳細

### Phase 1-A: 企画案作成（足軽）

足軽が以下の形式で企画案を出力する:

```yaml
proposal:
  title: "Splunk で Kerberoasting を検知する — EventID 4769 の活用法"
  topic_area: "ad_attack"
  target_reader: "Splunk 導入済み環境の Blue Team エンジニア"
  hook: "Kerberoasting は検知が難しいと言われるが、EventID 4769 を正しく絞り込めば現実的に検知できる。本記事では実践的なSPLクエリを紹介する。"
  outline:
    - "## Kerberoasting とは（攻撃の仕組みを簡潔に）"
    - "## 検知に使う EventID 4769 の見方"
    - "## SPL クエリで検知する"
    - "## 誤検知を減らすチューニング"
    - "## まとめ"
  differentiation: "既存記事はKerberoastingの攻撃手順解説が多い。本記事はBlue Team視点で誤検知チューニングまで踏み込む点が差別化。"
  estimated_chars: 2500
  hashtags:
    - "#Splunk"
    - "#ActiveDirectory"
    - "#セキュリティ"
    - "#BlueTeam"
```

### Phase 1-B: 企画一次レビュー（別の足軽）

以下の項目を全てチェックする:

- [ ] タイトルに検索キーワードが含まれているか
- [ ] 対象読者が具体的か（「エンジニア一般」は不可）
- [ ] アウトラインに「まとめ」セクションが含まれているか
- [ ] 差別化ポイントが明確か
- [ ] 筆者のトピック領域に合致しているか

### Phase 1-C: 企画軍師レビュー

軍師が以下を評価して `approved` / `revision_needed` を返す:

- **SEO**: タイトルのキーワードに検索需要があるか
- **独自性**: 同テーマの記事との差別化が成立しているか
- **ブランド**: RISS・Splunk・AD検知の専門性を活かせているか
- **実現可能性**: 足軽が実際に書ける内容か

### Phase 2-A: 記事執筆（足軽）

承認済み企画案を元に、以下の形式で記事を執筆する:

```markdown
# Splunk で Kerberoasting を検知する — EventID 4769 の活用法

Kerberoasting は…（導入文3〜5行）

## Kerberoasting とは
…

## 検知に使う EventID 4769 の見方
…

## SPL クエリで検知する

```splunk
index=windows EventCode=4769
  Ticket_Encryption_Type=0x17
| stats count by src_ip, Account_Name
| where count > 5
```

## 誤検知を減らすチューニング
…

## まとめ
- EventID 4769 の Encryption_Type=0x17 が Kerberoasting の主要シグネチャ
- count > 5 のしきい値で誤検知を大幅削減できる
- 定期的なサービスアカウント棚卸しとセットで運用する

#Splunk #ActiveDirectory #セキュリティ #BlueTeam
```

### Phase 2-B: 記事一次レビュー（別の足軽）

- [ ] 文字数が 1500〜4000字の範囲内か
- [ ] H1タイトルが企画案と一致しているか
- [ ] 導入文が3〜5行あるか
- [ ] 全H2セクションが企画アウトライン通りに存在するか
- [ ] 「まとめ」に3点以上の要点が箇条書きされているか
- [ ] コードブロックに言語指定があるか
- [ ] ハッシュタグが3〜5個付いているか

### Phase 2-C: 記事軍師レビュー

- **技術的正確性**: コマンド・クエリに誤りがないか
- **実践的価値**: 読んですぐ試せる具体性があるか
- **文章品質**: 論理の流れが自然か
- **企画との一致**: 承認された企画の意図が反映されているか

### Phase 3: GitHub アップロード（家老）

軍師承認後、家老が `articles/YYYYMMDD_<slug>.md` として
`side-business-plan` リポジトリにコミットする。

---

## 差し戻しが発生した場合

各レビューで NG / `revision_needed` が出た場合:

1. 家老がレビュー指摘を元に **redo タスク**を作成
2. 元の足軽（または別の足軽）が修正を実施
3. 再度レビューフローへ

差し戻しは何回でも発生しうる。軍師の指摘が明確なため、通常2回以内で承認される。

---

## 記事の保存場所

完成した記事は以下に保存される:

```
side-business-plan/
└── articles/
    ├── 20260610_splunk_kerberoasting.md
    ├── 20260615_nutanix_ce_setup.md
    └── ...
```

GitHub URL は `dashboard.md` の完了記録に残る。
note.com への実際の投稿は手動で行う（コピー貼り付け）。

---

## よくある質問

**Q. 足軽が何人必要？**  
1本の記事に最低4名（企画作成・企画レビュー・記事執筆・記事レビュー）。並行して別の記事を進める場合はさらに必要。

**Q. 記事1本の生成にどれくらいかかる？**  
差し戻しなしの場合、30〜60分。差し戻しが1回発生すると+15〜30分。

**Q. note.com への投稿は自動化できる？**  
現時点では自動化していない。GitHub に上がった `.md` ファイルをコピーして note のエディタに貼り付ける。
