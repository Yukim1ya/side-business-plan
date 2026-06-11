# Azure DDoS Protection Standard/Basic の選択基準と設定手順 — セキュリティエンジニアの実装ガイド

Azure への移行に伴い DDoS 攻撃脅威が増加する中、Standard/Basic の機能差を理解し、企業セキュリティ要件に基づいた正しい導入方法を解説します。Splunk 統合による検知フロー、Blue Team 視点のインシデント対応まで、実装レベルでの実践的ガイドをお届けします。

## Azure DDoS Protection とは — Standard/Basic の違い

Azure DDoS Protection は L3/L4 層の攻撃に対する保護を提供します。**Basic（無料）** は基本的な軽減のみ、**Standard（有料）** はリアルタイム検知・適応的軽減を備えます。金融機関や SLA 99.99% 環境では Standard 導入を推奨します。料金は攻撃頻度・SLA 要件・保護リソース数で決まるため、導入前に [Azure 公式料金ページ](https://azure.microsoft.com/ja-jp/pricing/details/ddos-protection/) で最新価格を確認してください。

## 機能・コスト比較表

| 機能 | Basic | Standard |
|------|-------|----------|
| **対応層** | L3/L4 | L3/L4 + L7（Application Gateway WAF で対応） |
| **検知ログ** | 最小限 | リアルタイム詳細ログ（Azure Diagnostic Logs） |
| **アラート機能** | なし | DDoS Alert ダッシュボード、Azure Monitor 統合 |
| **適応的軽減** | 固定パターン | 機械学習ベースのトラフィックプロファイリング |
| **月額費用** | 無料 | 有料（[Azure公式料金ページ](https://azure.microsoft.com/ja-jp/pricing/details/ddos-protection/)参照） |

DDoS 攻撃が月 1 回未満で許容度が高い場合は Basic、重要インフラや SLA 99.99% を保証する環境では Standard 導入を推奨します。

## 設定手順 — Bicep による Infrastructure as Code

Virtual Network レベルで DDoS Protection Plan を紐付けます。Bicep による宣言的設定でエンタープライズ環境を構築します。

```bicep
// ddos-protection.bicep
param location string = 'japaneast'
param environment string = 'production'

resource ddosProtectionPlan 'Microsoft.Network/ddosProtectionPlans@2023-02-01' = {
  name: 'ddos-plan-${environment}'
  location: location
  properties: {}
}

resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-02-01' = {
  name: 'vnet-${environment}'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.0.0.0/16'] }
    ddosProtectionPlan: { id: ddosProtectionPlan.id }
    enableDdosProtection: true
    subnets: [{ name: 'default', properties: { addressPrefix: '10.0.1.0/24' } }]
  }
}

output ddosPlanId string = ddosProtectionPlan.id
```

```bash
az deployment group create --resource-group myResourceGroup \
  --template-file ddos-protection.bicep \
  --parameters location=japaneast environment=production
```

Azure Portal からも設定可能です。エンタープライズ環境ではコード化による自動化・版管理を優先します。

## Splunk 連携による検知実装

Azure DDoS Protection Standard は診断ログを Azure Diagnostic Logs に送信します。これを Event Hub 経由で Splunk に転送し、リアルタイムに DDoS インシデントを検知できます。Splunk HEC（HTTP Event Collector）を有効化し、index=main、sourcetype=azure:eventhub で受信設定します。

### DDoS 検知クエリ

```splunk
index=main sourcetype=azure:eventhub "Attack detected"
| stats count as packet_count by src_ip, attack_type
| where packet_count > 10000
| eval severity=if(packet_count>100000, "Critical", "High")
```

### アラート集計クエリ

```splunk
index=main sourcetype=azure:eventhub "Attack detected"
| stats count as packets, latest(_time) as last_attack by src_ip
| where packets > 5000
```

> **注**: フィールド名・値（"Attack detected" 等）は Azure Diagnostic Logs の設定・バージョンにより異なる場合があります。実環境では `index=main sourcetype=azure:eventhub | fieldsummary` で実際のフィールド構造を確認してから検知クエリを調整してください。

これらのクエリで SOC チームへのリアルタイム通知を実現し、攻撃の早期対応を支援します。

## DDoS インシデント対応フレームワーク（Blue Team 視点）

DDoS 攻撃への対応は 4 ステップフレームワークで体系化します。これにより SLA 遵守と組織的インシデント学習を両立できます。

### Step 1: 検知（Detection）

Azure Monitor・Splunk アラートが自動トリガーされ、SOC オンコールエンジニアに通知が送信されます。baseline トラフィックプロファイル学習により誤検知を最小化します。重要度判定により優先度付けを実施します。

### Step 2: トリアージ（Triage）

検知後 5 分以内に対象リソース（Virtual Network / Public IP）、攻撃タイプ（ボリュメトリック / プロトコル）、攻撃元 IP、ビジネス影響度を確認し、SLA 違反リスクを判定します。地理的脅威インテリジェンスも合わせて確認します。

### Step 3: 緩和（Mitigation）

Azure DDoS Protection Standard が自動軽減を開始します。SLA 超過の場合、Application Gateway WAF を一時有効化するか、Microsoft Azure サポートにエスカレーション依頼します。カスタム軽減ポリシーの適用も検討します。

### Step 4: 事後分析（Post-Incident Analysis）

攻撃終息後 24 時間以内に根本原因分析、ログアーカイブ、改善計画を実施し、検知精度とルール策定に反映します。同一パターンの再発防止に向けたレッスンズラーン報告書を作成します。

## まとめ

- **Basic（無料）か Standard（月 3,000 円）かは、ビジネス要件と攻撃頻度で判定** — 重要インフラ・SLA 99.99% は Standard 推奨
- **Bicep による Infrastructure as Code と Splunk 統合で検知・軽減を自動化** — リアルタイム異常検知と組織的対応を実現
- **4 ステップフレームワーク（検知→トリアージ→緩和→事後分析）で DDoS インシデントに対応** — SLA 遵守と継続改善を両立

#Azure #DDoS #セキュリティ #ネットワークセキュリティ #クラウド
