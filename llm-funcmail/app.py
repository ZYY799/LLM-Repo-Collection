import os
from dotenv import load_dotenv
import smtplib, ssl, re, json, time
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, make_msgid
from openai import OpenAI
import streamlit as st

DEEPSEEK_MODELS = {
    "deepseek-chat": "DeepSeek Chat",
    "deepseek-reasoner": "DeepSeek Reasoner"
}

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
AUTHORIZATION_CODE = os.getenv("AUTHORIZATION_CODE")
DEFAULT_SENDER_EMAIL = os.getenv("DEFAULT_SENDER_EMAIL")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": f"Send an email from {DEFAULT_SENDER_EMAIL} to the specified recipient with the subject and content",
            "parameters": {
                "type": "object",
                "properties": {
                    "Subject": {"type": "string", "description": "Subject of the email"},
                    "Body": {"type": "string", "description": "The content of the email"},
                    "Recipients": {"type": "string", "description": "The recipients' email addresses (comma or semicolon separated)"}
                },
                "required": ["Subject", "Body", "Recipients"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search in the knowledge base for relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to find relevant information"}
                },
                "required": ["query"],
            },
        }
    }
]

KNOWLEDGE_BASE = {
    "python": "Python是一种高级编程语言，具有简洁的语法和强大的功能。它广泛用于数据科学、Web开发、人工智能等领域。",
    "ai": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
    "deepseek": "DeepSeek是一家专注于人工智能研究的公司，开发了多种先进的语言模型，包括DeepSeek Chat和DeepSeek Reasoner。",
    "streamlit": "Streamlit是一个开源的Python库，用于快速创建和部署数据科学和机器学习的Web应用程序。",
    "作者": "作者是该项目的开发者，主要目的是测试 Function Calling 机制以及相关功能的实现和调试。"
}

def parse_thinking_content(content: str):

    if not content:
        return None, None
    import re as _re
    thinking_pattern = r'<think>(.*?)</think>'
    match = _re.search(thinking_pattern, content, _re.DOTALL)
    if match:
        thinking_content = match.group(1).strip()
        final_answer = _re.sub(thinking_pattern, '', content, flags=_re.DOTALL).strip()
        return thinking_content, final_answer
    else:
        return None, content

def search_knowledge_base(query: str):
    q = (query or "").lower()
    results = []
    for key, value in KNOWLEDGE_BASE.items():
        if key in q or any(word in key for word in q.split()):
            results.append(f"**{key.title()}**: {value}")
    return "\n\n".join(results) if results else "在知识库中未找到相关信息。"

def chat_completion_request(messages, tools=None, tool_choice=None, model="deepseek-chat"):
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return resp

    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def send_email_ssl465_robust(sender_email: str, auth_code: str, recipients: str, subject: str, body: str, debug: bool=False):

    to_list = [e.strip() for e in re.split(r'[;,]', recipients or "") if e.strip()]
    if not to_list:
        raise ValueError("收件人为空")

    msg = MIMEText(body or "", "plain", "utf-8")
    msg["From"] = sender_email
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = Header(subject or "", "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=(sender_email.split("@")[-1] if "@" in sender_email else "localhost"))


    domain = (sender_email.split("@")[-1] if "@" in sender_email else "").lower()
    if "qq.com" in domain:
        smtp_server = "smtp.qq.com"
    elif "126.com" in domain:
        smtp_server = "smtp.126.com"
    elif "163.com" in domain:
        smtp_server = "smtp.163.com"
    elif "gmail.com" in domain:
        smtp_server = "smtp.gmail.com"
    else:

        smtp_server = "smtp.126.com"

    ctx = ssl.create_default_context()
    server = smtplib.SMTP_SSL(smtp_server, 465, timeout=45, context=ctx)
    try:
        if debug:
            server.set_debuglevel(1)
        server.ehlo()
        server.login(sender_email, auth_code)
        refused = server.sendmail(sender_email, to_list, msg.as_string())

        if refused:
            raise RuntimeError(f"部分/全部收件人被拒绝: {refused}")

        try:
            server.noop()
        except Exception:
            pass

        return True
    finally:
        try:
            server.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        except Exception:
            pass

st.set_page_config(page_title="🧠 Email-Function test", page_icon="🧠", layout="wide")
st.sidebar.header("📃 对话会话:")

def main():
    st.title("🧠 Email-Function test")
    st.sidebar.header("🔧 设置")
    selected_model = st.sidebar.selectbox(
        "选择模型:",
        options=list(DEEPSEEK_MODELS.keys()),
        format_func=lambda x: DEEPSEEK_MODELS[x],
        index=0
    )
    st.sidebar.info(f"当前模型: {DEEPSEEK_MODELS[selected_model]}")

    st.sidebar.markdown("### 📚 知识库预览")
    for key in KNOWLEDGE_BASE.keys():
        st.sidebar.markdown(f"<li>{key.title()}</li>", unsafe_allow_html=True)
    st.sidebar.markdown("</ul>", unsafe_allow_html=True)

    if not DEEPSEEK_API_KEY:
        st.sidebar.error("缺少 DEEPSEEK_API_KEY 环境变量")
    if not DEFAULT_SENDER_EMAIL:
        st.sidebar.error("缺少 DEFAULT_SENDER_EMAIL 环境变量")
    if not AUTHORIZATION_CODE:
        st.sidebar.warning("未设置 AUTHORIZATION_CODE（用于 SMTP 授权）")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant" and "thinking" in m:
                with st.expander("🧠 思考过程", expanded=False):
                    st.markdown(m["thinking"])
            st.markdown(m["content"])

    if prompt := st.chat_input("请输入您的问题..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("AI 正在思考中..."):
            response = chat_completion_request(
                messages=st.session_state.messages,
                tools=tools,
                model=selected_model
            )

        st.sidebar.json(st.session_state)
        st.sidebar.write(response)

        with st.chat_message("assistant"):
            msg = response.choices[0].message
            content = getattr(msg, "content", None)
            tool_calls = getattr(msg, "tool_calls", None) or []

            if content:
                thinking_content, final_answer = None, content
                if selected_model == "deepseek-reasoner":
                    thinking_content, final_answer = parse_thinking_content(content)

                if thinking_content:
                    with st.expander("🧠 思考过程", expanded=False):
                        st.markdown(thinking_content)
                st.markdown(final_answer or content)

                data = {"role": "assistant", "content": final_answer or content}
                if thinking_content:
                    data["thinking"] = thinking_content
                st.session_state.messages.append(data)

            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    fn_name = tool_call.function.name
                    fn_args = tool_call.function.arguments

                    if fn_name == "send_email":
                        args = json.loads(fn_args)

                        st.markdown("📧 **邮件内容预览**")
                        st.markdown(f"**发件人:** {DEFAULT_SENDER_EMAIL}")
                        st.markdown(f"**收件人:** {args['Recipients']}")
                        st.markdown(f"**主题:** {args['Subject']}")
                        st.markdown(f"**内容:** {args['Body']}")

                        unique_key = f"email_{int(time.time())}_{i}"
                        col1, col2 = st.columns(2)

                        def confirm_send_email(args_local: dict):
                            try:
                                ok = send_email_ssl465_robust(
                                    sender_email=DEFAULT_SENDER_EMAIL,
                                    auth_code=AUTHORIZATION_CODE or "",
                                    recipients=args_local.get("Recipients", ""),
                                    subject=args_local.get("Subject", ""),
                                    body=args_local.get("Body", ""),
                                    debug=False,
                                )
                                if ok:
                                    st.success("✅ 邮件发送成功（已提交服务器）。请检查收件箱/垃圾箱/已发送。")
                                    st.session_state.messages.append({"role": "assistant", "content": "邮件已成功发送！"})
                                else:
                                    st.error("❌ 邮件状态未知")
                                    st.session_state.messages.append({"role": "assistant", "content": "邮件状态未知，请稍后查看是否送达。"})
                            except smtplib.SMTPAuthenticationError as e:
                                st.error("❌ 认证失败：请确认 AUTHORIZATION_CODE 为 SMTP 授权码，且已在邮箱设置中开启 SMTP/IMAP。")
                                st.session_state.messages.append({"role": "assistant", "content": f"认证失败：{e}"})
                            except smtplib.SMTPServerDisconnected as e:
                                st.warning("⚠️ 服务器断开连接。若发生在发送后通常已投递；若在登录前断开，请检查网络/端口/证书。")
                                st.session_state.messages.append({"role": "assistant", "content": f"服务器断开连接：{e}"})
                            except Exception as e:
                                st.error(f"❌ 邮件发送失败: {e}")
                                st.session_state.messages.append({"role": "assistant", "content": f"邮件发送失败: {e}"})
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)

                        def cancel_send_email():
                            st.warning("⚠️ 邮件发送已取消")
                            st.session_state.messages.append({"role": "assistant", "content": "邮件发送已取消。"})
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)

                        with col1:
                            st.button("✅ 确认发送", on_click=confirm_send_email, args=(args,), key=f"confirm_{unique_key}")
                        with col2:
                            st.button("❌ 取消发送", on_click=cancel_send_email, key=f"cancel_{unique_key}")

                    elif fn_name == "search_knowledge":
                        args = json.loads(fn_args)
                        query = args["query"]

                        st.markdown(f"🔍 **搜索查询:** {query}")
                        search_results = search_knowledge_base(query)
                        st.markdown("📚 **搜索结果:**")
                        st.markdown(search_results)

                        resp_content = f"搜索查询: {query}\n\n搜索结果:\n{search_results}"
                        st.session_state.messages.append({"role": "assistant", "content": resp_content})
                        st.sidebar.json(st.session_state)
                        st.sidebar.write(response)

if __name__ == "__main__":
    main()
