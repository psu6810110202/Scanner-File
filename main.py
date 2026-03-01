import asyncio
import concurrent.futures
import threading
import time
import hashlib
import os
import string

# --- เช็กไฟล์จริง ---
def compute_file_hash(filepath):
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
        return f"❌ อ่านไม่ได้: {full_location} ({type(e).__name__})"

# --- ฟังก์ชันช่วยค้นหาไดรฟ์ที่มีอยู่ในเครื่อง ---    
def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

# --- ฟังก์ชันช่วยค้นหาไฟล์ในเครื่อง ---
def find_files_in_system(target, drive_list):
    found_paths = []
    print(f"🔎 เริ่มค้นหาในไดร์ฟ: {', '.join(drive_list)} ...")
    
    for drive in drive_list:
        print(f"📁 กำลังสแกน {drive}...")
        for root, dirs, files in os.walk(drive):
            if any(x in root for x in ['AppData', '$Recycle.Bin', 'Windows', '.git']):
                continue

            for filename in files:
                for targets in target:
                    if targets.lower() in filename.lower():
                        found_paths.append(os.path.join(root, filename))
    return list(set(found_paths))
    
# --- บันทึก Log ---
def logger_to_file(message):
    with open("scan_report.txt", "a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

# --- ฟังก์ชันหลัก ---
async def main():
    print("--- Scanner-File (v1.1) ---\n")

    available_drives = get_available_drives()
    print("เลือกโหมดการสแกน:")
    print("1. สแกนทุกไดร์ฟที่มี")
    print("2. เลือกเฉพาะบางไดร์ฟ")

    choice = input("กรุณาเลือก (1 หรือ 2): ").strip()
    
    selected_drives = []
    if choice == "1":
        selected_drives = available_drives
    elif choice == "2":
        print(f"\n📀 ไดร์ฟในเครื่องทั้งหมด: {', '.join(available_drives)}")
        drive_input = input(f"ระบุไดร์ฟที่ต้องการ: ").upper()
        selected_drives = [f"{d.strip()}:\\" for d in drive_input.split(",") if f"{d.strip()}:\\" in available_drives]
    
    if not selected_drives:
        print("⚠️ ไม่ได้เลือกไดร์ฟที่ถูกต้อง จบการทำงาน")
        return
    
    files = input("ใส่ชื่อไฟล์ในเครื่อง (หรือกด Enter เพื่อข้าม): ").strip()
    if not files: 
        print("⚠️ ไม่ได้ใส่ชื่อไฟล์ จบการทำงาน")
        return
    
    files = [f.strip() for f in files.split(",") if f.strip()]
    start_time = time.perf_counter()

    found_files = find_files_in_system(files, selected_drives)

    if not found_files:
        print(f"❌ ไม่พบไฟล์ {files} ในโฟลเดอร์นี้และโฟลเดอร์ย่อย")
        return

    print(f"✅ เจอไฟล์ทั้งหมด {len(found_files)} ตำแหน่งที่ตรงกับคำค้นหา")

    loop = asyncio.get_running_loop()
    tasks = []
    with concurrent.futures.ProcessPoolExecutor() as pool:
        for f in found_files:
            tasks.append(loop.run_in_executor(pool, compute_file_hash, f))

        print("🚀 กำลังรวบรวมข้อมูลและคำนวณ Hash พร้อมกัน...")
        results = await asyncio.gather(*tasks)

        # แสดงผลและบันทึก Log
        print("\n--- [ รายงานตำแหน่งไฟล์ที่พบ ] ---")
        for r in results:
            print(r)
            threading.Thread(target=logger_to_file, args=(r,), daemon=True).start()

    print(f"\n✅ ค้นหาและสแกนเสร็จสิ้นในเวลา: {time.perf_counter() - start_time:.2f} วินาที")

    print(f"\n✅ เสร็จสิ้น! บันทึกรายงานใน 'scan_report.txt' แล้ว")
    print(f"⏱️ เวลารวม: {time.perf_counter() - start_time:.2f} วินาที")

if __name__ == "__main__":
    asyncio.run(main())