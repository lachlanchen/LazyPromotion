---
title: "替 1,000 本多語書籍做 OCR 之前，先做一套小型測試集"
slug: "evaluate-multilingual-ocr-book-archive-before-rag"
status: "publish"
source_language: "en"
language: "zh"
author: "Lachlan Chen"
categories:
  - "電腦與網路"
  - "書籍"
tags:
  - "OCR"
  - "多語言"
  - "阿拉伯文"
  - "烏爾都文"
  - "本機 RAG"
excerpt: "比較大型多語書庫 OCR 的實用方法：抽取真正的頁面類型，分開量測文字與閱讀順序，保留原始頁面，再讓每一類頁面走實測效果最好的流程。"
---

等到一千本書全都跑完，才發現 OCR 看似通順，卻改錯人名、顛倒雙欄順序，或悄悄漏掉烏爾都文，代價會非常高。

所以別先問「哪個 OCR 引擎最好？」先做一套能代表手上書庫的小型測試集。最後的答案很可能不是單一引擎：乾淨英文頁走一條流程，阿拉伯文或 Nastaliq 字體走另一條，只有少數兩邊都讀不穩的頁面才送人工複核。

## 抽樣頁面類型，不只抽樣書名

正式處理整個書庫前，先選約 60 頁。數字不必迷信，重點是覆蓋真正存在的情況。第一版可以包括：

- 10 頁乾淨英文；
- 10 頁乾淨阿拉伯文；
- 10 頁烏爾都文或 Nastaliq；
- 10 頁左右向文字混排；
- 10 頁困難掃描：傾斜、透印、對比不足、頁邊筆記；
- 10 頁結構頁：雙欄、註腳、表格、詩歌或對照文本。

抽樣要跨出版社、年代、字體與掃描來源。另外保留一小套調參時完全不用的測試頁。否則很容易只把最初幾頁調得漂亮，卻誤以為整個書庫都改善了。

用簡單的 manifest 記錄樣本：

```csv
page_id,book_id,page_label,script,page_type,image_sha256,ground_truth
p001,b017,23,ara,single_column,8a4f...,truth/p001.txt
p002,b042,118,urd,nastaliq_footnotes,37c1...,truth/p002.txt
p003,b051,ix,mixed,mixed_rtl_ltr,2e90...,truth/p003.txt
```

頁面影像與雜湊值是固定基準。引擎、模型或語言包、版本、設定、耗時與輸出路徑則放進每次執行的紀錄。這樣結果才能重現，而不是只記得「上週 Paddle 好像比較好」。

## Ground truth 要小，但要可信

依照真正用途，準確轉寫每一張樣本頁。搜尋書庫通常需要正文、標題、人名、引文與有意義的標點；如果註腳重要，就一起轉寫；如果母音符號或其他附加符號會影響內容，也要保留。

轉寫檔使用 UTF-8。原樣轉寫（頁面印了什麼就保留什麼）不要改動。若比較時需要正規化，請另存衍生檔，並記下規則。[W3C 字串比對規範](https://www.w3.org/TR/charmod-norm/)建議用 Unicode 正規化提高比對一致性，但相容正規化可能合併你想保留的差異。NFC 可以作為合理的比較起點；刪除附加符號、把烏爾都文字形換成阿拉伯文字形，或合併標點，都應該是明確的實驗，不能是無聲的清理。

阿拉伯文／烏爾都文與英文混排的頁面要分兩件事檢查。第一，底層 Unicode 字元是否正確？第二，閱讀順序是否正確？一行文字即使字元全對，也可能因英文片語、頁碼或註腳插錯位置而無法使用。

## 文字錯誤與版面錯誤分開量測

字元錯誤率（CER）是很好用的第一個數字：

```text
CER =（替換 + 刪除 + 插入）/ 參考字元數
```

請依頁面類型與文字系統分開計算，不要只看總平均。大量容易的英文頁，會掩蓋烏爾都文幾乎不可用的情況。[JiWER](https://github.com/jitsi/jiwer) 等工具能計算字元與詞級錯誤，但正規化方式也是結果的一部分，必須和分數一起保存。

CER 不會量到閱讀順序。[OCR-D 評估規範](https://ocr-d.de/en/spec/ocrd_eval.html)會把文字、版面、閱讀順序與執行時間分成不同品質面向。每張測試頁再加一份簡短結構檢查：

- 標題是否在所屬段落之前；
- 欄位是否按正確順序排列；
- 註腳是否留在正確頁面並對到標記；
- 表格是否保留儲存格，或明確標記為不可靠；
- 左右向混排是否維持合理的邏輯順序；
- 頁面邊界是否保留。

若引擎能輸出版面資訊，就一起保存。Tesseract 除純文字外，也能輸出 hOCR 或 TSV。[ALTO](https://www.loc.gov/standards/alto/) 則是持續維護的 XML 格式，可保存 OCR 文字、頁面版面、座標與處理中繼資料。第一天不必把整個書庫統一成同一標準，但在評估前就丟掉 bounding box，會讓版面錯誤很難追查。

## 把前處理當成受控變數

[Tesseract 品質指南](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html) 將解析度、二值化、雜訊、旋轉、邊界與頁面分割等問題分開。一次只改一類變數，並永遠保留未修改的來源。

處理 PDF 時，[OCRmyPDF](https://ocrmypdf.readthedocs.io/en/latest/advanced.html) 可以略過已有文字的頁面、重做既有 OCR 層，或強制光柵化；三者並不相同。force 模式會攤平互動內容與既有文字，skip 模式則能保留原生數位頁面。它目前的 renderer 支援右至左文字，但這不代表某一款烏爾都文字體或掃描一定辨識良好。

一張小小的實驗表就夠：

```text
run A：原始影像 + 引擎／模型 1
run B：只做 deskew + 引擎／模型 1
run C：原始影像 + 引擎／模型 2
run D：只做 deskew + 引擎／模型 2
```

比較 CER、閱讀順序、失敗頁、耗時與儲存量。不要因為某一張壞掃描改善了，就把所有濾鏡套到每一本書。

## 不選「萬用冠軍」，改做頁面路由

評分後，建立簡單的路由表：

| 頁面類型 | 選定流程 | 複核規則 |
| --- | --- | --- |
| 原生數位英文 | 擷取既有文字 | 只複核擷取失敗頁 |
| 乾淨阿拉伯文印刷 | 實測最好的阿拉伯文流程 | 低於信心門檻時複核 |
| 烏爾都文 Nastaliq | 實測最好的烏爾都文流程 | 複核人名、引文與低信心片段 |
| 左右向混排 | 能保留版面的流程 | 一律檢查閱讀順序 |
| 表格或平行文本 | 針對結構的流程 | 儲存格崩壞時不要當連續正文索引 |

不同引擎的 confidence score 未經測試集校準，不能直接互比。較安全的規則來自實際錯誤：在樣本中選一個能抓到大部分壞頁的門檻，再人工檢查落在門檻以下的頁面。

## 把證據鏈一路帶進 RAG

每一頁都把四樣東西放在一起：

1. 原始頁面影像或來源 PDF 位置；
2. 原始 OCR 與版面輸出；
3. 用來搜尋的正規化文字；
4. 精確的引擎、模型、設定與執行時間。

索引正規化文字，但每個搜尋結果都必須能跳回來源頁。如果後續校正改變了搜尋文字，保留早期原始輸出並記錄修訂，不要覆蓋歷史。

使用語言模型清理時尤其要小心。宗教、法律、歷史或科學文本中，模型可能把罕見但正確的字改成流暢卻錯誤的內容。可以讓它標出可疑片段或安排複核優先次序，但不要讓它無聲改寫唯一保存的轉寫。

最後，用真正的問題測搜尋。保存 20–50 個查詢、應該找到的頁面，以及讀者必須能核對的段落。若查詢因 OCR 毀掉人名而失敗，就修 OCR 路由；若文字正確、只是用詞不同，再考慮詞彙搜尋加語意搜尋。延伸的[科學文獻集完整性指南](https://blog.lazying.art/html/computer_internet/3788/test-research-pdf-collection-before-local-rag.html)會把同一套評估帶到版本、引用、檢索與知識圖譜 provenance。這樣 embedding 才不會掩蓋來源品質問題。

## 跑完 60 頁後，應該得到什麼答案

測試最後要能明確回答：

- 哪些頁面能自動處理；
- 每種文字與版面該走哪條流程；
- 哪些頁面需要複核；
- 還剩多少字元與閱讀順序錯誤；
- 全量處理需要多少時間與空間；
- 書庫是否已經適合建立索引。

我維護的 [Local Knowledge Terminal](https://github.com/lachlanchen/LocalKnowledgeTerminal) 會把多語書庫處理結果連回可檢查的來源。[範例報告](https://lazying.art/lkt/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=local_knowledge_terminal_pilot&utm_content=multilingual_ocr) 展示了 provenance 與 go/no-go 的做法。若想替一個書庫做同樣的有界檢查，可以先填[免費 fit check](https://lazying.art/lkt/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=local_knowledge_terminal_pilot&utm_content=multilingual_ocr)；只有在中繼資料與權利條件合適後，才會界定可選的 USD 250 sprint。它評估的是代表性樣本，不包含自訂 OCR 或整個書庫的轉換。

順序其實很簡單：抽樣、轉寫、量測、路由、保存，最後才建立索引。
