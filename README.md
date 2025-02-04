# File Map
---------------------------------------
![Python Logo](https://github.com/fedetony/yt_download_pytubefix/blob/master/img/main_icon48.png "File Map")
 This is a program to Map your file structure in Harddrives, SDcards and USB storage devices. It stores the paths names and metadata, not the files or contents. It allows you to search for the location of files and to compare find redundant information in backups or storage in general. For latest state check [my github][wp] account. Please contribute with bug reports, or enhancements you would like to have.

Features
---------------------------------------
- Use encrypted Databases (Sqlite), password protected. 
- Search and find files.
- Compare and find redundance in files.
- Create Maps and Map your information/Files into a Map structure. i.e. organize your backups.
- Do simple file operations: copy, paste, cut, delete, rename, move, clone

---------------------------------------

How it works
---------------------------------------
You make a new database or use an existant database. You select the folder you want to map. The mapper will recursively look at each file and map its md5sum value.

Finding duplicates:
Each file has a unique md5sum value. If the file is repeated in the same directory with another name, or in a separate directory, you can remove the duplicates and save disk space.

If a file has been changed, its md5sum is different. You can check whether some files have been changed in your backup files. Select the ones that have changed or are new in a structure.

Special safety file check:
md5sum can be achieved by adding bits until you get the value of a modified file, yet, for safety check of a pecific file you can use md5sum, sha1 (128-bit), and sha256 (256-bit) hashes. A special safe file that needs to be modified will have to match these three hashes, which is impossible except for being the same file. Since each calculation takes a lot of time this is only made for special targeted files on demand.

File Size:
You can calculte file size easy, and see which are the files which take most space.

---------------------------------------

![Python Logo](https://github.com/fedetony/yt_download_pytubefix/blob/master/img/main_icon48.png "File Map") If you like my work consider [supporting me!][sp]

G1(junas) Cesium: D9CFSvUHQDJJ4iFExVU4fTMAidADV8kedabeqtV6o3CS

BTC Bitcoin: n211bgvuTVfwFoV6xwcHE5pPe4zWuQ27je

[sp]: https://github.com/sponsors/fedetony

[Github web page][wp].

[wp]: https://github.com/fedetony


