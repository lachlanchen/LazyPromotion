[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Tìm một nhu cầu thật, viết câu trả lời hữu ích, công khai mối liên hệ và để con người quyết định có gửi hay không.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![Model](https://img.shields.io/badge/Drafting-Codex%20account%20default%20%2F%20low-412991)](https://developers.openai.com/codex/models) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion là trợ lý cục bộ, ưu tiên duyệt trước khi gửi để tìm nhu cầu trên mạng xã hội. Công cụ làm việc với giao diện web thật của Reddit, X, Instagram và Hacker News trong một hồ sơ Chrome chuyên dụng có thể quan sát, lưu các kết quả có thể phù hợp vào SQLite, soạn câu trả lời có căn cứ bằng mô hình Codex được tài khoản hỗ trợ và đề xuất ở mức suy luận thấp, rồi dừng trước khi gửi công khai. Công cụ dành cho người duy trì muốn giúp người khác bằng sản phẩm nguồn mở phù hợp, chứ không biến cộng đồng thành hàng chờ bán hàng.

Kho mã còn lưu danh mục công khai gồm 108 kho mã nguồn `lachlanchen` chưa lưu trữ. Mã nguồn, sách, đồ thị tri thức, nghiên cứu, nội dung đa phương tiện, học ngôn ngữ và AI cục bộ được kết hợp thành các cơ hội xuất phát từ bài toán của người mua và chịu ràng buộc bởi bằng chứng. Sáu tuyến dịch vụ có phạm vi cố định hướng đến cột mốc 1.000 USD đầu tiên đã được xác nhận; lượt nhấp, sao, đơn ứng tuyển và bài đang xếp lịch không được tính là doanh thu.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Quy ước vận hành

- Hữu ích trước: trả lời nhu cầu cụ thể trước khi nhắc đến dự án.
- Minh bạch quan hệ: liên kết của chính mình luôn đi kèm lời nói tự nhiên như “tôi duy trì…” hoặc “tôi xây dựng…”.
- Đúng nhu cầu, không chỉ trùng từ khóa: bài cũ, ý định mơ hồ, nội dung tự quảng bá, yêu cầu nằm trong trích dẫn và cụm từ nhập nhằng đều bị lọc trước bước phân loại bằng mô hình.
- Bằng chứng trước lời chào bán: mỗi tuyến thương mại cần bằng chứng công khai có thể kiểm tra, phạm vi bằng văn bản, điều khoản loại trừ và bước kiểm tra độ phù hợp.
- Một người, một quyết định: không trả lời hàng loạt, nhắn tin riêng không được yêu cầu, tự động bình chọn, theo dõi, tiếp cận lặp lại hay tạo vòng lặp tương tác.
- Phê duyệt chính xác: sửa bản nháp sẽ vô hiệu hóa phê duyệt ngắn hạn gắn với hàm băm; nơi nhận và nội dung gửi phải khớp hoàn toàn với bản con người đã duyệt.
- Thao tác hiển thị: mọi việc trên trình duyệt chỉ dùng hồ sơ Chrome chuyên dụng qua noVNC; các cửa sổ Firefox cá nhân nằm ngoài phạm vi truy cập.
- Mặc định riêng tư: thông tin đăng nhập, cookie, tài liệu khách hàng, ứng viên, bản nháp, phê duyệt, dữ liệu thanh toán và bằng chứng vận hành không vào Git.
- Đo lường nghiêm ngặt: các trạng thái được tách riêng — chú ý → tương tác hữu ích → yêu cầu kiểm tra phù hợp → khách hàng tiềm năng đủ điều kiện → chấp nhận phạm vi → xác nhận thanh toán → đã giao → doanh thu thực nhận. Hoàn tiền được ghi riêng; không bước nào được suy ra từ lượt xem hay kỳ vọng.

## Thành phần hiện tại

| Đường dẫn | Mục đích |
| --- | --- |
| [`promotion.py`](../promotion.py) | Sổ cái SQLite, đối sánh nhu cầu, phân loại và soạn bằng Codex, phê duyệt gắn với hàm băm |
| [`browser.py`](../browser.py) | Khám phá, kiểm tra, chuẩn bị ô soạn và gửi có bảo vệ qua Playwright/CDP |
| [`worker.py`](../worker.py) | Khám phá hữu hạn có thời gian chờ và hàng đợi duyệt riêng tư; không bao giờ tự gửi |
| [`catalog.json`](../catalog.json) và [`github-repos.json`](../github-repos.json) | Quy tắc đối sánh được tuyển chọn và danh mục kho mã công khai |
| [`portfolio-opportunities.json`](../portfolio-opportunities.json) | Kết hợp mã, sách, hệ thống tri thức và nội dung đa phương tiện quanh bài toán người mua |
| [`docs/portfolio-inventory.md`](../docs/portfolio-inventory.md) | Bản đồ đầy đủ các sản phẩm công khai, nhóm theo vấn đề thực tế |
| [`docs/compound-opportunities.md`](../docs/compound-opportunities.md) | Các hợp đồng cơ hội được xếp hạng, có cổng bằng chứng và giao hàng |
| [`docs/first-1000.md`](../docs/first-1000.md) | Sáu dịch vụ giới hạn ở mức 250/500 USD và phép tính cột mốc trung thực |
| [`metrics.py`](../metrics.py), [`network.py`](../network.py) và [`signals.py`](../signals.py) | Phễu có cổng bằng chứng, đồ thị quan hệ công khai và tín hiệu nhu cầu bên thứ nhất |
| [`owned_monitor.py`](../owned_monitor.py) và [`lkt_inbox.py`](../lkt_inbox.py) | Giám sát xuất bản chỉ đọc và tiếp nhận riêng tư yêu cầu kiểm tra LKT |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Một desktop Xvfb/x11vnc/noVNC/Chrome bền vững |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Lựa chọn công cụ nguồn mở và MCP có thể kiểm toán |

## Bắt đầu nhanh

Cần Linux, Python 3.10+, Chrome, Playwright cho Python, Xvfb, x11vnc, `wmctrl`, noVNC/websockify, `tmux` và Codex CLI đã đăng nhập.

```bash
git clone https://github.com/lachlanchen/LazyPromotion.git
cd LazyPromotion
python -m pip install -r requirements.txt
python promotion.py init
scripts/desktop.sh start
python browser.py status
```

Đăng nhập thủ công trong noVNC, rồi chạy một tìm kiếm nhỏ tập trung vào nhu cầu rõ ràng:

```bash
python browser.py search --platform reddit --query 'need help add subtitles to video' --limit 12
python promotion.py list --min-score 5
python browser.py inspect CANDIDATE_ID
python promotion.py triage CANDIDATE_ID
python promotion.py draft CANDIDATE_ID
python browser.py prepare CANDIDATE_ID DRAFT_ID
```

Chỉ gửi sau khi con người duyệt đúng nơi nhận và toàn bộ nội dung:

```bash
python promotion.py approve DRAFT_ID --ttl-minutes 30 --confirm-reviewed-exact-content
python browser.py send CANDIDATE_ID DRAFT_ID --approval-token APPROVAL_TOKEN --confirm-public-write
```

Cùng một chu trình khám phá hỗ trợ Reddit, X, Instagram và Hacker News. Hacker News chỉ dành cho nghiên cứu: LazyPromotion không soạn, phê duyệt, chuẩn bị hay gửi bình luận tại đó. Việc lên lịch nội dung bên thứ nhất đã được duyệt qua Postiz luôn tách biệt với trả lời thành viên cộng đồng. Quy trình chi tiết cho worker, thanh toán, tiếp thị liên kết, giao hàng, Postiz và trình duyệt nằm trong [`docs/`](../docs/).

## Cách ly môi trường chạy

Trình khởi chạy chỉ sở hữu một màn hình 1920×1080 (`:116`), cổng VNC `5936`, cổng noVNC `6136` và cổng CDP loopback `9436`. Nó dùng lại một hồ sơ Chrome bền vững dành riêng cho dự án, từ chối cổng do tiến trình lạ chiếm, ghi một bản bàn giao vận hành riêng tư và chỉ dọn tài nguyên cũ thuộc quyền sở hữu của nó. Trình xem trên máy chủ nên được phóng to trong vùng làm việc GNOME nhưng không bao giờ bật toàn màn hình; hãy dừng toàn bộ stack khi không có lượt duyệt hiển thị nào đang chờ. Firefox cá nhân không thuộc môi trường này, vì vậy không được đọc, di chuyển hay dùng lại thẻ và phiên đăng nhập của nó.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Nền tảng nguồn mở

Phần lõi được giữ nhỏ có chủ đích: Playwright điều khiển trình duyệt hiển thị, SQLite lưu trạng thái cục bộ bền vững, còn mô hình Codex được tài khoản hỗ trợ thực hiện phân loại có cấu trúc và soạn bản nháp. Postiz chỉ dùng để lên lịch nội dung bên thứ nhất đã được duyệt. Kết nối MCP là tùy chọn và được ghim phiên bản; tiến trình con của mô hình không được quyền truy cập trình duyệt, bộ lập lịch, thông tin đăng nhập hay thanh toán. Xem [đánh giá đầy đủ](../docs/open-source-evaluation.md).

Lớp danh mục biến dự án công khai thành hợp đồng cơ hội rõ ràng thay vì quảng bá mọi kho mã cùng lúc. Sáu tuyến hiện tại gồm đánh giá độ phù hợp của bộ sưu tập cục bộ, bản sửa đổi có redline cho bản thảo, chuyển giao bài giảng song ngữ, clip kể chuyện, mẫu sách và lắp ráp clip AI. Nhập dữ liệu từ vựng là một chuyên môn LKT có thể tái sử dụng, không phải tuyên bố rằng một tin tuyển trên thị trường đã đóng vẫn còn mở.

## Xác thực

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

Các lệnh này kiểm tra hợp đồng cục bộ, không xác nhận dịch vụ bên thứ ba còn hoạt động, câu trả lời phù hợp cộng đồng, bản dịch đạt chất lượng, kết quả khách hàng hay doanh thu đã nhận.

## Trích dẫn

Nếu dùng LazyPromotion trong nghiên cứu, hãy trích dẫn kho mã. GitHub đọc [`CITATION.cff`](../CITATION.cff) và hiển thị bảng **Cite this repository**.

```bibtex
@software{chen_lazypromotion_2026,
  author = {Chen, Lachlan},
  title = {LazyPromotion: Review-First Social Discovery and Reply Assistance},
  year = {2026},
  url = {https://github.com/lachlanchen/LazyPromotion}
}
```

## Trạng thái và phạm vi

Đây là bản phát hành sớm ưu tiên Linux. Bộ chọn trang bên thứ ba, quy tắc nền tảng và khả năng của tài khoản có thể thay đổi. Khám phá và soạn thảo chỉ là hỗ trợ, không phải bằng chứng rằng nên đăng câu trả lời. Người vận hành vẫn chịu trách nhiệm về độ chính xác, quyền đối với nội dung, công khai quan hệ, độ phù hợp cộng đồng, điều khoản nền tảng, kiểm tra thanh toán và lần gửi cuối.
