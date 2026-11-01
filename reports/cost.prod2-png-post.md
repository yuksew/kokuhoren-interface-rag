# 書き起こしコスト（run: prod2-png-post）

単価（USD / 100万トークン）: claude-haiku-5-5 入力$0.1 出力$0.5, claude-sonnet-5-5 入力$2.0 出力$10.0。Batch API は 50% 引き。

## 呼び出しごと

| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |
|---|---|---|--:|--:|--:|--:|--:|---|
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p43 |  | 10,094 | 3,943 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p44 |  | 10,094 | 4,888 | 0.0 | 0.0035 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p47 |  | 10,094 | 5,613 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p49 |  | 10,094 | 4,486 | 0.0 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p51 |  | 10,094 | 8,469 | 0.0 | 0.0052 | 0.0026 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p52 |  | 10,094 | 5,720 | 0.0 | 0.0039 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p53 |  | 10,094 | 3,725 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p54 |  | 10,094 | 3,135 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p55 |  | 10,094 | 3,700 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p56 |  | 10,094 | 8,438 | 0.0 | 0.0052 | 0.0026 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p57 |  | 10,094 | 7,628 | 0.0 | 0.0048 | 0.0024 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p58 |  | 10,094 | 3,740 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p59 |  | 10,094 | 3,572 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p61 |  | 10,094 | 2,697 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p65 |  | 10,094 | 5,518 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p67 |  | 10,094 | 4,013 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p68 |  | 10,094 | 3,259 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p69 |  | 10,094 | 3,512 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p70 |  | 10,094 | 2,828 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p71 |  | 10,094 | 6,172 | 0.0 | 0.0041 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p72 |  | 10,094 | 5,272 | 0.0 | 0.0036 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p74 |  | 10,094 | 5,323 | 0.0 | 0.0037 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p75 |  | 10,094 | 5,048 | 0.0 | 0.0035 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p76 |  | 10,094 | 3,746 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p77 |  | 10,094 | 2,402 | 0.0 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p78 |  | 10,094 | 5,999 | 0.0 | 0.0040 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p79 |  | 10,094 | 7,374 | 0.0 | 0.0047 | 0.0023 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p80 |  | 10,094 | 4,235 | 0.0 | 0.0031 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p81 |  | 10,094 | 4,055 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p82 |  | 10,094 | 4,827 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p83 |  | 10,094 | 6,068 | 0.0 | 0.0040 | 0.0020 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p84 |  | 10,094 | 3,332 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p85 |  | 10,094 | 3,551 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p93 |  | 10,094 | 2,440 | 0.0 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p94 |  | 10,094 | 4,464 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p95 |  | 10,094 | 4,795 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p97 |  | 10,094 | 2,696 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p98 |  | 10,094 | 4,149 | 0.0 | 0.0031 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p99 |  | 10,094 | 4,717 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p101 |  | 10,094 | 2,022 | 0.0 | 0.0020 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p102 |  | 10,094 | 3,847 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p103 |  | 10,094 | 4,243 | 0.0 | 0.0031 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p105 |  | 10,094 | 2,830 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p106 |  | 10,094 | 3,697 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p108 |  | 10,094 | 3,053 | 0.0 | 0.0025 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p109 |  | 10,094 | 3,739 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p111 |  | 10,094 | 2,690 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p112 |  | 10,094 | 4,115 | 0.0 | 0.0031 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p114 |  | 10,094 | 5,290 | 0.0 | 0.0037 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p115 |  | 10,094 | 2,007 | 0.0 | 0.0020 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p117 |  | 10,094 | 2,712 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p118 |  | 10,094 | 3,931 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p119 |  | 10,094 | 3,566 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p120 |  | 10,094 | 3,322 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p121 |  | 10,094 | 3,802 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p123 |  | 10,094 | 2,529 | 0.0 | 0.0023 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p124 |  | 10,094 | 3,129 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p125 |  | 10,094 | 2,869 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p126 |  | 10,094 | 2,698 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p127 |  | 10,094 | 2,816 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p129 |  | 10,094 | 2,222 | 0.0 | 0.0021 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p130 |  | 10,094 | 3,927 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p131 |  | 10,094 | 1,590 | 0.0 | 0.0018 | 0.0009 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p132 |  | 10,094 | 2,867 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p133 |  | 10,094 | 2,879 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p135 |  | 10,094 | 5,550 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p136 |  | 10,094 | 2,856 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p138 |  | 10,094 | 2,739 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p139 |  | 10,094 | 3,044 | 0.0 | 0.0025 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p140 |  | 10,094 | 2,819 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p142 |  | 10,094 | 4,404 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p143 |  | 10,094 | 2,474 | 0.0 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p145 |  | 10,094 | 3,341 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p146 |  | 10,094 | 4,393 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p147 |  | 10,094 | 3,309 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p148 |  | 10,094 | 1,283 | 0.0 | 0.0017 | 0.0008 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p149 |  | 10,094 | 3,421 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p150 |  | 10,094 | 2,156 | 0.0 | 0.0021 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p151 |  | 10,094 | 2,763 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p152 |  | 10,094 | 3,103 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p153 |  | 10,094 | 2,089 | 0.0 | 0.0021 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p154 |  | 10,094 | 2,534 | 0.0 | 0.0023 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p155 |  | 10,094 | 2,962 | 0.0 | 0.0025 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p156 |  | 10,094 | 2,725 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p157 |  | 10,094 | 2,653 | 0.0 | 0.0023 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_kyotaku_r0604 p158 |  | 10,094 | 3,193 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p43 |  | 10,094 | 1,282 | 0.0 | 0.0330 | 0.0165 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p44 |  | 10,094 | 2,307 | 0.0 | 0.0433 | 0.0216 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p47 |  | 10,094 | 1,987 | 0.0 | 0.0401 | 0.0200 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p49 |  | 10,094 | 2,319 | 0.0 | 0.0434 | 0.0217 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p51 |  | 10,094 | 2,286 | 0.0 | 0.0430 | 0.0215 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p52 |  | 10,094 | 2,342 | 0.0 | 0.0436 | 0.0218 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p53 |  | 10,094 | 1,559 | 0.0 | 0.0358 | 0.0179 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p54 |  | 10,094 | 1,223 | 0.0 | 0.0324 | 0.0162 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p55 |  | 10,094 | 2,088 | 0.0 | 0.0411 | 0.0205 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p56 |  | 10,094 | 4,556 | 0.0 | 0.0657 | 0.0329 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p57 |  | 10,094 | 3,563 | 0.0 | 0.0558 | 0.0279 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p58 |  | 10,094 | 2,044 | 0.0 | 0.0406 | 0.0203 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p59 |  | 10,094 | 1,713 | 0.0 | 0.0373 | 0.0187 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p61 |  | 10,094 | 1,138 | 0.0 | 0.0316 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p65 |  | 10,094 | 2,376 | 0.0 | 0.0439 | 0.0220 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p67 |  | 10,094 | 1,742 | 0.0 | 0.0376 | 0.0188 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p68 |  | 10,094 | 1,716 | 0.0 | 0.0373 | 0.0187 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p69 |  | 10,094 | 2,290 | 0.0 | 0.0431 | 0.0215 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p70 |  | 10,094 | 1,326 | 0.0 | 0.0334 | 0.0167 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p71 |  | 10,094 | 2,447 | 0.0 | 0.0447 | 0.0223 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p72 |  | 10,094 | 2,609 | 0.0 | 0.0463 | 0.0231 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p74 |  | 10,094 | 2,484 | 0.0 | 0.0450 | 0.0225 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p75 |  | 10,094 | 2,275 | 0.0 | 0.0429 | 0.0215 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p76 |  | 10,094 | 2,548 | 0.0 | 0.0457 | 0.0228 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p77 |  | 10,094 | 967 | 0.0 | 0.0299 | 0.0149 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p78 |  | 10,094 | 2,513 | 0.0 | 0.0453 | 0.0227 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p79 |  | 10,094 | 2,759 | 0.0 | 0.0478 | 0.0239 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p80 |  | 10,094 | 1,986 | 0.0 | 0.0400 | 0.0200 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p81 |  | 10,094 | 2,316 | 0.0 | 0.0433 | 0.0217 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p82 |  | 10,094 | 2,503 | 0.0 | 0.0452 | 0.0226 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p83 |  | 10,094 | 2,752 | 0.0 | 0.0477 | 0.0239 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p84 |  | 10,094 | 1,278 | 0.0 | 0.0330 | 0.0165 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p85 |  | 10,094 | 1,448 | 0.0 | 0.0347 | 0.0173 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p93 |  | 10,094 | 1,132 | 0.0 | 0.0315 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p94 |  | 10,094 | 2,247 | 0.0 | 0.0427 | 0.0213 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p95 |  | 10,094 | 2,406 | 0.0 | 0.0442 | 0.0221 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p97 |  | 10,094 | 1,191 | 0.0 | 0.0321 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p98 |  | 10,094 | 2,128 | 0.0 | 0.0415 | 0.0207 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p99 |  | 10,094 | 2,308 | 0.0 | 0.0433 | 0.0216 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p101 |  | 10,094 | 1,193 | 0.0 | 0.0321 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p102 |  | 10,094 | 2,137 | 0.0 | 0.0416 | 0.0208 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p103 |  | 10,094 | 2,278 | 0.0 | 0.0430 | 0.0215 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p105 |  | 10,094 | 1,197 | 0.0 | 0.0322 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p106 |  | 10,094 | 1,970 | 0.0 | 0.0399 | 0.0199 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p108 |  | 10,094 | 1,182 | 0.0 | 0.0320 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p109 |  | 10,094 | 1,846 | 0.0 | 0.0386 | 0.0193 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p111 |  | 10,094 | 1,181 | 0.0 | 0.0320 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p112 |  | 10,094 | 1,829 | 0.0 | 0.0385 | 0.0192 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p114 |  | 10,094 | 2,835 | 0.0 | 0.0485 | 0.0243 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p115 |  | 10,094 | 773 | 0.0 | 0.0279 | 0.0140 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p117 |  | 10,094 | 1,145 | 0.0 | 0.0316 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p118 |  | 10,094 | 1,971 | 0.0 | 0.0399 | 0.0199 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p119 |  | 10,094 | 1,637 | 0.0 | 0.0366 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p120 |  | 10,094 | 1,498 | 0.0 | 0.0352 | 0.0176 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p121 |  | 10,094 | 1,763 | 0.0 | 0.0378 | 0.0189 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p123 |  | 10,094 | 1,176 | 0.0 | 0.0319 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p124 |  | 10,094 | 1,946 | 0.0 | 0.0396 | 0.0198 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p125 |  | 10,094 | 1,480 | 0.0 | 0.0350 | 0.0175 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p126 |  | 10,094 | 1,490 | 0.0 | 0.0351 | 0.0175 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p127 |  | 10,094 | 1,568 | 0.0 | 0.0359 | 0.0179 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p129 |  | 10,094 | 1,200 | 0.0 | 0.0322 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p130 |  | 10,094 | 1,875 | 0.0 | 0.0389 | 0.0195 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p131 |  | 10,094 | 1,441 | 0.0 | 0.0346 | 0.0173 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p132 |  | 10,094 | 1,448 | 0.0 | 0.0347 | 0.0173 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p133 |  | 10,094 | 1,532 | 0.0 | 0.0355 | 0.0178 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p135 |  | 10,094 | 2,923 | 0.0 | 0.0494 | 0.0247 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p136 |  | 10,094 | 1,292 | 0.0 | 0.0331 | 0.0166 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p138 |  | 10,094 | 1,164 | 0.0 | 0.0318 | 0.0159 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p139 |  | 10,094 | 1,660 | 0.0 | 0.0368 | 0.0184 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p140 |  | 10,094 | 1,107 | 0.0 | 0.0313 | 0.0156 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p142 |  | 10,094 | 2,844 | 0.0 | 0.0486 | 0.0243 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p143 |  | 10,094 | 1,079 | 0.0 | 0.0310 | 0.0155 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p145 |  | 10,094 | 1,591 | 0.0 | 0.0361 | 0.0180 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p146 |  | 10,094 | 2,430 | 0.0 | 0.0445 | 0.0222 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p147 |  | 10,094 | 1,625 | 0.0 | 0.0364 | 0.0182 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p148 |  | 10,094 | 1,172 | 0.0 | 0.0319 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p149 |  | 10,094 | 1,849 | 0.0 | 0.0387 | 0.0193 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p150 |  | 10,094 | 908 | 0.0 | 0.0293 | 0.0146 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p151 |  | 10,094 | 1,203 | 0.0 | 0.0322 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p152 |  | 10,094 | 1,820 | 0.0 | 0.0384 | 0.0192 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p153 |  | 10,094 | 900 | 0.0 | 0.0292 | 0.0146 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p154 |  | 10,094 | 1,183 | 0.0 | 0.0320 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p155 |  | 10,094 | 1,628 | 0.0 | 0.0365 | 0.0182 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p156 |  | 10,094 | 1,586 | 0.0 | 0.0360 | 0.0180 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p157 |  | 10,094 | 1,193 | 0.0 | 0.0321 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotaku_r0604 p158 |  | 10,094 | 1,483 | 0.0 | 0.0350 | 0.0175 | end_turn |

## モデル別 合計・1ページ平均

| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| claude-haiku-5-5 | 86 | 868,084 | 325,752 | 0.2497 | 0.1248 | 10,094 | 3,788 | 0.0029 | 0.0015 |
| claude-sonnet-5-5 | 86 | 868,084 | 156,385 | 3.3000 | 1.6500 | 10,094 | 1,818 | 0.0384 | 0.0192 |

**この検証の合計（通常 API）: $3.5497**

## 全ページ処理した場合の見積もり

検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。

| 範囲 | ページ数 | claude-haiku-5-5 通常$ | claude-haiku-5-5 Batch$ | claude-sonnet-5-5 通常$ | claude-sonnet-5-5 Batch$ |
|---|--:|--:|--:|--:|--:|
| 事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編） | 941 | 2.73 | 1.37 | 36.10 | 18.05 |
| 介護 manifest の spec 全部 | 2,533 | 7.35 | 3.68 | 97.19 | 48.59 |
| 障害 manifest の spec 全部 | 1,680 | 4.88 | 2.44 | 64.46 | 32.23 |
| 両分野 spec 全部 | 4,213 | 12.23 | 6.11 | 161.64 | 80.82 |

対象ページ数の内訳: kaigo_kyotsu_r0806=100, kaigo_jigyosho_r0604=237, kaigo_kyotaku_r0604=201, shogai_kyotsu_r0710=63, shogai_jigyosho_r0710=340
