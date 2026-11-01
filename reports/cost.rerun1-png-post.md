# 書き起こしコスト（run: rerun1-png-post）

単価（USD / 100万トークン）: claude-haiku-5-5 入力$0.1 出力$0.5, claude-sonnet-5-5 入力$2.0 出力$10.0。Batch API は 50% 引き。

## 呼び出しごと

| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |
|---|---|---|--:|--:|--:|--:|--:|---|
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p35 |  | 9,975 | 4,656 | 0.0 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p36 |  | 9,975 | 5,234 | 0.0 | 0.0036 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p38 |  | 9,975 | 8,587 | 0.0 | 0.0053 | 0.0026 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p41 |  | 9,975 | 5,815 | 0.0 | 0.0039 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p42 |  | 9,975 | 6,631 | 0.0 | 0.0043 | 0.0022 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p80 |  | 9,975 | 6,339 | 0.0 | 0.0042 | 0.0021 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p84 |  | 9,975 | 4,371 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p12 |  | 9,971 | 11,030 | 0.0 | 0.0065 | 0.0033 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p16 |  | 9,971 | 6,397 | 0.0 | 0.0042 | 0.0021 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p26 |  | 9,971 | 7,623 | 0.0 | 0.0048 | 0.0024 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p35 |  | 9,971 | 5,705 | 0.0 | 0.0039 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p43 |  | 9,971 | 6,210 | 0.0 | 0.0041 | 0.0021 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p44 |  | 9,971 | 5,844 | 0.0 | 0.0039 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p46 |  | 9,971 | 3,972 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p47 |  | 9,971 | 6,866 | 0.0 | 0.0044 | 0.0022 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p53 |  | 9,971 | 16,586 | 0.0 | 0.0093 | 0.0046 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p55 |  | 9,971 | 8,859 | 0.0 | 0.0054 | 0.0027 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p68 |  | 9,971 | 3,991 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p71 |  | 9,971 | 4,477 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p84 |  | 9,971 | 3,901 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p92 |  | 9,971 | 7,682 | 0.0 | 0.0048 | 0.0024 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p93 |  | 9,971 | 6,147 | 0.0 | 0.0041 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p100 |  | 9,971 | 5,628 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p13 |  | 9,995 | 4,897 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p14 |  | 9,995 | 4,558 | 0.0 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p20 |  | 9,995 | 9,333 | 0.0 | 0.0057 | 0.0028 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p31 |  | 9,995 | 3,693 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p60 |  | 9,995 | 7,316 | 0.0 | 0.0047 | 0.0023 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p82 |  | 9,995 | 5,683 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p83 |  | 9,995 | 45,246 | 0.0 | 0.0236 | 0.0118 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p85 |  | 9,995 | 40,732 | 0.0 | 0.0214 | 0.0107 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p87 |  | 9,995 | 38,182 | 0.0 | 0.0201 | 0.0100 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p90 |  | 9,995 | 34,251 | 0.0 | 0.0181 | 0.0091 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p95 |  | 9,995 | 31,659 | 0.0 | 0.0168 | 0.0084 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p99 |  | 9,995 | 36,472 | 0.0 | 0.0192 | 0.0096 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p101 |  | 9,995 | 46,705 | 0.0 | 0.0244 | 0.0122 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p105 |  | 9,995 | 40,288 | 0.0 | 0.0211 | 0.0106 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p108 |  | 9,995 | 35,920 | 0.0 | 0.0190 | 0.0095 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p112 |  | 9,995 | 34,680 | 0.0 | 0.0183 | 0.0092 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p115 |  | 9,995 | 34,765 | 0.0 | 0.0184 | 0.0092 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p125 |  | 9,995 | 26,323 | 0.0 | 0.0142 | 0.0071 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p126 |  | 9,995 | 37,636 | 0.0 | 0.0198 | 0.0099 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p129 |  | 9,995 | 40,612 | 0.0 | 0.0213 | 0.0107 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p132 |  | 9,995 | 40,955 | 0.0 | 0.0215 | 0.0107 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p139 |  | 9,995 | 29,485 | 0.0 | 0.0157 | 0.0079 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p141 |  | 9,995 | 26,739 | 0.0 | 0.0144 | 0.0072 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p146 |  | 9,995 | 32,683 | 0.0 | 0.0173 | 0.0087 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p147 |  | 9,995 | 31,806 | 0.0 | 0.0169 | 0.0085 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p158 |  | 9,995 | 20,339 | 0.0 | 0.0112 | 0.0056 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p272 |  | 9,995 | 3,820 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p273 |  | 9,995 | 4,932 | 0.0 | 0.0035 | 0.0017 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p295 |  | 9,995 | 41,606 | 0.0 | 0.0218 | 0.0109 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p296 |  | 9,995 | 62,521 | 0.0 | 0.0323 | 0.0161 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p297 |  | 9,995 | 61,792 | 0.0 | 0.0319 | 0.0159 | end_turn |
| claude-haiku-5-5 | shogai_kyotsu_r0710 p8 |  | 9,991 | 439 | 0.0 | 0.0012 | 0.0006 | end_turn |
| claude-haiku-5-5 | shogai_kyotsu_r0710 p12 |  | 9,991 | 9,356 | 0.0 | 0.0057 | 0.0028 | end_turn |
| claude-haiku-5-5 | shogai_kyotsu_r0710 p24 |  | 9,991 | 9,240 | 0.0 | 0.0056 | 0.0028 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p35 |  | 9,975 | 2,320 | 0.0 | 0.0432 | 0.0216 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p36 |  | 9,975 | 2,904 | 0.0 | 0.0490 | 0.0245 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p38 |  | 9,975 | 2,787 | 0.0 | 0.0478 | 0.0239 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p41 |  | 9,975 | 2,805 | 0.0 | 0.0480 | 0.0240 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p42 |  | 9,975 | 2,998 | 0.0 | 0.0499 | 0.0250 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p80 |  | 9,975 | 2,608 | 0.0 | 0.0460 | 0.0230 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p84 |  | 9,975 | 2,167 | 0.0 | 0.0416 | 0.0208 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p12 |  | 9,971 | 2,081 | 0.0 | 0.0408 | 0.0204 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p16 |  | 9,971 | 1,504 | 0.0 | 0.0350 | 0.0175 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p26 |  | 9,971 | 4,860 | 0.0 | 0.0685 | 0.0343 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p35 |  | 9,971 | 2,491 | 0.0 | 0.0449 | 0.0224 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p43 |  | 9,971 | 1,432 | 0.0 | 0.0343 | 0.0171 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p44 |  | 9,971 | 1,332 | 0.0 | 0.0333 | 0.0166 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p46 |  | 9,971 | 1,189 | 0.0 | 0.0318 | 0.0159 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p47 |  | 9,971 | 1,291 | 0.0 | 0.0329 | 0.0164 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p53 |  | 9,971 | 1,191 | 0.0 | 0.0319 | 0.0159 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p55 |  | 9,971 | 1,218 | 0.0 | 0.0321 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p68 |  | 9,971 | 1,366 | 0.0 | 0.0336 | 0.0168 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p71 |  | 9,971 | 1,691 | 0.0 | 0.0369 | 0.0184 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p84 |  | 9,971 | 1,499 | 0.0 | 0.0349 | 0.0175 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p92 |  | 9,971 | 4,302 | 0.0 | 0.0630 | 0.0315 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p93 |  | 9,971 | 2,743 | 0.0 | 0.0474 | 0.0237 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p100 |  | 9,971 | 2,363 | 0.0 | 0.0436 | 0.0218 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p13 |  | 9,995 | 2,585 | 0.0 | 0.0458 | 0.0229 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p14 |  | 9,995 | 2,369 | 0.0 | 0.0437 | 0.0218 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p20 |  | 9,995 | 4,865 | 0.0 | 0.0686 | 0.0343 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p31 |  | 9,995 | 1,747 | 0.0 | 0.0375 | 0.0187 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p60 |  | 9,995 | 2,445 | 0.0 | 0.0444 | 0.0222 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p82 |  | 9,995 | 3,664 | 0.0 | 0.0566 | 0.0283 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p83 |  | 9,995 | 30,393 | 0.0 | 0.3239 | 0.1620 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p85 |  | 9,995 | 597 | 0.0 | 0.0260 | 0.0130 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p87 |  | 9,995 | 29,446 | 0.0 | 0.3145 | 0.1572 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p90 |  | 9,995 | 40,157 | 0.0 | 0.4216 | 0.2108 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p95 |  | 9,995 | 1,853 | 0.0 | 0.0385 | 0.0193 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p99 |  | 9,995 | 22,113 | 0.0 | 0.2411 | 0.1206 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p101 |  | 9,995 | 532 | 0.0 | 0.0253 | 0.0127 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p105 |  | 9,995 | 1,416 | 0.0 | 0.0341 | 0.0171 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p108 |  | 9,995 | 1,042 | 0.0 | 0.0304 | 0.0152 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p112 |  | 9,995 | 1,898 | 0.0 | 0.0390 | 0.0195 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p115 |  | 9,995 | 1,349 | 0.0 | 0.0335 | 0.0167 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p125 |  | 9,995 | 26,159 | 0.0 | 0.2816 | 0.1408 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p126 |  | 9,995 | 1,162 | 0.0 | 0.0316 | 0.0158 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p129 |  | 9,995 | 611 | 0.0 | 0.0261 | 0.0131 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p132 |  | 9,995 | 18,717 | 0.0 | 0.2072 | 0.1036 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p139 |  | 9,995 | 390 | 0.0 | 0.0239 | 0.0119 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p141 |  | 9,995 | 1,268 | 0.0 | 0.0327 | 0.0163 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p146 |  | 9,995 | 20,088 | 0.0 | 0.2209 | 0.1104 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p147 |  | 9,995 | 3,103 | 0.0 | 0.0510 | 0.0255 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p158 |  | 9,995 | 425 | 0.0 | 0.0242 | 0.0121 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p272 |  | 9,995 | 2,027 | 0.0 | 0.0403 | 0.0201 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p273 |  | 9,995 | 2,552 | 0.0 | 0.0455 | 0.0228 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p295 |  | 9,995 | 2,367 | 0.0 | 0.0437 | 0.0218 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p296 |  | 9,995 | 5,885 | 0.0 | 0.0788 | 0.0394 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p297 |  | 9,995 | 50,778 | 0.0 | 0.5278 | 0.2639 | end_turn |
| claude-sonnet-5-5 | shogai_kyotsu_r0710 p8 |  | 9,991 | 313 | 0.0 | 0.0231 | 0.0116 | end_turn |
| claude-sonnet-5-5 | shogai_kyotsu_r0710 p12 |  | 9,991 | 3,118 | 0.0 | 0.0512 | 0.0256 | end_turn |
| claude-sonnet-5-5 | shogai_kyotsu_r0710 p24 |  | 9,991 | 1,951 | 0.0 | 0.0395 | 0.0197 | end_turn |

## モデル別 合計・1ページ平均

| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| claude-haiku-5-5 | 57 | 569,179 | 1,087,215 | 0.6005 | 0.3003 | 9,986 | 19,074 | 0.0105 | 0.0053 |
| claude-sonnet-5-5 | 57 | 569,179 | 340,527 | 4.5436 | 2.2718 | 9,986 | 5,974 | 0.0797 | 0.0399 |

**この検証の合計（通常 API）: $5.1442**

## 全ページ処理した場合の見積もり

検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。

| 範囲 | ページ数 | claude-haiku-5-5 通常$ | claude-haiku-5-5 Batch$ | claude-sonnet-5-5 通常$ | claude-sonnet-5-5 Batch$ |
|---|--:|--:|--:|--:|--:|
| 事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編） | 941 | 9.91 | 4.96 | 75.01 | 37.50 |
| 介護 manifest の spec 全部 | 2,533 | 26.69 | 13.34 | 201.91 | 100.95 |
| 障害 manifest の spec 全部 | 1,680 | 17.70 | 8.85 | 133.91 | 66.96 |
| 両分野 spec 全部 | 4,213 | 44.38 | 22.19 | 335.82 | 167.91 |

対象ページ数の内訳: kaigo_kyotsu_r0806=100, kaigo_jigyosho_r0604=237, kaigo_kyotaku_r0604=201, shogai_kyotsu_r0710=63, shogai_jigyosho_r0710=340
