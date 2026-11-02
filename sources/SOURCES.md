# 出典一覧

`src/list_sources.py` が `sources/manifest.yaml`・`sources/rules_manifest.yaml` から作る（手で直さない）。
最新と判断した根拠は `sources/README.md`・`sources/rules_survey.md`。取得日時と sha256 は `fetch_log*.json`。

公開元: WAM NET、こども家庭庁、厚生労働省（WAM NET は独立行政法人福祉医療機構のサイトで、厚生労働省の事務連絡と添付資料を載せている）

どれも公開されている一次資料で、原本の PDF・Excel はリポジトリに含めない（`src/fetch.py` で取得する）。書き起こしの著作権・利用条件は各原本の公開元に従う。

## インタフェース仕様書・事務連絡（34 件）

### 介護保険（22 件）

**掲載ページ: <https://www.wam.go.jp/gyoseiShiryou/detail?gno=22560&ct=020050010>（WAM NET）**

- [介護保険事務処理システム変更に係る参考資料の送付について（確定版）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0522172637639/20260525_000.pdf)（令和8年6月施行分（令和8年度介護報酬改定） 確定版） — 取り込み: なし
- [国保連合会とのインタフェースの変更点について](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520082230677/20260522_010.pdf)（令和8年6月施行分（令和8年度介護報酬改定） 確定版） — 取り込み: なし
- [インタフェース仕様書 共通編](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430162031689/20260428_005.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 共通編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430162021934/20260428_004.pdf)（令和8年6月版 確定版（R8.5.25事務連絡）） — 取り込み: なし
- [インタフェース仕様書 都道府県編](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430162052610/20260428_007.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 都道府県編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430162039804/20260428_006.pdf)（令和8年6月版 確定版（R8.5.25事務連絡）） — 取り込み: なし
- [インタフェース仕様書 保険者編（分冊1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0428141109965/20260428_009.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 保険者編（分冊2）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0428141145989/20260428_010.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 保険者編（分冊3）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430185902189/20260428_011.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 保険者編（分冊4）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430185916734/20260428_012.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 保険者編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/043016211227/20260428_008.pdf)（令和8年6月版 確定版（R8.5.25事務連絡）） — 取り込み: なし
- [インタフェース仕様書 サービス事業所編](https://www.wam.go.jp/gyoseiShiryou-files/documents/2024/032720224810/20240329_323.pdf)（令和6年4月版 確定版（R6.3.28事務連絡）。R8.5.25確定版でも「変更なし」として同一ファイルを再掲）
- [インタフェース仕様書 居宅介護支援事業所編](https://www.wam.go.jp/gyoseiShiryou-files/documents/2024/0327202302106/20240329_325.pdf)（令和6年4月版 確定版（R6.3.28事務連絡）。R8.5.25確定版でも「変更なし」として同一ファイルを再掲）
- [市町村合併等に係る保険者インタフェース](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/042814145979/20260428_018.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 市町村合併IF編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0430162137474/20260428_017.pdf)（令和8年6月版 確定版（R8.5.25事務連絡）） — 取り込み: なし
- [インタフェース仕様書 生活保護単独受給者にかかる追加インタフェース](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0428141532100/20260428_020.pdf)（令和8年6月版 確定版（R8.5.25事務連絡））
- [インタフェース仕様書 生保単独IF編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0428141511729/20260428_019.pdf)（令和8年6月版 確定版（R8.5.25事務連絡）） — 取り込み: なし
- [伝送システム仕様書 インターネット編](https://www.wam.go.jp/gyoseiShiryou-files/documents/2022/0808123002643/202208_028.pdf)（令和4年10月版 R8.5.25確定版で「変更なし」として再掲）

**掲載ページ: <https://www.wam.go.jp/gyoseiShiryou/detail?gno=20501&ct=020050010>（WAM NET）**

- [インタフェース仕様書 サービス事業所編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2024/0327202239896/20240329_322.pdf)（令和6年4月版 確定版（R6.3.28事務連絡）） — 取り込み: なし
- [インタフェース仕様書 居宅介護支援事業所編 新旧対照表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2024/0327202255302/20240329_324.pdf)（令和6年4月版 確定版（R6.3.28事務連絡）） — 取り込み: なし

**掲載ページ: <https://www.wam.go.jp/gyoseiShiryou/detail?gno=22911&ct=020050010>（WAM NET）**

- [介護保険事務処理システム変更に係る参考資料の送付について（その１）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/1006155538844/20261002_000.pdf)（令和9年4月施行分（令和9年度介護保険制度改正・報酬改定） その１（案段階）） — 取り込み: なし
- [国保連合会とのインタフェースの変更点について（2027年5月以降出力分）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/1002092721384/20261002_005.pdf)（令和9年4月施行分（令和9年度介護保険制度改正・報酬改定） その１（案段階）） — 取り込み: なし

### 障害福祉（障害児を含む）（12 件）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174643_00025.html>（厚生労働省）**

- [障害福祉サービス等報酬改定に係るインタフェース仕様書【確定版】等の提示について](https://www.mhlw.go.jp/content/12200000/001696456.pdf)（令和8年6月施行分 確定版） — 取り込み: なし
- [障害福祉サービス等報酬改定に係るインタフェース仕様書（案）等の提示について](https://www.mhlw.go.jp/content/12200000/001663320.pdf)（令和8年6月施行分 案） — 取り込み: なし
- [インタフェース仕様書 都道府県編](https://www.mhlw.go.jp/content/12200000/001663321.pdf)（令和8年6月施行分 確定版（R8.4.28事務連絡。R8.2.27案から見直しなし））
- [インタフェース仕様書 都道府県編 修正履歴](https://www.mhlw.go.jp/content/12200000/001663322.pdf)（令和8年6月施行分 確定版（内容現在 令和8年4月28日）） — 取り込み: なし

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174643_00020.html>（厚生労働省）**

- [就労選択支援の施行に係るインタフェース仕様書【確定版】等の提示について](https://www.mhlw.go.jp/content/12200000/001565557.pdf)（令和7年10月施行分 確定版（9月修正）） — 取り込み: なし
- [就労選択支援の施行に係るインタフェース仕様書（案）等の提示について](https://www.mhlw.go.jp/content/12200000/001565559.pdf)（令和7年10月施行分 案（抜粋版）） — 取り込み: なし
- [インタフェース仕様書 共通編](https://www.mhlw.go.jp/content/12200000/001565560.pdf)（令和7年10月施行分 確定版（R7.9.19事務連絡））
- [インタフェース仕様書 共通編 修正履歴](https://www.mhlw.go.jp/content/12200000/001565579.pdf)（令和7年10月施行分 9月修正履歴（内容現在 令和7年9月19日）） — 取り込み: なし
- [インタフェース仕様書 市町村編](https://www.mhlw.go.jp/content/12200000/001565562.pdf)（令和7年10月施行分 確定版（R7.9.19事務連絡。R7.6.2案から18-19ページ等を修正））
- [インタフェース仕様書 市町村編 修正履歴](https://www.mhlw.go.jp/content/12200000/001565984.pdf)（令和7年10月施行分 9月修正履歴（内容現在 令和7年9月19日）） — 取り込み: なし
- [インタフェース仕様書 サービス事業所編](https://www.mhlw.go.jp/content/12200000/001565561.pdf)（令和7年10月施行分 確定版（R7.9.19事務連絡））
- [インタフェース仕様書 サービス事業所編 修正履歴](https://www.mhlw.go.jp/content/12200000/001565581.pdf)（令和7年10月施行分 9月修正履歴（内容現在 令和7年9月19日）） — 取り込み: なし

## 算定ルール資料（95 件）

### 介護保険（60 件）

**掲載ページ: <https://www.mhlw.go.jp/hourei/>（厚生労働省）**

- [指定居宅サービスに要する費用の額の算定に関する基準（平成12年厚生省告示第19号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa0253&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定居宅介護支援に要する費用の額の算定に関する基準（平成12年厚生省告示第20号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa0254&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定施設サービス等に要する費用の額の算定に関する基準（平成12年厚生省告示第21号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa0255&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定地域密着型サービスに要する費用の額の算定に関する基準（平成18年厚生労働省告示第126号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa7862&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定介護予防サービスに要する費用の額の算定に関する基準（平成18年厚生労働省告示第127号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa7863&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定地域密着型介護予防サービスに要する費用の額の算定に関する基準（平成18年厚生労働省告示第128号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa7864&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [指定介護予防支援に要する費用の額の算定に関する基準（平成18年厚生労働省告示第129号）](https://www.mhlw.go.jp/web/t_doc?dataId=82aa7865&dataType=0&pageNo=1)（法令等データベース 溶け込み版）
- [介護保険法施行規則第百四十条の六十三の二第一項第一号に規定する厚生労働大臣が定める基準（令和3年厚生労働省告示第72号。総合事業・介護予防ケアマネジメントの単位数）](https://www.mhlw.go.jp/web/t_doc?dataId=82ab8054&dataType=0&pageNo=1)（法令等データベース 溶け込み版）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000188411_00073.html>（厚生労働省）**

- [指定居宅サービスに要する費用の額の算定に関する基準等の一部を改正する告示（令和8年厚生労働省告示第87号）](https://www.mhlw.go.jp/content/12404000/001675895.pdf)（R8.3.13 公布）
- [老企第36号 新旧対照表](https://www.mhlw.go.jp/content/12404000/001682729.pdf)（R8.3.13 改正）
- [指定介護予防サービスに要する費用の額の算定に関する基準の制定に伴う実施上の留意事項について（新旧）](https://www.mhlw.go.jp/content/12404000/001675938.pdf)（R8.3.13 改正）
- [留意事項通知（老企第36号ほか）等の一部改正 新旧対照表 及び 当該通知の発出に伴うQ&A（介護保険最新情報 Vol.1502）](https://www.mhlw.go.jp/content/001698614.pdf)（R8.5.8 改正）
- [介護予防・日常生活支援総合事業の留意事項 新旧対照表](https://www.mhlw.go.jp/content/001673837.pdf)（R8.3.13 改正）
- [令和8年度介護職員等処遇改善加算に関するQ&A（第1版）](https://www.mhlw.go.jp/content/12404000/001675711.pdf)（R8）

**掲載ページ: <https://www.mhlw.go.jp/stf/newpage_38790.html>（厚生労働省）**

- [老企第36号（訪問通所サービス・居宅療養管理指導・福祉用具貸与・居宅介護支援の留意事項）新旧対照表（抄）](https://www.mhlw.go.jp/content/12300000/001227887.pdf)（R6.3.15 改正）
- [老企第36号 新旧対照表](https://www.mhlw.go.jp/content/12300000/001247345.pdf)（R6.4.18 改正）
- [老企第40号（短期入所・特定施設・施設サービスの留意事項）新旧対照表](https://www.mhlw.go.jp/content/12300000/001227894.pdf)（R6.3.15 改正）
- [老計発第0317001号等（介護予防サービスの留意事項）新旧対照表](https://www.mhlw.go.jp/content/12300000/001227907.pdf)（R6.3.15 改正）
- [老計発第0317001号等 新旧対照表](https://www.mhlw.go.jp/content/12300000/001247346.pdf)（R6.4.18 改正）
- [老計発第0331005号等（地域密着型サービスの留意事項）新旧対照表](https://www.mhlw.go.jp/content/12300000/001227915.pdf)（R6.3.15 改正）
- [老計発第0331005号等 新旧対照表](https://www.mhlw.go.jp/content/12300000/001247347.pdf)（R6.4.18 改正）
- [介護予防・日常生活支援総合事業の留意事項（老認発0319第3号）](https://www.mhlw.go.jp/content/12300000/000947634.pdf)（改正前（全文））
- [令和6年度介護報酬改定に関するQ&A（Vol.1）](https://www.mhlw.go.jp/content/12300000/001230308.pdf)（R6.3.15）
- [令和6年度介護報酬改定に関するQ&A（Vol.2）](https://www.mhlw.go.jp/content/12300000/001239535.pdf)（R6.3.19）
- [令和6年度介護報酬改定に関するQ&A（Vol.3）](https://www.mhlw.go.jp/content/12300000/001239536.pdf)（R6.3.29）
- [令和6年度介護報酬改定に関するQ&A（Vol.4）](https://www.mhlw.go.jp/content/12300000/001247348.pdf)（R6.4.18）
- [令和6年度介護報酬改定に関するQ&A（Vol.5）](https://www.mhlw.go.jp/content/12300000/001250798.pdf)（R6.4.30）
- [令和6年度介護報酬改定に関するQ&A（Vol.6）](https://www.mhlw.go.jp/content/12300000/001255640.pdf)（R6.5.17）
- [令和6年度介護報酬改定に関するQ&A（Vol.7）](https://www.mhlw.go.jp/content/12300000/001261868.pdf)（R6.6.7）
- [令和6年度介護報酬改定に関するQ&A（Vol.8）](https://www.mhlw.go.jp/content/12300000/001309722.pdf)（R6.7.9）
- [令和6年度介護報酬改定に関するQ&A（Vol.9）](https://www.mhlw.go.jp/content/12300000/001309723.pdf)（R6.8.29）
- [令和6年度介護報酬改定に関するQ&A（Vol.10）](https://www.mhlw.go.jp/content/12300000/001309718.pdf)（R6.9.27）
- [令和6年度介護報酬改定に関するQ&A（Vol.11）](https://www.mhlw.go.jp/content/12300000/001404862.pdf)（R6.11.11）
- [令和6年度介護報酬改定に関するQ&A（Vol.12）](https://www.mhlw.go.jp/content/12300000/001381691.pdf)（R7.1.22）
- [令和6年度介護報酬改定に関するQ&A（Vol.13）](https://www.mhlw.go.jp/content/12300000/001473357.pdf)（R7.4.7）
- [令和6年度介護報酬改定に関するQ&A（Vol.14）](https://www.mhlw.go.jp/content/12300000/001478559.pdf)（R7.4.18）
- [令和6年度介護報酬改定に関するQ&A（Vol.15）](https://www.mhlw.go.jp/content/12300000/001552756.pdf)（R7.7.9）
- [令和6年度介護報酬改定に関するQ&A（Vol.16）](https://www.mhlw.go.jp/content/12300000/001557055.pdf)（R7.9.5）
- [令和6年度介護報酬改定に関するQ&A（Vol.17）](https://www.mhlw.go.jp/content/12300000/001572619.pdf)（R7.10.1）
- [令和6年度介護報酬改定に関するQ&A（Vol.18）](https://www.mhlw.go.jp/content/12300000/001723857.pdf)（R8.7.14）
- [介護職員等処遇改善加算等に関するQ&A（第3版）](https://www.mhlw.go.jp/content/12300000/001266718.pdf)（R6.6.20）

**掲載ページ: <https://www.wam.go.jp/gyoseiShiryou/detail?gno=22560&ct=020050010>（WAM NET）**

- [介護給付費請求書等の記載要領について（平成13年11月16日老老発第31号）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0414230733572/20260416_014.pdf)（R8.6 施行分 確定版（R8.5.25 事務連絡））
- [介護給付費請求書等の記載要領について 別表](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/041423074279/20260416_015.pdf)（R8.6 施行分 確定版（R8.5.25 事務連絡））
- [介護給付費請求書・明細書及び給付管理票記載例](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0420143053543/20260416_024.pdf)（R8.6 施行分 確定版（R8.5.25 事務連絡））
- [介護給付費単位数等サービスコード表 介護サービス（R8.6.1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/052008190186/20260522_003.pdf)（R8.6 施行分 確定版）
- [介護給付費単位数等サービスコード表 介護サービス（R8.6.1）エクセル版](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0521184041930/20260522_013.zip)（R8.6 施行分 確定版）
- [介護給付費単位数等サービスコード表 介護予防サービス（R8.6.1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520081914484/20260522_004.pdf)（R8.6 施行分 確定版）
- [介護給付費単位数等サービスコード表 介護予防サービス（R8.6.1）エクセル版](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0521184051104/20260522_014.zip)（R8.6 施行分 確定版）
- [介護給付費単位数等サービスコード表 地域密着型サービス（R8.6.1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520081927889/20260522_005.pdf)（R8.6 施行分 確定版）
- [介護給付費単位数等サービスコード表 地域密着型サービス（R8.6.1）エクセル版](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/052118405922/20260522_015.zip)（R8.6 施行分 確定版）
- [介護予防・日常生活支援総合事業サービスコード表（R8.6.1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520082055424/20260522_007.pdf)（R8.6 施行分 確定版）
- [介護予防・日常生活支援総合事業サービスコード表（R8.6.1）エクセル版](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0521184108165/20260522_016.zip)（R8.6 施行分 確定版）
- [介護報酬の算定構造のイメージ（R8.6.1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520081831222/20260522_001.pdf)（R8.6 施行分 確定版）
- [令和6年4月以降の介護予防・日常生活支援総合事業におけるサービス種類の考え方](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0522171821794/20260522_017.pdf)（R8.6 施行分 確定版）
- [介護予防・日常生活支援総合事業における請求明細書と給付管理票の提出パターン](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0522171834175/20260522_018.pdf)（R8.6 施行分 確定版）
- [介護予防・日常生活支援総合事業費請求書・明細書及び給付管理票記載例](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/0520082144743/20260522_008.pdf)（R8.6 施行分 確定版）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index_00010.html>（厚生労働省）**

- [「「指定居宅サービスに要する費用の額の算定に関する基準…の留意事項について」等の一部改正について」の発出等に伴うQ&A（Vol.2）（介護保険最新情報 Vol.1523）](https://www.mhlw.go.jp/content/001722713.pdf)（R8.7.13）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000184585.html>（厚生労働省）**

- [介護予防・日常生活支援総合事業のガイドラインについて（老発0605第5号、最終改正 老発0820第2号）](https://www.mhlw.go.jp/content/12300000/001741382.pdf)（R8.8.20）
- [地域支援事業の実施について（老発第0609001号、最終改正 老発0820第1号）](https://www.mhlw.go.jp/content/12300000/001741386.pdf)（R8.8.20）

**掲載ページ: <https://www.wam.go.jp/gyoseiShiryou/detail?gno=22911&ct=020050010>（WAM NET）**

- [介護保険事務処理システム変更に係る参考資料（R9 総合事業のサービス種類の変更 その1）](https://www.wam.go.jp/gyoseiShiryou-files/documents/2026/1006155538844/20261002_000.pdf)（R8.10.6 事務連絡） — 取り込み: なし

### 障害福祉（障害児を含む）（35 件）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000202214_00009.html>（厚生労働省）**

- [障害福祉サービス等の算定基準等の一部を改正する告示（令和6年こども家庭庁・厚生労働省告示第3号）](https://www.mhlw.go.jp/content/001239565.pdf)（R6）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.1](https://www.mhlw.go.jp/content/001260473.pdf)（R6.3.29）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.2](https://www.mhlw.go.jp/content/001250243.pdf)（R6.4.5）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.3](https://www.mhlw.go.jp/content/001253308.pdf)（R6.5.10）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.4](https://www.mhlw.go.jp/content/001260438.pdf)（R6.6.4）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.5](https://www.mhlw.go.jp/content/001297221.pdf)（R6.8.29）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.6](https://www.mhlw.go.jp/content/001316215.pdf)（R6.10.11）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.7](https://www.mhlw.go.jp/content/001385141.pdf)（R7.1.24）
- [令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.8](https://www.mhlw.go.jp/content/001471548.pdf)（R7.3.31）
- [「令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.1」の正誤について](https://www.mhlw.go.jp/content/001241668.pdf)（R6）
- [「令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.1」の正誤（その2）及び VOL.2 の正誤](https://www.mhlw.go.jp/content/001250239.pdf)（R6）
- [「令和6年度障害福祉サービス等報酬改定等に関するQ&A VOL.1」の正誤（その3）について](https://www.mhlw.go.jp/content/001260428.pdf)（R6）

**掲載ページ: 未特定（PDF の URL だけ確認）**

- [障害福祉サービス等の算定基準等の一部を改正する告示（令和7年こども家庭庁・厚生労働省告示第2号）](https://www.mhlw.go.jp/content/12200000/001471228.pdf)（R7）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000202214_00013.html>（厚生労働省）**

- [指定障害福祉サービス等及び基準該当障害福祉サービスに要する費用の額の算定に関する基準等の一部を改正する告示（令和8年）](https://www.mhlw.go.jp/content/001684450.pdf)（R8.3.31）
- [指定地域相談支援に要する費用の額の算定に関する基準等の一部を改正する告示（令和8年）](https://www.mhlw.go.jp/content/001684361.pdf)（R8.3.31）
- [障発第1031001号（指定障害福祉サービス等の算定基準の留意事項）新旧対照表（全文2段）](https://www.mhlw.go.jp/content/001705650.pdf)（R8.5.28 改正）
- [「「指定障害福祉サービス等…の留意事項について」の一部改正について」等の発出に伴うQ&A（令和8年5月28日）](https://www.mhlw.go.jp/content/001705652.pdf)（R8.5.28）
- [令和8年度障害福祉サービス等報酬改定等に関するQ&A VOL.1](https://www.mhlw.go.jp/content/001683290.pdf)（R8.3.31）
- [令和8年度障害福祉サービス等報酬改定等に関するQ&A VOL.2](https://www.mhlw.go.jp/content/001722503.pdf)（R8.7.13）

**掲載ページ: <https://www.cfa.go.jp/policies/shougaijishien/shisaku/r8hoshukaitei>（こども家庭庁）**

- [【官報】児童福祉法に基づく指定通所支援及び基準該当通所支援に要する費用の額の算定に関する基準等の一部を改正する告示（令和8年こども家庭庁告示第5号）](https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/2c5e1bb4-ee80-462b-992f-06f0d8c9b774/255d371a/20260402_policies_shougaijishien_shisaku_r8hoshukaitei_15.pdf)（R8.3.31）
- [児童福祉法に基づく指定通所支援等の算定基準の留意事項（障発0330第16号）改正後全文](https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/2c5e1bb4-ee80-462b-992f-06f0d8c9b774/4aacbf83/20260402_policies_shougaijishien_shisaku_r8hoshukaitei_17.pdf)（R8.4 時点）
- [児童福祉法に基づく指定通所支援等の算定基準の留意事項 新旧対照表](https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/2c5e1bb4-ee80-462b-992f-06f0d8c9b774/65f8ab1f/20260528_policies_shougaijishien_shisaku_r8hoshukaitei_28.pdf)（R8.5.28 改正）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174644_00021.html>（厚生労働省）**

- [請求書明細書（記載例）](https://www.mhlw.go.jp/content/12200000/001565602.pdf)（令和7年10月施行分（R8.6 は変更なし））
- [実績記録票（記載例）](https://www.mhlw.go.jp/content/12200000/001565588.pdf)（令和7年10月施行分（R8.6 は変更なし））

**掲載ページ: <https://www.cfa.go.jp/policies/shougaijishien/shisaku/hoshukaitei>（こども家庭庁）**

- [障害福祉サービス等報酬改定（障害児支援）に関するQ&A](https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/253aba4f-3ce0-4aa1-a777-3d42440f1ca2/87a60237/20240517_policies_shougaijishien_shisaku_hoshukaitei_98.pdf)（R6.5.17）

**掲載ページ: <https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174644_00022.html>（厚生労働省）**

- [介護給付費等単位数サービスコード（令和8年6月施行分）その1 居宅介護〜（訪問系・日中活動系など）](https://www.mhlw.go.jp/content/12200000/001696433.pdf)（R8.6 施行分）
- [介護給付費等単位数サービスコード（令和8年6月施行分）その2 短期入所〜](https://www.mhlw.go.jp/content/12200000/001696434.pdf)（R8.6 施行分）
- [介護給付費等単位数サービスコード（令和8年6月施行分）その3 障害児（児童発達支援〜）](https://www.mhlw.go.jp/content/12200000/001696435.pdf)（R8.6 施行分）
- [介護給付費等単位数サービスコード（令和8年6月施行分）その1 Excel](https://www.mhlw.go.jp/content/12200000/001696436.xlsx)（R8.6 施行分）
- [介護給付費等単位数サービスコード（令和8年6月施行分）その2 Excel](https://www.mhlw.go.jp/content/12200000/001696437.xlsx)（R8.6 施行分）
- [介護給付費等単位数サービスコード（令和8年6月施行分）その3 Excel](https://www.mhlw.go.jp/content/12200000/001696438.xlsx)（R8.6 施行分）
- [障害福祉サービス費等の報酬算定構造（令和8年6月）](https://www.mhlw.go.jp/content/12200000/001663319.pdf)（R8.6 施行分）
- [請求サービスコードと決定サービスコード対応表（令和8年6月）](https://www.mhlw.go.jp/content/12200000/001696448.pdf)（R8.6 施行分）
- [請求サービスコードと決定サービスコード対応表（令和8年6月）Excel その1](https://www.mhlw.go.jp/content/12200000/001696450.xls)（R8.6 施行分）
- [請求サービスコードと決定サービスコード対応表（令和8年6月）Excel その2](https://www.mhlw.go.jp/content/12200000/001696451.xls)（R8.6 施行分）
