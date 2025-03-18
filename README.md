# Crawl-Data

# crawl data khi có HTML : lấy link trong từng pages => click qua từng pages lấy link => có list link sẽ vào từng trang để lấy theo thẻ HTML

# muốn crawl theo ngày dùng ctrl U để check ngày

# crawl khi có có api => call api của họ lấy thông tin trong api

# crawl data khi không có api và không có HTML

# c1 : dùng id để lấy html trang web (từng sản phẩm) url = `https://keeptee.com/?attachment_id=${object_id}`; và const cloudscraper = require('cloudscraper') để bỏ qua chặn của cloudscraper , cách chống crawl : render id chữ hoặc cho id + 10000000

# c2 : dùng id để lấy html của pages => sau đó lấy link sản phẩm trong từng trang web
