[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# LazyPromotion

*Tìm một nhu cầu thật, viết câu trả lời hữu ích, công khai mối liên hệ và để con người quyết định có gửi hay không.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Playwright](https://img.shields.io/badge/Browser-Playwright%20%2B%20CDP-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/) [![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](../LICENSE) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/lachlanchen)

LazyPromotion là trợ lý cục bộ, ưu tiên duyệt trước khi gửi để tìm nhu cầu trên mạng xã hội. Công cụ tìm kiếm qua giao diện web thật của Reddit, X hoặc Instagram bằng một hồ sơ Chrome hiển thị và bền vững, lưu ứng viên vào SQLite, soạn một câu trả lời có căn cứ bằng `gpt-5.6-sol` với mức suy luận thấp, rồi dừng trước khi gửi công khai. Mục đích là giúp người khác bằng dự án nguồn mở phù hợp, không phải tiếp thị hàng loạt.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Quy ước vận hành

- Hữu ích trước: trả lời nhu cầu cụ thể trước khi nhắc đến dự án.
- Minh bạch quan hệ: liên kết của chính mình luôn kèm lời nói rõ như “tôi duy trì…” hoặc “tôi xây dựng…”.
- Một người, một quyết định: không trả lời hàng loạt, nhắn tin riêng không được yêu cầu, tự động bình chọn, theo dõi hay tạo vòng lặp tương tác.
- Nhận biết bài đăng chéo: các bản dài giống hệt của cùng tác giả được gom vào một ứng viên chuẩn, ưu tiên bản đã được trả lời.
- Mặc định ưu tiên bài mới: thời gian nguồn và quy mô thảo luận được ghi lại; bài quá 30 ngày bị đánh dấu cũ và không được tạo bản nháp.
- Phê duyệt chính xác: sửa bản nháp sẽ vô hiệu hóa phê duyệt ngắn hạn gắn với hàm băm nội dung.
- Thao tác hiển thị: Chrome chạy trong noVNC và ảnh bằng chứng cục bộ được Git bỏ qua.
- Phiên luôn riêng tư: thông tin đăng nhập, cookie, hồ sơ, ứng viên, bản nháp và phê duyệt không vào kho mã.

## Thành phần hiện tại

| Đường dẫn | Mục đích |
| --- | --- |
| [`promotion.py`](../promotion.py) | Sổ cái SQLite, đối sánh, soạn bằng Codex và phê duyệt |
| [`browser.py`](../browser.py) | Tìm kiếm, kiểm tra, chuẩn bị và gửi có bảo vệ qua Playwright/CDP |
| [`catalog.json`](../catalog.json) | Ánh xạ có căn cứ từ nhu cầu thật đến dự án đang duy trì |
| [`scripts/desktop.sh`](../scripts/desktop.sh) | Một desktop Xvfb/x11vnc/noVNC/Chrome bền vững |
| [`docs/open-source-evaluation.md`](../docs/open-source-evaluation.md) | Đánh giá các lựa chọn nguồn mở |
| [`tests/`](../tests/) | Kiểm thử đối sánh, tính lũy đẳng và phê duyệt chính xác |

## Bắt đầu nhanh

Cần Linux, Python 3.10+, Chrome, Playwright cho Python, Xvfb, x11vnc, noVNC/websockify, `tmux` và Codex CLI đã đăng nhập.

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

## Cách ly môi trường chạy

Cấu hình mặc định dùng một màn hình 3840×1080 (`:116`) với hai vùng Chrome 1920×1080 độc lập cùng chia sẻ một hồ sơ bền vững. noVNC cung cấp vùng chiến dịch trên `6138`, vùng liên kết trên `6137` và toàn cảnh trên `6136`; CDP giữ ở `127.0.0.1:9436` và phiên là `lazypromotion-browser`. Mọi dịch vụ chỉ liên kết với loopback; trình khởi chạy từ chối cổng lạ đang bị chiếm và chỉ dọn khóa màn hình cũ được chứng minh là của chính nó.

```bash
scripts/desktop.sh status
scripts/desktop.sh stop
```

## Nền tảng nguồn mở

Phiên bản đầu dùng Playwright và SQLite thay vì bộ lập lịch lớn hoặc khung né phát hiện. Postiz và Mixpost hữu ích cho chiến dịch đã lên kế hoạch; tính năng né tránh hay tương tác tự động không thuộc quy trình duyệt trước này. Xem [đánh giá đầy đủ](../docs/open-source-evaluation.md).

## Xác thực

```bash
python -m unittest discover -s tests -v
python -m py_compile promotion.py browser.py
bash -n scripts/desktop.sh
git diff --check
```

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

Đây là phiên bản đầu tập trung vào Linux. Bộ chọn của trang bên thứ ba có thể thay đổi. Người vận hành vẫn chịu trách nhiệm về độ chính xác, quy tắc cộng đồng, điều khoản nền tảng, công khai quan hệ và lần gửi cuối.
