import os
import sys

# ถอยกลับ 2 ชั้นไปยัง Root Directory (index.py -> api/ -> Root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from book import app

app = app