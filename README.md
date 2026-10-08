# HeroAnalizator

Windows security and forensics utility designed for auditing and managing the Windows Task Scheduler.

## Features

* **Privilege Elevation:** Automatically checks for administrator privileges and requests UAC elevation on startup.
* **Task Categorization:** Background thread (`QThread`) parses task XML files and categorizes them based on creation age.
* **CRUD Operations:**
  * **Create and Edit:** Interface to configure task names, executable file paths, command-line arguments, and triggers (OnStart, OnLogon, Daily with execution time).
  * **Delete:** Remove tasks via the interface.
* **Context Menu:** Right-click options to copy task names, copy command strings, or delete tasks.
* **User Interface:** PyQt6-based dark-themed interface.

## Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** PyQt6
* **System Integration:** `ctypes`, `schtasks` CLI, XML parsing (`xml.etree.ElementTree`)
* **Compilation:** Nuitka (translation to native C/C++ code and standalone binary generation)

## Installation and Execution

1. Clone the repository:
   ```bash
   git clone [https://github.com/USERNAME/HeroAnalizator.git](https://github.com/Plugecon/HeroAnalizator.git)
   cd HeroAnalizator
