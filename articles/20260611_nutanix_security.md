# Nutanix Community Edition のセキュリティハードニング — RISS実務経験で学ぶ設定ガイド

本記事では、RISS（情報処理安全確保支援士）資格を持つセキュリティエンジニアが実務経験から、Nutanix Community Edition（CE）の必須セキュリティ対策を解説します。低コストで HCI 技術を習得できる Nutanix CE ですが、セキュリティ設定の情報は限定的です。本記事で分かること：デフォルト設定のリスク、Prism Element の認証強化、AHV ハイパーバイザーのハードニング、ネットワークセグメンテーション戦略、インシデント対応の実践的知見です。想定読者は Nutanix CE 環境を自社構築・運用するインフラエンジニア、検証環境でセキュリティ設定を重視したい DevOps エンジニアです。

## Nutanix CE セキュリティのよくある落とし穴（デフォルト設定の危険性）

CIA トリアッド（機密性・完全性・可用性）の観点から見ると、Nutanix CE の初期デプロイメント状態は「可用性」重視で「機密性」が犠牲になっています。典型的なリスク：
- **HTTP 平文通信**：認証情報の盗聴危険
- **デフォルトパスワード**：単純な初期パスワード
- **ファイアウォール無効**：全ポート開放状態
- **セキュリティアラート未設定**：侵害検知不可

これらは検証環境で放置されることが多く、本番拡張時に問題となります。

## Prism Element で実施すべきセキュリティ設定（認証・アクセス制御）

NIST フレームワークの「アクセス制御（AC）」領域です。Prism Element 管理画面への不正アクセスを防ぐため、以下 4 項目を実施します。

**1. HTTPS 有効化と証明書設定**

デフォルト HTTP は平文通信のため、管理画面へのアクセス認証情報が盗聴される危険があります。
```yaml
# Prism Element: Settings > SSL Settings
SSL_CERTIFICATE_PATH: /etc/nutanix/ssl/server.crt
ENABLE_REDIRECT_HTTP_TO_HTTPS: true
```
自己署名証明書でも良いですが、組織 CA 証明書を使用するとブラウザ警告を消すことができます。

**2. デフォルトパスワード強化**（12文字以上、特殊文字含む）

初期パスワードは必ず変更します。複雑性要件：大文字・小文字・数字・特殊文字を各 1 字以上。
```bash
# Prism UI: 画面右上 > admin > Change Password
# または CVM SSH ログイン後: password_reset コマンド
```

**3. 二要素認証（MFA）の設定**

Prism Element 2024 以降は TOTP ベースの MFA をサポート。Google Authenticator など任意のアプリで対応可能。
```bash
# Prism Element > Settings > Authentication > Enable 2FA
```

**4. ロールベースアクセス制御（RBAC）**

管理者権限の集約は危険です。運用チーム内で役割に応じてロールを分割します。
```bash
# Prism Element > Administration > Users > Add User
# Role: View-Only / Power User / Administrator から選択
```

## AHV ハイパーバイザーのハードニング — ファイアウォール・SSH・CVE対応

NIST IA（認証・識別）領域の強化。AHV ホストの SSH ポートが広く開かれているデフォルトを修正します。

**1. ファイアウォール有効化**
```bash
acli
<acli> > host.acl_config <host-id> inbound_deny_rules "22/tcp from 0.0.0.0/0"
# ※動作確認要
```

**2. SSH 強化設定**
```bash
# /etc/ssh/sshd_config
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
# ※動作確認要
```

**3. CVE パッチ適用フロー**
```bash
# 1. Nutanix セキュリティアドバイザリを確認
#    https://portal.nutanix.com/page/documents/security-advisories
# 2. CVM にログイン: ssh root@<cvm-ip>
# 3. 状態確認: ncli cluster status  # ※動作確認要
# 4. アップデート実行: ncli cluster upgrade-start  # ※動作確認要
```

## ネットワークセグメンテーション実装（管理・VM・ストレージの分離）

NIST SC（システム・通信保護）領域。トラフィック分離で侵害時の被害最小化（ゼロトラスト）を実現します。

**推奨構成**：

| セグメント | VLAN | 用途 | CIDR |
|--|--|--|--|
| 管理 | 10 | Prism/SSH | 10.0.10.0/24 |
| VM | 20 | ゲストVM | 10.0.20.0/24 |
| ストレージ | 30 | iSCSI/NFS | 10.0.30.0/24 |

**ACL ルール例**：
```bash
acli
<acli> > host.acl_config <host-id> inbound_allow_rules \
  "22/tcp from 10.0.10.0/24" \
  "6100-6105/tcp from 10.0.10.0/24"
# ※動作確認要
```

## 運用中の脆弱性管理と Nutanix セキュリティアラート活用

継続的監視で NIST の検出・分析・対応領域を実現します。

**1. Prism Security Dashboard**
```bash
# Prism UI: Security & Compliance > Security Dashboard
# 危険度: Critical(即対応) → High(2週) → Medium(1月)
```

**2. SIEM 連携（Splunk）**
```splunk
index=nutanix event_type=security_alert
| where severity IN (Critical, High)
```

**3. インシデント初動対応**（Blue Team 経験）

1. Prism アラート確認（CVE の痕跡）
2. ファイアウォール確認（セグメンテーション突破検査）
3. /var/log/cvm.log 確認（SSH 侵入有無）
4. IOPS 異常検知（Ransomware 検出）
5. DNS ログ確認（C2 通信検出）

早期発見が被害を最小化します。

## まとめ

Nutanix CE のセキュリティハードニングは3段階で実現：

- **第1段階**：HTTPS・パスワード・SSH 鍵認証 → CIA の「機密性」確保
- **第2段階**：RBAC・ファイアウォール・CVE パッチ → NIST IA・SI 強化
- **第3段階**：ネットワークセグメンテーション・監視・対応計画 → ゼロトラスト実装

実装を通じて CIA トリアッド・NIST フレームワーク・ゼロトラスト原則の具体的応用が理解でき、本番構築の品質向上に繋がります。

#Nutanix #セキュリティ #ハードニング #インフラエンジニア #HCI
