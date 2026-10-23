# 实验室科研辅助 Agent（Python + Streamlit）

## 功能
- AI 研究助手：通过 DeepSeek API 进行对话
- 文献总结：提取 PDF 文字并生成结构化总结
- 研究笔记：使用 SQLite 保存到本机
- 任务管理：添加、完成和删除研究任务

## 1. 安装 Python
建议安装 Python 3.11 或 3.12，并在安装界面勾选 `Add Python to PATH`。

## 2. 解压项目
将整个文件夹放到容易找到的位置，例如桌面。

## 3. 打开终端
Windows：进入项目文件夹，在地址栏输入 `cmd` 后回车，或在文件夹空白处右键打开终端。

## 4. 安装依赖
```bash
python -m pip install -r requirements.txt
```

如果 `python` 命令不可用，可试：
```bash
py -m pip install -r requirements.txt
```

## 5. 获取 API Key
到 DeepSeek 开放平台创建 API Key。API Key 是私密凭证，不要发给别人，也不要放进代码文件。

## 6. 启动
```bash
python -m streamlit run app.py
```
浏览器通常会打开本地页面；如果没有自动打开，请复制终端显示的 `Local URL`（通常是 `http://localhost:8501`）到浏览器。

## 7. 使用
- 在左侧 `DeepSeek API Key` 输入你的密钥
- 模型名称默认是 `deepseek-flash`；若服务商的控制台要求其他模型名，请按控制台更新
- 在左侧选择 `AI 研究助手`、`文献总结`、`研究笔记` 或 `任务管理`

## 数据与隐私
- 研究笔记和任务保存到项目文件夹里的 `research_assistant.db`
- API 对话和提交给 AI 的 PDF 文本会发送到 DeepSeek API 处理
- PDF 文本提取目前最多使用前 45,000 个字符；扫描版 PDF 需要先做 OCR
- 请勿上传受保密协议限制、未脱敏的个人信息或实验室机密
- API 使用可能产生费用

## 常见问题
### `python` 不是内部或外部命令
重新安装 Python 并勾选 Add Python to PATH，或尝试 `py` 命令。

### API Key / 认证错误
确认密钥复制完整、账户 API 可用且没有多余空格；不要把密钥粘贴到公开截图或代码仓库。

### 模型不存在
检查服务商控制台当前支持的模型名称，并修改侧边栏的“模型名称”。

### PDF 总结为空
该 PDF 可能是扫描图片，或复制文字功能受限。先对 PDF 做 OCR，再上传可选择文字的版本。
