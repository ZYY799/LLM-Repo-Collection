# 🧠 FunctionCall Mail Agent

## Quickly start
下载本项目文件并进行相关配置
### Requirements

- python 3.9+
- 安装依赖：

```bash
pip install streamlit openai python-dotenv
```
### Env config
创建 `.env` 文件并配置以下环境变量：

```env
# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key

# 邮件授权码（用于邮件发送功能）
AUTHORIZATION_CODE=your_email_authorization_code

# 邮箱号（与上面授权码对应，发件人邮箱）
DEFAULT_SENDER_EMAIL=XXXXXX@XX.com
```

### 3. Run

```bash
# 启动Streamlit应用
streamlit run stapp.py
```

### Useage

#### 邮件发送

可以要求AI帮助发送邮件，系统会调用邮件发送功能。
**示例：**
```
用户：帮我发送一封邮件，通知2770468515@qq.com，主题是会议通知，内容是告知他明天下午两点在学院开会，具体信息看微信通知。
```


#### 知识搜索

可以搜索内置的知识库获取相关信息。

**示例：**
```
用户：作者是谁
AI：会自动调用知识库搜索功能并返回Python的相关信息
```

## Advanced settings

### 自定义知识库

可以在 `app.py` 中的 `KNOWLEDGE_BASE` 字典中添加更多知识条目：

```python
KNOWLEDGE_BASE = {
    "python": "Python相关信息...",
    "ai": "人工智能相关信息...",
    "your_topic": "你的主题信息...",
}
```

### 添加新的工具

可以在 `tools` 列表中添加新的Function Calling工具：

```python
{
    "type": "function",
    "function": {
        "name": "your_function_name",
        "description": "功能描述",
        "parameters": {
            # 参数定义
        }
    }
}
```
---

*最后更新：2025-08-20*
