# 書き起こしコスト（run: anthropic-pdf）

単価（USD / 100万トークン）: claude-haiku-5-5 入力$0.1 出力$0.5, claude-sonnet-5-5 入力$2.0 出力$10.0。Batch API は 50% 引き。

## 呼び出しごと

| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |
|---|---|---|--:|--:|--:|--:|--:|---|
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p80 | merged・split | 7,693 | 4,594 | 17.16 | 0.0031 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p81 | merged・split | 7,814 | 6,688 | 25.3 | 0.0041 | 0.0021 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p84 | simple | 7,585 | 5,049 | 22.5 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p110 | matrix | 6,946 | 3,906 | 16.2 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p12 | simple | 7,455 | 2,557 | 11.91 | 0.0020 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p35 | merged・split | 7,572 | 5,077 | 18.88 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p36 | split | 6,712 | 1,177 | 5.8 | 0.0013 | 0.0006 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p41 | split・merged | 7,468 | 3,466 | 14.94 | 0.0025 | 0.0012 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p17 | merged | 7,845 | 5,932 | 20.09 | 0.0037 | 0.0019 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p20 | merged・split | 7,823 | 7,900 | 25.81 | 0.0047 | 0.0024 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p21 | merged・split | 7,901 | 6,176 | 21.69 | 0.0039 | 0.0019 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p31 | simple | 7,532 | 3,068 | 11.88 | 0.0023 | 0.0011 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p90 | matrix | 8,327 | 29,491 | 93.62 | 0.0156 | 0.0078 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p80 | merged・split | 7,693 | 2,447 | 12.33 | 0.0399 | 0.0199 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p81 | merged・split | 7,814 | 2,916 | 14.06 | 0.0448 | 0.0224 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p84 | simple | 7,585 | 2,156 | 11.38 | 0.0367 | 0.0184 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p110 | matrix | 6,946 | 1,611 | 8.83 | 0.0300 | 0.0150 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p12 | simple | 7,455 | 1,631 | 9.39 | 0.0312 | 0.0156 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p35 | merged・split | 7,572 | 2,228 | 11.0 | 0.0374 | 0.0187 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p36 | split | 6,712 | 352 | 2.91 | 0.0169 | 0.0085 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p41 | split・merged | 7,468 | 1,346 | 7.88 | 0.0284 | 0.0142 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p17 | merged | 7,845 | 3,281 | 15.62 | 0.0485 | 0.0243 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p20 | merged・split | 7,823 | 3,610 | 17.19 | 0.0517 | 0.0259 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p21 | merged・split | 7,901 | 3,004 | 15.12 | 0.0458 | 0.0229 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p31 | simple | 7,532 | 1,636 | 8.33 | 0.0314 | 0.0157 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p90 | matrix | 8,327 | 19,823 | 89.34 | 0.2149 | 0.1074 | end_turn |

## モデル別 合計・1ページ平均

| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| claude-haiku-5-5 | 13 | 98,673 | 85,081 | 0.0524 | 0.0262 | 7,590 | 6,545 | 0.0040 | 0.0020 |
| claude-sonnet-5-5 | 13 | 98,673 | 46,041 | 0.6578 | 0.3289 | 7,590 | 3,542 | 0.0506 | 0.0253 |

**この検証の合計（通常 API）: $0.7102**

## 全ページ処理した場合の見積もり

検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。

| 範囲 | ページ数 | claude-haiku-5-5 通常$ | claude-haiku-5-5 Batch$ | claude-sonnet-5-5 通常$ | claude-sonnet-5-5 Batch$ |
|---|--:|--:|--:|--:|--:|
| 事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編） | 941 | 3.79 | 1.90 | 47.61 | 23.80 |
| 介護 manifest の spec 全部 | 2,533 | 10.21 | 5.11 | 128.14 | 64.07 |
| 障害 manifest の spec 全部 | 1,680 | 6.77 | 3.39 | 84.99 | 42.50 |
| 両分野 spec 全部 | 4,213 | 16.98 | 8.49 | 213.14 | 106.57 |

対象ページ数の内訳: kaigo_kyotsu_r0806=100, kaigo_jigyosho_r0604=237, kaigo_kyotaku_r0604=201, shogai_kyotsu_r0710=63, shogai_jigyosho_r0710=340
