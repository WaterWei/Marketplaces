# PaddleOCR API 配置

## 端点

```
JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MODEL = "PaddleOCR-VL-1.6"
```

## 认证

```python
TOKEN = "6b7af09b5ea10f556e9e2ab69d5986fdc4543c2e"
headers = {"Authorization": f"bearer {TOKEN}"}
```

## optionalPayload 参数

```python
optional_payload = {
    "markdownIgnoreLabels": [
        "header", "header_image", "footer", "footer_image",
        "number", "footnote", "aside_text"
    ],
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useLayoutDetection": True,
    "useChartRecognition": False,
    "useSealRecognition": False,
    "useOcrForImageBlock": False,
    "mergeTables": True,
    "relevelTitles": True,
    "layoutShapeMode": "auto",
    "promptLabel": "ocr",
    "repetitionPenalty": 1,
    "temperature": 0,
    "topP": 1,
    "minPixels": 147384,
    "maxPixels": 2822400,
    "layoutNms": True,
    "restructurePages": True
}
```

## 提交 & 下载流程

参考实现：`docs/paddleocr/test_ocr.py`

流程：
1. POST 提交 PDF → 获取 `jobId`
2. 轮询 GET `{JOB_URL}/{jobId}` 直到 `state == "done"`
3. 从 `resultUrl.jsonUrl` 下载 JSONL
4. 解析每行 JSON，提取 `layoutParsingResults[].markdown`
5. 保存每页为 `doc_{page_num}.md`，图片下载到 `imgs/` 目录
