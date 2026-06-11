# Active Directory Certificate Services設定不備の検知と対策【ESC1-8脆弱性の実務ガイド】

## 導入文

本記事では、Active Directory Certificate Services (AD CS) の設定ミスから生じるESC1〜ESC8脆弱性と、その検知・対策方法を解説します。特にESC1（テンプレート権限昇格）とESC8（NTLM Relay）は攻撃インパクトが大きく、Blue Teamセキュリティエンジニア・AD管理者必読の内容です。ここでは実務経験に基づいた検知ルール設計と、Splunkダッシュボード構築までカバーします。

## AD CS設定不備とは（ESC1-8概要）

Active Directory Certificate Servicesは、組織内のデジタル証明書を発行・管理するWindows認証基盤です。設定不備により、攻撃者が以下を悪用できます：

### ESC1〜ESC8の全体像

| ESC種別 | 攻撃手法 | インパクト | 難易度 |
|--------|--------|---------|-------|
| **ESC1** | テンプレート権限昇格 | 権限奪取（高） | 中 |
| **ESC8** | NTLM Relay活用 | 認証バイパス（高） | 中 |
| ESC2 | オブジェクト制御権限悪用 | 権限奪取 | 中 |
| ESC3 | 登録エージェントテンプレート悪用 | なりすまし | 低 |
| ESC4 | アクセス制御リスト(ACL)設定ミス | 権限奪取 | 高 |
| ESC5 | 親オブジェクト権限継承 | 権限昇格 | 高 |
| ESC6 | EDITF_ATTRIBUTESUBJECTALTNAME2フラグ悪用（SAN） | 権限奪取 | 中 |
| ESC7 | CA ACL設定不備 | 権限奪取 | 高 |

本記事では、インパクトが最も大きい**ESC1とESC8**に焦点を当て、詳細な検知パターンと対策を提示します。

## 攻撃シナリオ：Certipy・PrivEsc経路

### ESC1: テンプレート権限昇格の流れ

```powershell
# 【注意】以下は攻撃ツールの説明であり、実環境での実行は推奨しません
# Certipy を使用したESC1エクスプロイト（参考情報）
certipy find -u attacker@example.com -p password -u example.com/attacker -dc-ip 192.168.1.10
certipy req -u attacker@example.com -p password -ca 'example-CA' -template Administrator
certipy auth -pfx administrator.pfx -username administrator
```

攻撃者は以下のステップで管理者権限を奪取します：

1. **AD CS テンプレート列挙** → 権限設定ミスのあるテンプレートを発見
2. **証明書リクエスト送信** → 攻撃者の指定したサブジェクトで証明書を取得
3. **Kerberos認証代理** → 管理者アカウント相当の証明書で認証
4. **権限昇格完了** → Domainロールで任意操作実行可能

### ESC8: NTLM Relay経由の権限奪取

ESC8は、WebEnrollmentサービス（HTTP）を悪用し、NTLMリレー攻撃を仕掛けます：

```bash
# 【注意】以下は理論的説明であり、実環境での実行は推奨しません
# Responder + impacket-ntlmrelayx を使用した NTLM Relay
responder -I eth0 -v
ntlmrelayx.py -t http://ca-server/certsrv/certfnsh.asp ...
```

## Windows イベントログでの検知（EventCode 4899, 4688他）

### 前提条件：監査ポリシーの有効化

EventCode 4899（証明書テンプレート変更）は、デフォルトではWindows Security Logに記録されません。以下の監査ポリシーを有効化する必要があります：

```powershell
# 監査ポリシー設定（Group Policy / local gpedit）
# 場所: Computer Configuration > Windows Settings > Security Settings > Advanced Audit Policy
# ポリシー: Public Key Infrastructure (PKI) 関連の監査を有効化
auditpol /set /subcategory:"Certification Services" /success:enable /failure:enable
```

### 検知対象イベントコード

- **EventCode 4899**: テンプレート変更（ESC1の兆候）
- **EventCode 4688**: ツール使用検知
- **EventCode 4625**: ログイン失敗（Relay失敗）
- **EventCode 4624**: ログイン成功

## Splunk検知ルール実装例

### ESC1検知: テンプレート権限昇格の異常検知

```splunk
index=windows sourcetype=WinEventLog EventCode=4899 
| stats count by ComputerName, Template_Name, RequestID
| where count > 1 
```

**解説**: EventCode 4899が短期間に複数回発生する場合、テンプレート権限の変更が行われています。管理者アカウントをホワイトリスト化して誤検知を削減します。このクエリをSplunk Webで「名前を付けて保存」→「アラート」として登録し、検知時にメール通知を設定してください。

### ESC8検知: NTLM Relay経由の認証異常

```splunk
index=windows sourcetype=WinEventLog (EventCode=4624 OR EventCode=4625)
| transaction ComputerName maxpause=30s
| where eventcount > 5 AND duration < 60
| search NOT user IN (admin_accounts_whitelist)
```

**解説**: 30秒以内に5件以上の認証イベント（成功・失敗混在）が集中している場合、Relay攻撃の兆候です。バッチアカウントはホワイトリスト化します。上記と同様にSplunk Webでアラートとして保存し、重大度「High」で通知設定することを推奨します。

## 対策：テンプレート権限・監査の設定

### ステップ1: 危険なテンプレート権限の排除

```powershell
# AD CS テンプレートの権限確認・修正
# 管理ツール > Certification Authority > Certificate Templates (右クリック)
# Properties > Security タブで以下を確認：

# ⚠️ 危険な権限
# - "Authenticated Users" に "Enroll" 権限
# - "Everyone" に任意の権限

# ✅ 推奨設定
# - "Domain Admins" のみに管理権限
# - 特定グループのみに "Enroll" 権限
# - 監査ポリシー有効化
```

### ステップ2: 監査ポリシーの有効化

```powershell
# Group Policy Editor (gpedit.msc) で以下を設定：
# コンピュータの構成 > ポリシー > Windows 設定 > セキュリティ設定 > 詳細監査ポリシー構成
# > オブジェクト アクセス > Certificate Services (ENABLED)

# または PowerShell で確認
auditpol /get /category:"Object Access"
```

### ステップ3: Splunk検知ダッシュボード構築

上述のSPLクエリをダッシュボード上でパネル化します：
- EventCode 4899の異常値アラート
- NTLM Relay疑いの認証イベント集計

## まとめ

AD CS設定不備は組織のActive Directory全体の防御を無力化する重大なリスクです：

- **ESC1・ESC8が最優先**: Blue Team優先検知対象
- **監査ポリシーの前提条件**: EventCode 4899はデフォルト記録なし
- **Splunk で検知自動化**: Certipyツール使用や異常な権限操作を24時間監視
- **テンプレート権限の定期レビュー**: 半期ごとの権限棚卸し実施推奨

#ActiveDirectory #PKI #セキュリティ #Splunk #ESC脆弱性