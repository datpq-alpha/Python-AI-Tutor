# import os, time
# from dotenv import load_dotenv
# from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_community.vectorstores import Chroma
#
#
# load_dotenv()
#
#
# # === Cấu hình LLM và Embeddings ===
# def get_embeddings():
#     """Khởi tạo model embedding mới nhất của Google"""
#     return GoogleGenerativeAIEmbeddings(
#         model="models/gemini-embedding-001",  # Đã đổi từ embedding-001 sang text-embedding-004
#         task_type="retrieval_document"      # Thêm dòng này để AI hiểu là dùng cho tìm kiếm tài liệu
#     )
#
#
# def get_llm(temperature=0.1):
#     """Khởi tạo Gemini LLM"""
#     return ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash",
#         temperature=temperature,
#         # convert_system_message_to_human=True
#     )
#
#
# # === Xử lý và lưu trữ Vector ===
# def load_and_process_pdfs(pdf_folder="data"):
#     """Đọc PDF bằng PyMuPDF - Cực kỳ mạnh mẽ cho sách giáo khoa"""
#     documents = []
#     if not os.path.exists(pdf_folder):
#         os.makedirs(pdf_folder)
#
#     files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
#
#     if not files:
#         print(f"⚠️ Thư mục '{pdf_folder}' thực sự đang trống!")
#         return []
#
#     for file in files:
#         file_path = os.path.join(pdf_folder, file)
#         print(f"📄 Đang phân tích chuyên sâu: {file}...")
#         try:
#             loader = PyMuPDFLoader(file_path)
#             data = loader.load()
#             print(f"✅ Đã đọc thành công {len(data)} trang văn bản.")
#             documents.extend(data)
#         except Exception as e:
#             print(f"❌ Lỗi khi đọc file {file}: {e}")
#
#     if not documents:
#         return []
#
#     # Chia nhỏ văn bản
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200
#     )
#     chunks = text_splitter.split_documents(documents)
#     return chunks
#
#
# def create_vector_store(chunks, persist_dir="chroma_db"):
#     """Tạo và lưu Chroma Vector Store với cơ chế chống lỗi Quota (Rate Limit)"""
#     embeddings = get_embeddings()
#
#     if os.path.exists(persist_dir):
#         import shutil
#         shutil.rmtree(persist_dir)
#
#     # Chia nhỏ chunks thành từng đợt (batch) để tránh lỗi 429
#     batch_size = 30  # Mỗi lần chỉ gửi 30 đoạn văn bản
#     vector_store = None
#
#     print(f"📦 Tổng số: {len(chunks)} đoạn văn bản. Bắt đầu nạp theo từng đợt...")
#
#     for i in range(0, len(chunks), batch_size):
#         batch = chunks[i:i + batch_size]
#         if vector_store is None:
#             vector_store = Chroma.from_documents(
#                 documents=batch,
#                 embedding=embeddings,
#                 persist_directory=persist_dir
#             )
#         else:
#             vector_store.add_documents(batch)
#
#         print(f"✅ Đã nạp xong {min(i + batch_size, len(chunks))}/{len(chunks)} đoạn...")
#
#         # Nghỉ 15 giây giữa các đợt để "né" giới hạn 100 req/phút của Google
#         if i + batch_size < len(chunks):
#             print("⏳ Đang nghỉ 15 giây để tránh lỗi quá tải API...")
#             time.sleep(15)
#
#     print(f"🎉 Hoàn tất! Vector store đã sẵn sàng tại '{persist_dir}'")
#     return vector_store
#
#
# def load_vector_store(persist_dir="chroma_db"):
#     """Tải vector store có sẵn"""
#     if not os.path.exists(persist_dir):
#         raise FileNotFoundError(f"Vector store chưa được tạo. Chạy 'python ingest.py' trước.")
#     embeddings = get_embeddings()
#     return Chroma(persist_directory=persist_dir, embedding_function=embeddings)
import os, time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import Chroma

load_dotenv()

# === Cấu hình LLM và Embeddings ===
def get_embeddings():
    """Embedding model mới của Google (chuẩn RAG)"""
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="retrieval_document"
    )


def get_llm(temperature=0.1):
    """LLM Gemini mới (fix lỗi 404)"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",   # ✅ FIX CHÍNH Ở ĐÂY
        temperature=temperature,
        max_output_tokens=1024
    )


# === Xử lý PDF ===
def load_and_process_pdfs(pdf_folder="data"):
    documents = []

    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)

    # ✅ đọc cả thư mục con (fix bug "không tìm thấy PDF")
    from glob import glob
    files = glob(f"{pdf_folder}/**/*.pdf", recursive=True)

    if not files:
        print(f"⚠️ Thư mục '{pdf_folder}' thực sự đang trống!")
        return []

    for file_path in files:
        file_name = os.path.basename(file_path)
        print(f"📄 Đang phân tích chuyên sâu: {file_name}...")
        try:
            loader = PyMuPDFLoader(file_path)
            data = loader.load()
            print(f"✅ Đã đọc thành công {len(data)} trang văn bản.")
            documents.extend(data)
        except Exception as e:
            print(f"❌ Lỗi khi đọc file {file_name}: {e}")

    if not documents:
        return []

    # Chia nhỏ văn bản
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators = ["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


# === Vector Store ===
def create_vector_store(chunks, persist_dir="chroma_db"):
    embeddings = get_embeddings()

    if os.path.exists(persist_dir):
        import shutil
        shutil.rmtree(persist_dir)

    batch_size = 30
    vector_store = None

    print(f"📦 Tổng số: {len(chunks)} đoạn văn bản. Bắt đầu nạp theo từng đợt...")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        if vector_store is None:
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_dir
            )
        else:
            vector_store.add_documents(batch)

        print(f"✅ Đã nạp xong {min(i + batch_size, len(chunks))}/{len(chunks)} đoạn...")

        # ✅ giảm sleep (15s hơi quá lâu)
        if i + batch_size < len(chunks):
            time.sleep(15)

    print(f"🎉 Hoàn tất! Vector store đã sẵn sàng tại '{persist_dir}'")
    return vector_store


def load_vector_store(persist_dir="chroma_db"):
    if not os.path.exists(persist_dir):
        raise FileNotFoundError("Chưa có vector DB. Chạy ingest.py trước.")

    embeddings = get_embeddings()
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )