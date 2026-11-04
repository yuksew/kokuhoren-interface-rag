# 書き起こしコスト（run: prod6-png-post）

単価（USD / 100万トークン）: claude-haiku-5-5 入力$0.1 出力$0.5, claude-sonnet-5-5 入力$2.0 出力$10.0。Batch API は 50% 引き。

## 呼び出しごと

| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |
|---|---|---|--:|--:|--:|--:|--:|---|
| claude-haiku-5-5 | kaigo_internet_r0410 p6 |  | 10,089 | 3,345 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p10 |  | 10,089 | 4,668 | 0.0 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p13 |  | 10,089 | 3,432 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p14 |  | 10,089 | 2,361 | 0.0 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p15 |  | 10,089 | 4,299 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p16 |  | 10,089 | 3,499 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p17 |  | 10,089 | 3,034 | 0.0 | 0.0025 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p18 |  | 10,089 | 3,305 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p19 |  | 10,089 | 3,683 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p20 |  | 10,089 | 3,477 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p21 |  | 10,089 | 3,987 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p24 |  | 10,089 | 3,835 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p25 |  | 10,089 | 3,139 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p26 |  | 10,089 | 4,413 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p27 |  | 10,089 | 4,527 | 0.0 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p28 |  | 10,089 | 4,200 | 0.0 | 0.0031 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p30 |  | 10,089 | 5,493 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p32 |  | 10,089 | 4,188 | 0.0 | 0.0031 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p33 |  | 10,089 | 3,524 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p34 |  | 10,089 | 4,350 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p35 |  | 10,089 | 6,588 | 0.0 | 0.0043 | 0.0022 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p36 |  | 10,089 | 4,638 | 0.0 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p37 |  | 10,089 | 4,654 | 0.0 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p38 |  | 10,089 | 5,523 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p39 |  | 10,089 | 5,119 | 0.0 | 0.0036 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p40 |  | 10,089 | 3,672 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p41 |  | 10,089 | 3,299 | 0.0 | 0.0027 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p42 |  | 10,089 | 5,328 | 0.0 | 0.0037 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p43 |  | 10,089 | 2,393 | 0.0 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p44 |  | 10,089 | 4,018 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p45 |  | 10,089 | 4,760 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p46 |  | 10,089 | 3,474 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p49 |  | 10,089 | 5,673 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p50 |  | 10,089 | 4,572 | 0.0 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p51 |  | 10,089 | 3,945 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p52 |  | 10,089 | 5,177 | 0.0 | 0.0036 | 0.0018 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p53 |  | 10,089 | 4,090 | 0.0 | 0.0031 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p54 |  | 10,089 | 3,956 | 0.0 | 0.0030 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p55 |  | 10,089 | 3,774 | 0.0 | 0.0029 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p56 |  | 10,089 | 4,375 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p57 |  | 10,089 | 3,479 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p58 |  | 10,089 | 4,644 | 0.0 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p59 |  | 10,089 | 3,556 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p60 |  | 10,089 | 5,627 | 0.0 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p61 |  | 10,089 | 4,446 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p62 |  | 10,089 | 4,390 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p63 |  | 10,089 | 4,135 | 0.0 | 0.0031 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p64 |  | 10,089 | 2,039 | 0.0 | 0.0020 | 0.0010 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p65 |  | 10,089 | 4,864 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p66 |  | 10,089 | 3,856 | 0.0 | 0.0029 | 0.0015 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p67 |  | 10,089 | 4,332 | 0.0 | 0.0032 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p68 |  | 10,089 | 2,724 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p69 |  | 10,089 | 3,594 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p70 |  | 10,089 | 3,557 | 0.0 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p71 |  | 10,089 | 3,227 | 0.0 | 0.0026 | 0.0013 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p72 |  | 10,089 | 2,720 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p73 |  | 10,089 | 2,930 | 0.0 | 0.0025 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p74 |  | 10,089 | 1,218 | 0.0 | 0.0016 | 0.0008 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p76 |  | 10,089 | 2,714 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p77 |  | 10,089 | 4,711 | 0.0 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p78 |  | 10,089 | 4,545 | 0.0 | 0.0033 | 0.0016 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p79 |  | 10,089 | 3,403 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p81 |  | 10,089 | 2,747 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p83 |  | 10,089 | 2,727 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p84 |  | 10,089 | 1,510 | 0.0 | 0.0018 | 0.0009 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p85 |  | 10,089 | 2,831 | 0.0 | 0.0024 | 0.0012 | end_turn |
| claude-haiku-5-5 | kaigo_internet_r0410 p86 |  | 10,089 | 3,419 | 0.0 | 0.0027 | 0.0014 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p6 |  | 10,089 | 1,795 | 0.0 | 0.0381 | 0.0191 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p10 |  | 10,089 | 1,702 | 0.0 | 0.0372 | 0.0186 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p13 |  | 10,089 | 1,146 | 0.0 | 0.0316 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p14 |  | 10,089 | 782 | 0.0 | 0.0280 | 0.0140 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p15 |  | 10,089 | 1,638 | 0.0 | 0.0366 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p16 |  | 10,089 | 1,125 | 0.0 | 0.0314 | 0.0157 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p17 |  | 10,089 | 1,263 | 0.0 | 0.0328 | 0.0164 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p18 |  | 10,089 | 1,347 | 0.0 | 0.0336 | 0.0168 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p19 |  | 10,089 | 1,587 | 0.0 | 0.0360 | 0.0180 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p20 |  | 10,089 | 1,401 | 0.0 | 0.0342 | 0.0171 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p21 |  | 10,089 | 1,209 | 0.0 | 0.0323 | 0.0161 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p24 |  | 10,089 | 1,447 | 0.0 | 0.0346 | 0.0173 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p25 |  | 10,089 | 1,144 | 0.0 | 0.0316 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p26 |  | 10,089 | 2,045 | 0.0 | 0.0406 | 0.0203 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p27 |  | 10,089 | 2,191 | 0.0 | 0.0421 | 0.0210 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p28 |  | 10,089 | 1,835 | 0.0 | 0.0385 | 0.0193 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p30 |  | 10,089 | 1,695 | 0.0 | 0.0371 | 0.0186 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p32 |  | 10,089 | 1,727 | 0.0 | 0.0374 | 0.0187 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p33 |  | 10,089 | 853 | 0.0 | 0.0287 | 0.0144 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p34 |  | 10,089 | 1,173 | 0.0 | 0.0319 | 0.0160 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p35 |  | 10,089 | 2,342 | 0.0 | 0.0436 | 0.0218 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p36 |  | 10,089 | 1,646 | 0.0 | 0.0366 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p37 |  | 10,089 | 1,564 | 0.0 | 0.0358 | 0.0179 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p38 |  | 10,089 | 1,546 | 0.0 | 0.0356 | 0.0178 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p39 |  | 10,089 | 2,118 | 0.0 | 0.0414 | 0.0207 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p40 |  | 10,089 | 1,748 | 0.0 | 0.0377 | 0.0188 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p41 |  | 10,089 | 1,368 | 0.0 | 0.0339 | 0.0169 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p42 |  | 10,089 | 1,515 | 0.0 | 0.0353 | 0.0177 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p43 |  | 10,089 | 692 | 0.0 | 0.0271 | 0.0135 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p44 |  | 10,089 | 1,636 | 0.0 | 0.0365 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p45 |  | 10,089 | 1,658 | 0.0 | 0.0368 | 0.0184 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p46 |  | 10,089 | 1,156 | 0.0 | 0.0317 | 0.0159 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p49 |  | 10,089 | 1,716 | 0.0 | 0.0373 | 0.0187 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p50 |  | 10,089 | 1,849 | 0.0 | 0.0387 | 0.0193 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p51 |  | 10,089 | 1,846 | 0.0 | 0.0386 | 0.0193 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p52 |  | 10,089 | 2,542 | 0.0 | 0.0456 | 0.0228 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p53 |  | 10,089 | 2,089 | 0.0 | 0.0411 | 0.0205 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p54 |  | 10,089 | 1,614 | 0.0 | 0.0363 | 0.0182 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p55 |  | 10,089 | 1,649 | 0.0 | 0.0367 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p56 |  | 10,089 | 1,999 | 0.0 | 0.0402 | 0.0201 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p57 |  | 10,089 | 1,775 | 0.0 | 0.0379 | 0.0190 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p58 |  | 10,089 | 1,784 | 0.0 | 0.0380 | 0.0190 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p59 |  | 10,089 | 1,291 | 0.0 | 0.0331 | 0.0165 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p60 |  | 10,089 | 2,853 | 0.0 | 0.0487 | 0.0244 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p61 |  | 10,089 | 2,240 | 0.0 | 0.0426 | 0.0213 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p62 |  | 10,089 | 2,468 | 0.0 | 0.0449 | 0.0224 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p63 |  | 10,089 | 2,527 | 0.0 | 0.0454 | 0.0227 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p64 |  | 10,089 | 704 | 0.0 | 0.0272 | 0.0136 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p65 |  | 10,089 | 2,267 | 0.0 | 0.0428 | 0.0214 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p66 |  | 10,089 | 1,706 | 0.0 | 0.0372 | 0.0186 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p67 |  | 10,089 | 1,502 | 0.0 | 0.0352 | 0.0176 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p68 |  | 10,089 | 1,259 | 0.0 | 0.0328 | 0.0164 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p69 |  | 10,089 | 1,554 | 0.0 | 0.0357 | 0.0179 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p70 |  | 10,089 | 1,655 | 0.0 | 0.0367 | 0.0184 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p71 |  | 10,089 | 1,425 | 0.0 | 0.0344 | 0.0172 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p72 |  | 10,089 | 1,134 | 0.0 | 0.0315 | 0.0158 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p73 |  | 10,089 | 1,646 | 0.0 | 0.0366 | 0.0183 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p74 |  | 10,089 | 468 | 0.0 | 0.0249 | 0.0124 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p76 |  | 10,089 | 1,281 | 0.0 | 0.0330 | 0.0165 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p77 |  | 10,089 | 2,953 | 0.0 | 0.0497 | 0.0249 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p78 |  | 10,089 | 3,075 | 0.0 | 0.0509 | 0.0255 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p79 |  | 10,089 | 1,893 | 0.0 | 0.0391 | 0.0196 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p81 |  | 10,089 | 1,777 | 0.0 | 0.0379 | 0.0190 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p83 |  | 10,089 | 1,460 | 0.0 | 0.0348 | 0.0174 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p84 |  | 10,089 | 385 | 0.0 | 0.0240 | 0.0120 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p85 |  | 10,089 | 847 | 0.0 | 0.0286 | 0.0143 | end_turn |
| claude-sonnet-5-5 | kaigo_internet_r0410 p86 |  | 10,089 | 1,580 | 0.0 | 0.0360 | 0.0180 | end_turn |

## モデル別 合計・1ページ平均

| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| claude-haiku-5-5 | 67 | 675,963 | 259,732 | 0.1975 | 0.0987 | 10,089 | 3,877 | 0.0029 | 0.0015 |
| claude-sonnet-5-5 | 67 | 675,963 | 108,907 | 2.4410 | 1.2205 | 10,089 | 1,625 | 0.0364 | 0.0182 |

**この検証の合計（通常 API）: $2.6384**

## 全ページ処理した場合の見積もり

検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。

| 範囲 | ページ数 | claude-haiku-5-5 通常$ | claude-haiku-5-5 Batch$ | claude-sonnet-5-5 通常$ | claude-sonnet-5-5 Batch$ |
|---|--:|--:|--:|--:|--:|
| 事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編） | 941 | 2.77 | 1.39 | 34.28 | 17.14 |
| 介護 manifest の spec 全部 | 2,533 | 7.46 | 3.73 | 92.27 | 46.14 |
| 障害 manifest の spec 全部 | 1,680 | 4.95 | 2.48 | 61.20 | 30.60 |
| 両分野 spec 全部 | 4,213 | 12.42 | 6.21 | 153.47 | 76.74 |

対象ページ数の内訳: kaigo_kyotsu_r0806=100, kaigo_jigyosho_r0604=237, kaigo_kyotaku_r0604=201, shogai_kyotsu_r0710=63, shogai_jigyosho_r0710=340
