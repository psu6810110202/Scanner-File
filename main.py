import asyncio
import concurrent.futures
import threading
import time
import hashlib
import os
from pathlib import Path

# --- 1. งานเช็กไฟล์จริง (ใช้ Process Pool เพราะการคำนวณ Hash กิน CPU) ---
def compute_file_hash(filepath):
    """อ่านไฟล์จริง คำนวณ SHA-256 และบอกที่อยู่ไฟล์"""
    full_location = os.path.abspath(filepath)
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return (f"🛡️ [FILE FOUND] {os.path.basename(filepath)}\n"
                f"📍 Location: {full_location}\n"
                f"🔑 SHA-256: {sha256_hash.hexdigest()}\n"
                f"{'-'*50}")
    except Exception as e:
        return f"❌ ไฟล์ {filepath}: อ่านไม่ได้ ({str(e)})"
    
# --- 3. งานบันทึก Log จริง (ใช้ Threading เขียนลงไฟล์แยก) ---
def logger_to_file(message):
    with open("scan_report.txt", "a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

async def main():
    print("--- Scanner-File (v1.0) ---\n")
    
    files = input("ใส่ชื่อไฟล์ในเครื่อง (หรือกด Enter เพื่อข้าม): ").split()

    start_time = time.perf_counter()
    loop = asyncio.get_running_loop()
    tasks = []

    # 2. เตรียมงานคำนวณไฟล์ (Process Pool)
    with concurrent.futures.ProcessPoolExecutor() as pool:
        for f in files:
            tasks.append(loop.run_in_executor(pool, compute_file_hash, f))

        print("\n🚀 กำลังรันการสแกนจริงทั้งหมดขนานกัน...")
        results = await asyncio.gather(*tasks)

        # แสดงผลและบันทึก Log ผ่าน Thread
        for r in results:
            print(r)
            # โยนงานบันทึก Log ให้ Thread ทำเบื้องหลัง
            threading.Thread(target=logger_to_file, args=(r,), daemon=True).start()

    print(f"\n✅ เสร็จสิ้น! บันทึกรายงานใน 'scan_report.txt' แล้ว")
    print(f"⏱️ เวลารวม: {time.perf_counter() - start_time:.2f} วินาที")

if __name__ == "__main__":
    asyncio.run(main())