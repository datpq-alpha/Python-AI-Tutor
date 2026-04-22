from utils import load_and_process_pdfs, create_vector_store

if __name__ == "__main__":
    print("🔄 Đang xử lý tài liệu từ thư mục data/...")
    chunks = load_and_process_pdfs("data")
    if chunks:
        create_vector_store(chunks)
        print("🎉 Hoàn tất! Hệ thống đã sẵn sàng.")
    else:
        print("⚠️ Không tìm thấy file PDF nào trong thư mục data.")