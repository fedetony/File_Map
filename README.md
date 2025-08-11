# 🗂️ File Map

![File Map Icon](https://github.com/fedetony/yt_download_pytubefix/blob/master/img/main_icon48.png)

**File Map** is a powerful tool to map and manage your file structures across hard drives, SD cards, and USB storage devices. It stores **paths and metadata**—not the actual files—allowing you to search, compare, and organize your data with precision.

🔗 For the latest updates, check out [my GitHub profile](https://github.com/fedetony).  
💬 Contributions, bug reports, and feature suggestions are always welcome!

---

## ✨ Features

- 🔐 Encrypted, password-protected SQLite databases  
- 🔍 Search and locate files across mapped devices  
- 🧮 Compare file maps and see changes in Timestamps/Backups/Organized Directories.
- 🧹 Compare files to detect redundancy and save space  
- 🗺️ Create structured maps to organize backups  
- 🧰 Perform basic file operations: copy, paste, cut, delete, rename, move, clone  
- 🕒 Timeline tracking of file changes (via hashes and metadata)  
- 📊 Analyze file sizes to identify space hogs  
- 🧪 Multi-hash safety checks (MD5, SHA1, SHA256) for sensitive files  

---

## ⚙️ How It Works

1. **Create or load a database**  
2. **Select a folder to map**  
3. The mapper recursively scans files and records metadata including:
   - File path
   - Size
   - MD5 hash

### 🔁 Finding Duplicates

File Map uses MD5 hashes to identify redundant files across your storage.  
- **Duplicates**: Same content, different names, in the same directory  
- **Repeated**: Same content, same or different names, in different directories  

👉 [See full explanation in the Wiki](https://github.com/fedetony/File_Map/wiki#duplicatesrepeated-files)

- You can safely select which to keep and which to remove to reclaim disk space.

### 🛡️ Safety File Checks

For critical files watched, File Map can compute:
- **MD5**
- **SHA1 (128-bit)**
- **SHA256 (256-bit)**

Matching all three ensures the file is **exactly the same**, making tampering virtually impossible.

---

## 💸 Support My Work

If File Map has helped you, consider supporting development:

- **G1 (Junas Cesium):** `D9CFSvUHQDJJ4iFExVU4fTMAidADV8kedabeqtV6o3CS`  
- **BTC (Bitcoin):** `n211bgvuTVfwFoV6xwcHE5pPe4zWuQ27je`  
- Or become a sponsor via [GitHub Sponsors](https://github.com/sponsors/fedetony)

---

## 📚 Resources

- [Project Wiki](https://github.com/fedetony) – Technical notes and usage tips  
- [GitHub Repository](https://github.com/fedetony) – Source code and updates  
