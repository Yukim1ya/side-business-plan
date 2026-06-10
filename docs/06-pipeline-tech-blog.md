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
将軍: new_blog_article.sh --topic "テーマ" を実行 → 家老に自動送信
        │
        ▼
【Phase 1: 企画】
家老 → 足軽A: テーマをもとに企画案を自律作成
             （topic_area・対象読者・構成・差別化を足軽が決定）
             ↓
        足軽B: 一次レビュー（NG → 足軽Aに差し戻し）
             ↓ OK
        軍師: 企画レビュー（revision_needed → 足軽Aに再依頼）
             ↓ approved
【Phase 2: 執筆】
家老 → 足軽C: 承認済み企画案をもとに記事執筆
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

## 使い方（テーマを渡すだけ）

`multi-agent-shogun` リポジトリで以下を実行する。**指定するのはテーマのみ。**

```bash
bash scripts/new_blog_article.sh --topic "Splunk で Kerberoasting を検知する"
```

```bash
bash scripts/new_blog_article.sh --topic "Nutanix CE の初期セットアップ手順"
```

topic_area・対象読者・記事構成・ハッシュタグは、企画作成足軽がテーマをもとに自律的に決定する。

実行すると以下が自動で行われる:
1. `queue/tasks/cmd_blog_XXX.yaml` を自動採番して作成
2. 家老のinboxに起動メッセージを送信
3. 進捗確認コマンドを表示

### 進捗確認

```bash
cat dashboard.md
```

家老が `dashboard.md` の `github_url` フィールドを更新したら完了。

---

## 各フェーズの詳細

### Phase 1-A: 企画案作成（足軽）

足軽はテーマだけを受け取り、以下を**自律的に決定**して企画案を作成する:

| 決定項目 | 説明 |
|---------|------|
| `topic_area` | テーマに最も近い領域（splunk / ad_attack / nutanix / riss / general） |
| `target_reader` | 誰が読むと最も価値があるかを具体的に定義 |
| `title` | 検索キーワードを含む具体的なタイトル案 |
| `outline` | 読者が得るものを最大化する記事構成 |
| `differentiation` | 既存記事との差別化ポイント |
| `hashtags` | note.com で発見されやすいタグ |

企画案のアウトプット形式:

```yaml
proposal:
  title: "Splunk で Kerberoasting を検知する — EventID 4769 の活用法"
  topic_area: "ad_attack"
  target_reader: "Splunk 導入済み環境の Blue Team エンジニア"
  hook: "Kerberoasting は検知が難しいと言われるが、EventID 4769 を正しく絞り込めば現実的に検知できる。"
  outline:
    - "## Kerberoasting とは（攻撃の仕組みを簡潔に）"
    - "## 検知に使う EventID 4769 の見方"
    - "## SPL クエリで検知する"
    - "## 誤検知を減らすチューニング"
    - "## まとめ"
  differentiation: "Blue Team視点で誤検知チューニングまで踏み込む点が差別化"
  estimated_chars: 2500
  hashtags:
    - "#Splunk"
    - "#ActiveDirectory"
    - "#セキュリティ"
    - "#BlueTeam"
```

### Phase 1-B: 企画一次レビュー（別の足軽）

- [ ] タイトルに検索キーワードが含まれているか
- [ ] 対象読者が具体的か（「エンジニア一般」は不可）
- [ ] アウトラインに「まとめ」セクションが含まれているか
- [ ] 差別化ポイントが明確か
- [ ] 筆者のトピック領域に合致しているか

### Phase 1-C: 企画軍師レビュー

- **SEO**: タイトルのキーワードに検索需要があるか
- **独自性**: 同テーマの記事との差別化が成立しているか
- **ブランド**: Splunk・AD検知の専門性を活かせているか
- **実現可能性**: 足軽が実際に書ける内容か

### Phase 2-A: 記事執筆（足軽）

承認済み企画案を元に記事を執筆する（フォーマット仕様は `context/tech_blog.md` 参照）。

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

---

## 記事の保存場所

```
side-business-plan/
└── articles/
    ├── 20260610_splunk_kerberoasting.md
    ├── 20260615_nutanix_ce_setup.md
    └── ...
```

note.com への実際の投稿は手動で行う（GitHub の `.md` ファイルをコピー貼り付け）。

---

## よくある質問

**Q. 足軽が何人必要？**  
1本の記事に最低4名（企画作成・企画レビュー・記事執筆・記事レビュー）。

**Q. 記事1本の生成にどれくらいかかる？**  
差し戻しなしの場合、30〜60分。

**Q. topic_area などを自分で指定したい場合は？**  
`queue/tasks/cmd_blog_XXX.yaml` を直接編集してから家老に送信すれば上書き可能。

---

## トラブルシューティング

### 家老が停止してパイプラインが進まない場合

**症状**: `new_blog_article.sh` を実行してもパイプラインが進まず、`dashboard.md` が更新されない。

**診断コマンド**:

```bash
# 1. 家老のinbox未読件数を確認（0より多ければ未処理メッセージあり）
grep "read: false" queue/inbox/karo.yaml | wc -l

# 2. 家老ペインの状態を確認
tmux capture-pane -t multiagent:agents.0 -p | tail -20

# 3. エージェント全体のステータスを確認
bash scripts/agent_status.sh
```

**原因**: 家老がSession Start手順（自己識別→memory→instructions読み込み）を途中で完了せず、別エージェントのinboxを誤読するなどの誤認識状態に陥っている。

**復旧手順**:

```bash
# multi-agent-shogunリポジトリで実行
bash scripts/inbox_write.sh karo "セッションをリセットせよ。queue/inbox/karo.yamlのread:falseエントリを処理してtech_blogパイプラインを開始せよ。" clear_command shogun
```

`clear_command` タイプのメッセージを受け取ると `inbox_watcher.sh` が自動的に `/clear` を家老ペインに送信する。  
家老は Session Start 手順に従って：
1. 自己識別（`karo`であることを確認）
2. memory読み込み
3. instructions/karo.md 読み込み
4. inbox の未読メッセージを処理してパイプライン再開

**復旧確認**:

```bash
# 家老ペインで以下のようなログが出ていれば復旧成功
tmux capture-pane -t multiagent:agents.0 -p | grep -E "(inbox|cmd_blog|Phase)"

# 未読件数が0に近づいていれば処理中
grep "read: false" queue/inbox/karo.yaml | wc -l
```
