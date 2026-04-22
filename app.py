import streamlit as st
import os
import time  # 🔥 Import thêm thư viện time
from langchain.chains import ConversationalRetrievalChain # ✅ Đổi thành chuỗi hội thoại
from langchain.memory import ConversationBufferWindowMemory # ✅ Thêm bộ nhớ
from langchain.prompts import PromptTemplate
from utils import get_llm, load_vector_store

st.set_page_config(page_title="Python AI Tutor", page_icon="🐍", layout="wide")
st.title("🐍 Python AI Tutor – Trợ lý học tập thông minh")

# --- KHỞI TẠO STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔥 Khởi tạo mảng lưu thời gian các request
if "request_times" not in st.session_state:
    st.session_state.request_times = []

# --- KHỞI TẠO RAG CHAIN CÓ BỘ NHỚ ---
if "qa_chain" not in st.session_state:
    try:
        vector_store = load_vector_store()
        llm = get_llm()

        # Giữ nguyên Template cũ của bạn
        template = """Bạn là trợ lý giảng dạy Python.

NHIỆM VỤ:
- Ưu tiên trả lời dựa trên NGỮ CẢNH được cung cấp
- Nếu ngữ cảnh chưa đủ, bạn được phép sử dụng kiến thức Python chung để bổ sung
- Không được bịa thông tin sai

CÁCH TRẢ LỜI:
1. Trả lời rõ ràng, dễ hiểu
2. Có thể mở rộng thêm nếu cần để người học hiểu bản chất
3. Nếu phù hợp → đưa ví dụ code Python
4. Nếu có phần không nằm trong tài liệu → nói rõ: "Phần này là kiến thức bổ sung"

NẾU NGỮ CẢNH KHÔNG LIÊN QUAN:
→ Hãy trả lời dựa trên kiến thức Python cơ bản và nói rõ: "Không có trong tài liệu, nhưng..."

---------------------
NGỮ CẢNH:
{context}
---------------------
CÂU HỎI:
{question}

TRẢ LỜI:
"""

        PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

        # ✅ KHỞI TẠO BỘ NHỚ (Nhớ 3 vòng hội thoại gần nhất)
        if "memory" not in st.session_state:
            st.session_state.memory = ConversationBufferWindowMemory(
                memory_key="chat_history", # Khóa mặc định LangChain cần
                return_messages=True,
                output_key="answer",       # Báo cho memory biết đâu là câu trả lời để lưu lại
                k=3                        # Chỉ nhớ 3 câu hỏi/đáp gần nhất
            )

        # ✅ DÙNG CONVERSATIONAL CHAIN THAY VÌ RETRIEVALQA
        st.session_state.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 3, "fetch_k": 6}
            ),
            memory=st.session_state.memory, # Gắn bộ nhớ vào đây
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": PROMPT} # Nhét prompt của bạn vào bước cuối
        )
    except Exception as e:
        st.error(f"Lỗi: {e}. Đừng quên chạy 'python ingest.py'!")
        st.stop()

# --- HIỂN THỊ CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- XỬ LÝ LOGIC RATE LIMIT & NHẬN CÂU HỎI ---
if prompt := st.chat_input("Hỏi tôi bất cứ điều gì về bài học Python..."):

    # 🔥 Logic kiểm tra Rate Limit (Tối đa 5 req/phút)
    current_time = time.time()
    # Lọc giữ lại những request diễn ra trong vòng 60 giây qua
    st.session_state.request_times = [t for t in st.session_state.request_times if current_time - t < 60]

    if len(st.session_state.request_times) >= 5:
        # Nếu đã đủ 5 request trong 60s qua, chặn lại
        st.warning("⚠️ Bạn đã đạt giới hạn 5 câu hỏi / phút. Vui lòng đợi một lát rồi thử lại nhé!")
    else:
        # Cho phép gửi request và ghi nhận thời gian
        st.session_state.request_times.append(current_time)

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Đang tra cứu và suy nghĩ..."):
                # ✅ Sửa "query" thành "question"
                res = st.session_state.qa_chain.invoke({"question": prompt})

                # ✅ Sửa "result" thành "answer"
                answer = res["answer"]

                st.markdown(answer)

                # Hiển thị nguồn (giữ nguyên)
                with st.expander("📚 Nguồn tài liệu"):
                    sources = {os.path.basename(d.metadata['source']) for d in res['source_documents']}
                    for s in sources:
                        st.write(f"- {s}")

        st.session_state.messages.append({"role": "assistant", "content": answer})