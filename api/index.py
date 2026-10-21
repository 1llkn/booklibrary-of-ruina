import os
import sys

# ถอยกลับ 2 ชั้น (index.py -> โฟลเดอร์ api -> โฟลเดอร์หลัก Root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from book import app

app = app