#!/usr/bin/env python3
"""
技術記事半自動生成スクリプト
Claude API を使ってテーマ・キーワードから記事ドラフトを生成する。

Usage:
    python generate_article.py --topic "Splunk SPL チートシート" --type splunk
    python generate_article.py --topic "Kerberoasting 検知" --type ad_attack
    python generate_article.py --topic "Nutanix CE セットアップ" --type nutanix
    python generate_article.py --topic "カスタムテーマ" --audience "インフラエンジニア"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import anthropic


SYSTEM_PROMPT = """あなたは情報処理安全確保支援士（RISS）資格を持つ、
Splunk・Active Directory攻撃検知・Nutanixの専門家による技術ブログの記事生成AIです。

記事を生成する際の原則:
- 実務経験に基づいた具体的・実践的な内容にする
- コードサンプルや設定例を必ず含める
- 初心者にも分かりやすく、上級者にも役立つ内容にする
- Zenn / note 向けのMarkdown形式で出力する
- 見出しは ## (H2) から始め、最大4階層まで
- 記事末尾に「まとめ」セクションを必ず含める
"""

TEMPLATES = {
    "splunk": {
        "system_suffix": "Splunk SPLクエリや検知ルールの解説に特化している。",
        "prompt_hint": """
対象読者: SOCアナリスト・セキュリティエンジニア
必須要素:
- SPLクエリのサンプルコード（コードブロック形式）
- ユースケース（どういうインシデントを検知するか）
- よくあるハマりポイントと解決策
- 参考: Splunk公式ドキュメントへの言及
""",
    },
    "ad_attack": {
        "system_suffix": "Active Directory攻撃（レッドチーム）とその検知（ブルーチーム）の両面を解説する。",
        "prompt_hint": """
対象読者: セキュリティエンジニア・SOCアナリスト（Blue Team視点）
必須要素:
- 攻撃の仕組みの概要（図解的な説明）
- 検知に使えるWindowsイベントID一覧（表形式）
- Splunk または KQL での検知クエリ例
- 対策・ハードニング方法
- MITRE ATT&CK フレームワークへの言及（該当するTTP）
""",
    },
    "nutanix": {
        "system_suffix": "Nutanix CE（Community Edition）の構築・運用に特化している。",
        "prompt_hint": """
対象読者: インフラエンジニア・自宅ラボ愛好家
必須要素:
- 手順はコマンドラインベースで具体的に記載
- スクリーンショット代わりの説明（「ここで〇〇が表示される」など）
- 注意点・よくあるエラーと解決策
- 筆者環境スペック（参考として）
""",
    },
    "general": {
        "system_suffix": "幅広い技術トピックに対応する。",
        "prompt_hint": "",
    },
}


def build_prompt(topic: str, article_type: str, audience: str) -> str:
    template = TEMPLATES.get(article_type, TEMPLATES["general"])
    hint = template["prompt_hint"]

    return f"""以下のテーマで技術ブログ記事を生成してください。

## テーマ
{topic}

## 対象読者
{audience}

## 要件
{hint}

## 出力形式
- Markdown形式（Zenn/note 投稿用）
- 文字数: 2000〜4000文字
- コードサンプルは必ずシンタックスハイライト付きコードブロックで記載
- 最初の行は記事タイトル（# で始まる H1）
- タイトル直後に導入文（3〜5行）を置く
"""


def generate_article(
    topic: str,
    article_type: str = "general",
    audience: str = "セキュリティエンジニア・インフラエンジニア",
    output_dir: str = "output",
) -> Path:
    template = TEMPLATES.get(article_type, TEMPLATES["general"])
    system = SYSTEM_PROMPT + template["system_suffix"]

    client = anthropic.Anthropic()

    print(f"生成中: {topic} (type={article_type})", file=sys.stderr)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},  # システムプロンプトをキャッシュ
            }
        ],
        messages=[
            {
                "role": "user",
                "content": build_prompt(topic, article_type, audience),
            }
        ],
    )

    content = response.content[0].text

    # 出力ファイル名: output/YYYYMMDD_HHMMSS_<topic_slug>.md
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)
    slug = topic[:40].replace(" ", "_").replace("/", "-")
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}.md"
    out_file = out_path / filename
    out_file.write_text(content, encoding="utf-8")

    usage = response.usage
    print(
        f"完了: {out_file}\n"
        f"  入力トークン: {usage.input_tokens} "
        f"(キャッシュ作成: {getattr(usage, 'cache_creation_input_tokens', 0)}, "
        f"キャッシュ読込: {getattr(usage, 'cache_read_input_tokens', 0)})\n"
        f"  出力トークン: {usage.output_tokens}",
        file=sys.stderr,
    )

    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claude API で技術記事ドラフトを生成する"
    )
    parser.add_argument("--topic", required=True, help="記事のテーマ・タイトル案")
    parser.add_argument(
        "--type",
        choices=list(TEMPLATES.keys()),
        default="general",
        help="記事タイプ (splunk / ad_attack / nutanix / general)",
    )
    parser.add_argument(
        "--audience",
        default="セキュリティエンジニア・インフラエンジニア",
        help="対象読者",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ディレクトリ (デフォルト: output/)",
    )
    args = parser.parse_args()

    out_file = generate_article(
        topic=args.topic,
        article_type=args.type,
        audience=args.audience,
        output_dir=args.output_dir,
    )
    print(out_file)


if __name__ == "__main__":
    main()
