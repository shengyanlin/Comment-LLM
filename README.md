# 🍽️ Google Map 評論分析系統 (Comment-LLM)

一個基於 Python 的智能評論分析系統，能夠自動爬取 Google Map 店家評論，建立 RAG (檢索增強生成) 知識庫，並使用大語言模型回答用戶的自然語言問題。

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Selenium](https://img.shields.io/badge/Selenium-4.35+-orange.svg)](https://selenium-python.readthedocs.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--turbo-purple.svg)](https://openai.com/)

## 🎯 功能特色

- **🕷️ 智能爬蟲**: 使用 Selenium 自動爬取 Google Map 評論，支援近一年內的評論數據
- **🧠 RAG 系統**: 基於 Sentence Transformers 和 FAISS 的向量檢索，實現語義搜索
- **🤖 LLM 整合**: 支援 OpenAI GPT 和本地 Ollama 模型，提供智能問答
- **💬 互動介面**: 提供友善的命令行互動式問答體驗
- **📊 數據分析**: 自動生成評論統計、情感分析和摘要報告
- **⚙️ 靈活配置**: 支援多種配置選項和環境設定

## 🏗️ 系統架構

```
Comment-LLM/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── google_map_scraper.py    # Google Map 評論爬蟲
│   ├── rag/
│   │   ├── __init__.py
│   │   └── review_rag.py           # RAG 檢索增強生成系統
│   └── llm/
│       ├── __init__.py
│       └── question_answering.py   # LLM 問答系統
├── data/                           # 數據存儲目錄
│   ├── reviews/                    # 評論數據
│   └── vector_db/                  # 向量數據庫
├── config/
│   └── default_config.json        # 預設配置檔案
├── main.py                        # 主程式入口
├── test_system.py                 # 系統測試腳本
├── requirements.txt               # 依賴套件清單
├── .env.example                   # 環境變數範例
└── README.md                      # 專案說明文檔
```

## 🚀 快速開始

### 1. 環境準備

確保您的系統已安裝：
- Python 3.12+
- Conda (推薦) 或 pip
- Chrome 瀏覽器

### 2. 建立虛擬環境

```bash
# 使用 Conda (推薦)
conda create -n comment_conso python=3.12 -y
conda activate comment_conso

# 或使用 venv
python -m venv comment_env
# Windows
comment_env\Scripts\activate
# macOS/Linux
source comment_env/bin/activate
```

### 3. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 4. 環境配置

複製環境變數範例檔案並設置 API 金鑰：

```bash
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env
```

編輯 `.env` 檔案，添加您的 OpenAI API 金鑰：
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 系統測試

運行測試腳本確保所有組件正常：

```bash
python test_system.py
```

### 6. 啟動系統

```bash
# 互動模式 (推薦新手)
python main.py

# 直接指定餐廳 URL
python main.py --url "https://www.google.com/maps/place/餐廳URL"

# 使用現有評論檔案
python main.py --reviews "data/reviews/reviews_20231201_120000.json"

# 直接提問
python main.py --reviews "reviews.json" --question "這家餐廳的食物品質如何？"
```

## 📖 使用指南

### 爬取評論

1. 在 Google Map 上找到目標餐廳
2. 複製完整的 URL (例如: `https://www.google.com/maps/place/餐廳名稱/@...`)
3. 運行程式並輸入 URL
4. 系統將自動爬取近一年內的評論數據

### 智能問答範例

系統支援各種自然語言問題：

- **食物品質**: "這家餐廳的食物好吃嗎？"、"有什麼推薦的菜品？"
- **服務品質**: "服務態度怎麼樣？"、"等待時間長嗎？"
- **環境氛圍**: "餐廳環境如何？"、"適合約會嗎？"
- **價格評價**: "價格合理嗎？"、"CP值高嗎？"
- **綜合分析**: "這家餐廳值得推薦嗎？"、"有什麼需要改進的地方？"

### 特殊命令

在互動模式中，您可以使用以下特殊命令：

- `stats` - 查看評論統計數據 (評分分佈、平均評分等)
- `summary` - 生成整體評論摘要報告
- `quit` 或 `exit` - 退出程式

## ⚙️ 配置選項

編輯 `config/default_config.json` 來自定義系統設定：

```json
{
  "scraper": {
    "max_reviews": 100,     // 最大爬取評論數量
    "year_limit": 1,        // 時間限制 (年)
    "headless": true        // 是否使用無頭瀏覽器
  },
  "rag": {
    "model_name": "all-MiniLM-L6-v2",  // 嵌入模型
    "top_k": 5              // 檢索評論數量
  },
  "llm": {
    "model_name": "gpt-3.5-turbo",     // LLM 模型
    "temperature": 0.7      // 生成溫度
  }
}
```

## 🔧 進階功能

### 使用本地模型 (Ollama)

1. 安裝 [Ollama](https://ollama.ai/)
2. 下載模型: `ollama pull llama2`
3. 修改配置檔案中的 LLM 設定
4. 重新運行程式

### 批次處理多個餐廳

```python
from main import CommentLLMApp

app = CommentLLMApp()
app.initialize_components()

restaurants = [
    ("https://maps.google.com/restaurant1", "餐廳A"),
    ("https://maps.google.com/restaurant2", "餐廳B")
]

for url, name in restaurants:
    app.scrape_restaurant_reviews(url, name)
    app.build_knowledge_base()
    # 進行分析...
```

### 自定義爬蟲設定

```python
# 修改爬蟲參數
scraper = GoogleMapReviewScraper(headless=False)  # 顯示瀏覽器
reviews = scraper.scrape_reviews(
    url="restaurant_url",
    max_reviews=200,    # 爬取更多評論
    year_limit=2        # 擴展到兩年內
)
```

## 📊 輸出格式

### 評論數據結構
```json
{
  "reviewer_name": "評論者姓名",
  "rating": 5,
  "content": "很棒的餐廳，食物美味，服務優良",
  "date": "2023-12-01T10:30:00",
  "date_text": "2個月前",
  "photo_count": 2
}
```

### LLM 回答結果
```json
{
  "answer": "基於評論分析的回答內容",
  "success": true,
  "model": "gpt-3.5-turbo",
  "usage": {
    "total_tokens": 150
  },
  "restaurant_name": "餐廳名稱",
  "total_reviews": 87
}
```

## 🛠️ 故障排除

### 常見問題

#### 1. 爬蟲無法工作
```bash
# 檢查 Chrome 瀏覽器版本
google-chrome --version

# 更新 ChromeDriver
pip install --upgrade webdriver-manager

# 檢查網路連線
ping google.com
```

#### 2. API 呼叫失敗
- 驗證 OpenAI API 金鑰是否正確
- 檢查 API 配額和計費狀態
- 確認網路可以存取 OpenAI API

#### 3. 向量檢索錯誤
- 確保有足夠的磁碟空間 (建議 >2GB)
- 檢查評論數據是否有效
- 嘗試重新建立向量數據庫

#### 4. 模組導入錯誤
```bash
# 確認虛擬環境已啟動
conda activate comment_conso

# 重新安裝套件
pip install -r requirements.txt --force-reinstall

# 檢查 Python 路徑
python -c "import sys; print(sys.path)"
```

### 調試模式

啟用詳細日誌輸出：
```bash
python main.py --config config/debug_config.json
```

檢查系統狀態：
```bash
python test_system.py
```

## 📈 效能優化

### 硬體建議
- **RAM**: 8GB+ (16GB 推薦)
- **CPU**: 4核心以上
- **硬碟**: SSD 推薦，至少 5GB 可用空間

### 軟體優化
- 使用 `headless=True` 加速爬蟲
- 調整 `max_reviews` 控制處理量
- 使用本地 LLM 減少 API 成本

## 🤝 貢獻指南

歡迎提交 Issues 和 Pull Requests！

### 開發流程
1. Fork 此專案
2. 創建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交變更: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 開啟 Pull Request

### 代碼規範
```bash
# 代碼格式化
black src/ main.py

# 代碼檢查
flake8 src/ main.py

# 運行測試
pytest tests/
```

## 📝 授權條款

此專案使用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## ⚠️ 免責聲明

- 請遵守 Google 服務條款和 robots.txt 規定
- 此工具僅供學習和研究用途
- 請合理使用 API 避免超出配額限制
- 爬取數據請遵守相關法律法規
- 不保證爬取數據的完整性和準確性

## 🔗 相關資源

### 官方文檔
- [OpenAI API 文檔](https://platform.openai.com/docs)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Selenium](https://selenium-python.readthedocs.io/)

### 模型資源
- [Hugging Face Models](https://huggingface.co/models)
- [Ollama Models](https://ollama.ai/library)

### 社群支援
- [GitHub Issues](https://github.com/shengyanlin/Comment-LLM/issues)
- [GitHub Discussions](https://github.com/shengyanlin/Comment-LLM/discussions)

## 🌟 更新日誌

### v1.0.0 (2025-09-21)
- ✨ 初始版本發布
- 🕷️ Google Map 評論爬蟲功能
- 🧠 RAG 檢索增強生成系統
- 🤖 OpenAI GPT 整合
- 💬 互動式命令行介面
- 📊 評論統計和分析功能

---

**如果這個專案對您有幫助，請給我們一個 ⭐ Star！**
