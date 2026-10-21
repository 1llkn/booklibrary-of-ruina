import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'archive_library_secret_key')

DEFAULT_MONGO_URI = "mongodb+srv://kaw25555665765_db_user:f5m5CpEhpJcMRuWR@booktest.9j6mgew.mongodb.net/booktest?retryWrites=true&w=majority"

def get_collections():
    """สร้าง Connection แบบ Lazy Loading เพื่อป้องกัน Vercel Cold Start Crash"""
    mongo_uri = os.environ.get('MONGO_URI', DEFAULT_MONGO_URI)
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
    db = client['booktest']
    return db['books'], db['members'], db['borrow_records']

def init_db():
    """สร้างข้อมูลเริ่มต้นเมื่อคลังยังว่างเปล่า"""
    try:
        books_col, members_col, _ = get_collections()
        if books_col.count_documents({}) == 0:
            sample_books = [
                {"code": "BK001", "title": "ระบบวิเคราะห์และออกแบบสารสนเทศ", "author": "ดร.สมชาย ใจดี", "category": "หมวดวิทยาการคอมพิวเตอร์", "isbn": "978-6160011221", "total_qty": 3, "available_qty": 2},
                {"code": "BK002", "title": "การบริหารจัดการฐานข้อมูลขั้นสูง", "author": "ผศ.วิภาดา รักเรียน", "category": "หมวดเทคโนโลยีสารสนเทศ", "isbn": "978-6160011222", "total_qty": 2, "available_qty": 1},
                {"code": "BK003", "title": "การพัฒนาเว็บแอปพลิเคชันด้วย Python", "author": "อาจารย์ประจำวิชา", "category": "หมวดวิศวกรรมซอฟต์แวร์", "isbn": "978-1305686113", "total_qty": 5, "available_qty": 5},
                {"code": "BK004", "title": "เทคโนโลยีสารสนเทศเพื่อการจัดการ", "author": "รศ.นพดล สุขเสริฐ", "category": "หมวดบริหารธุรกิจ", "isbn": "978-6160011224", "total_qty": 4, "available_qty": 4}
            ]
            books_col.insert_many(sample_books)

        if members_col.count_documents({}) == 0:
            sample_members = [
                {"code": "M68040264", "name": "ณัฏฐณิชา คณารัตน์", "role": "นักเรียน", "phone": "081-111-2222", "email": "natthanicha@buu.ac.th"},
                {"code": "M68040267", "name": "ศักย์ศรณ์ แก่นจันทร์", "role": "นักเรียน", "phone": "082-222-3333", "email": "saksorn@buu.ac.th"},
                {"code": "M68040456", "name": "ณัฐนนท์ พยมพฤกษ์", "role": "อาจารย์", "phone": "083-333-4444", "email": "nattanon@buu.ac.th"},
                {"code": "M68040459", "name": "ธีรภัทร รัตนา", "role": "นักเรียน", "phone": "084-444-5555", "email": "theeraphat@buu.ac.th"}
            ]
            members_col.insert_many(sample_members)
    except Exception as e:
        print(f"Init DB Error: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบจัดการห้องสมุด — Library Information System</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800;900&family=Kanit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-obsidian: #050508;
            --sidebar-width: 310px;
            --gold-primary: #FFD700;
            --gold-bright: #FFE566;
            --cyan-ruina: #58B2DC;
            --cyan-glow: rgba(88, 178, 220, 0.45);
            --border-gold: rgba(255, 215, 0, 0.45);
            --border-cyan: rgba(88, 178, 220, 0.55);
            --panel-glass: rgba(6, 6, 12, 0.22);
            --text-main: #FFFFFF;
            --text-muted: #C5C5DC;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        ::-webkit-scrollbar { width: 7px; }
        ::-webkit-scrollbar-track { background: #050508; }
        ::-webkit-scrollbar-thumb { background: var(--cyan-ruina); border-radius: 2px; }

        body {
            background-color: var(--bg-obsidian);
            color: var(--text-main);
            font-family: 'Kanit', sans-serif;
            min-height: 100vh;
            display: flex;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background-image: 
                repeating-linear-gradient(-45deg, rgba(88, 178, 220, 0.01) 0px, rgba(88, 178, 220, 0.01) 2px, transparent 2px, transparent 12px),
                url('/static/libraryofruinawallpapers.jpg');
            background-size: auto, cover;
            background-position: center;
            opacity: 0.88;
            z-index: -2;
            pointer-events: none;
        }

        #welcome-splash {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(4, 4, 7, 0.92);
            backdrop-filter: blur(15px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 1;
            transition: opacity 0.9s ease, visibility 0.9s ease;
            padding: 20px;
        }

        #welcome-splash.fade-out {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }

        .invitation-card {
            width: 100%;
            max-width: 500px;
            background: rgba(9, 9, 14, 0.88);
            border: 2px solid var(--gold-primary);
            outline: 1px solid var(--cyan-ruina);
            outline-offset: -7px;
            padding: 35px 30px;
            text-align: center;
            box-shadow: 0 0 50px rgba(0,0,0,0.95), 0 0 25px var(--cyan-glow);
            position: relative;
            animation: cardAppear 0.85s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .invitation-card::before, .invitation-card::after {
            content: '◆';
            position: absolute;
            color: var(--cyan-ruina);
            font-size: 0.9rem;
        }
        .invitation-card::before { top: 12px; left: 14px; }
        .invitation-card::after { bottom: 12px; right: 14px; }

        .invitation-badge {
            border: 1px solid var(--gold-primary);
            padding: 8px 18px;
            margin: 0 auto 16px auto;
            display: inline-block;
            background: rgba(12, 12, 18, 0.8);
        }

        .invitation-sub-logo {
            font-size: 0.7rem;
            color: var(--gold-primary);
            letter-spacing: 2px;
            font-weight: 600;
        }

        .invitation-header {
            font-family: 'Cinzel', serif;
            font-size: 2rem;
            font-weight: 800;
            color: #F3E5AB;
            letter-spacing: 6px;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .splash-gif {
            max-height: 120px;
            width: auto;
            border-radius: 8px;
            border: 1px solid var(--border-gold);
            box-shadow: 0 0 18px var(--cyan-glow);
            margin: 12px auto 16px auto;
            display: block;
        }

        .ornament-divider {
            color: var(--gold-primary);
            font-size: 0.85rem;
            margin-bottom: 16px;
            letter-spacing: 4px;
            opacity: 0.85;
        }

        .invitation-quote {
            font-family: 'Cinzel', serif;
            font-size: 0.95rem;
            color: var(--gold-primary);
            letter-spacing: 2px;
            margin-bottom: 16px;
            font-weight: 600;
        }

        .invitation-poem {
            font-family: 'Cinzel', serif;
            font-size: 0.78rem;
            color: var(--text-muted);
            letter-spacing: 1.5px;
            line-height: 1.7;
            text-transform: uppercase;
        }

        @keyframes cardAppear {
            0% { opacity: 0; transform: scale(0.9); }
            100% { opacity: 1; transform: scale(1); }
        }

        .layout-wrapper {
            display: flex;
            width: 100%;
            min-height: 100vh;
            position: relative;
        }

        aside.sidebar {
            width: var(--sidebar-width);
            background: rgba(5, 5, 10, 0.25);
            backdrop-filter: blur(3px);
            border-right: 2px solid var(--border-gold);
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0; bottom: 0; left: 0;
            z-index: 1000;
            box-shadow: 8px 0 25px rgba(0,0,0,0.5);
        }

        .sidebar-brand {
            padding: 26px 20px 20px 20px;
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.18) 0%, rgba(88, 178, 220, 0.08) 100%);
            border-bottom: 2px solid var(--border-gold);
            display: flex;
            align-items: center;
            gap: 14px;
            position: relative;
        }

        .sidebar-logo {
            height: 48px;
            width: auto;
            border-radius: 6px;
            border: 1px solid var(--border-gold);
            box-shadow: 0 0 12px var(--cyan-glow);
            transition: transform 0.3s ease;
        }

        .sidebar-logo:hover {
            transform: scale(1.08);
        }

        .brand-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--gold-bright);
            letter-spacing: 0.8px;
            line-height: 1.2;
            text-transform: uppercase;
            text-shadow: 0 2px 8px rgba(0,0,0,0.9);
        }

        .brand-sub {
            font-size: 0.7rem;
            color: var(--cyan-ruina);
            letter-spacing: 1.5px;
            font-weight: 600;
            margin-top: 3px;
            text-shadow: 0 1px 5px rgba(0,0,0,0.9);
        }

        .sidebar-menu {
            display: flex;
            flex-direction: column;
            padding: 26px 16px;
            gap: 10px;
            flex: 1;
        }

        .sidebar-menu-cat {
            font-size: 0.68rem;
            color: var(--gold-primary);
            text-transform: uppercase;
            letter-spacing: 2.5px;
            padding: 0 12px 4px 12px;
            font-weight: 700;
            text-shadow: 0 2px 6px rgba(0,0,0,0.9);
        }

        .sidebar-menu a {
            position: relative;
            color: var(--text-main);
            text-decoration: none;
            padding: 13px 18px;
            font-weight: 600;
            font-size: 0.95rem;
            transform: skewX(-8deg);
            background: rgba(6, 6, 12, 0.22);
            border: 1px solid rgba(255, 215, 0, 0.25);
            transition: all 0.22s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            backdrop-filter: blur(2px);
            text-shadow: 0 2px 6px rgba(0,0,0,0.9);
        }

        .sidebar-menu a span.unskew {
            display: inline-block;
            transform: skewX(8deg);
        }

        .sidebar-menu a:hover {
            color: #FFFFFF;
            background: rgba(88, 178, 220, 0.35);
            border-color: var(--cyan-ruina);
            transform: skewX(-8deg) translateX(8px);
            box-shadow: 0 0 18px var(--cyan-glow);
        }

        .sidebar-menu a.active {
            color: #060609;
            background: linear-gradient(135deg, var(--gold-bright) 0%, #D4AF37 100%);
            border-color: var(--gold-bright);
            font-weight: 800;
            transform: skewX(-8deg) translateX(10px);
            box-shadow: 0 0 22px rgba(255, 215, 0, 0.55);
            text-shadow: none;
        }

        .sidebar-menu a.active span.unskew {
            color: #060609;
        }

        main.main-content {
            margin-left: var(--sidebar-width);
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            width: calc(100% - var(--sidebar-width));
        }

        header.top-header {
            background: rgba(6, 6, 12, 0.2);
            backdrop-filter: blur(3px);
            border-bottom: 2px solid var(--border-gold);
            padding: 16px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 900;
        }

        .header-title-box {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .header-tag {
            background: var(--cyan-ruina);
            color: #060609;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 4px 10px;
            transform: skewX(-12deg);
            letter-spacing: 1px;
        }

        .header-quote {
            font-family: 'Cinzel', serif;
            font-size: 1rem;
            font-weight: 700;
            color: var(--gold-bright);
            letter-spacing: 1px;
            text-shadow: 0 2px 8px rgba(0,0,0,0.9);
        }

        .container {
            padding: 35px 40px;
            width: 100%;
            flex: 1;
            max-width: 1450px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 22px;
            margin-bottom: 35px;
        }

        .card {
            background: var(--panel-glass);
            backdrop-filter: blur(3px);
            border: 1px solid var(--border-gold);
            padding: 22px 26px;
            position: relative;
            transform: skewX(-5deg);
            transition: all 0.25s ease;
            box-shadow: 0 8px 25px rgba(0,0,0,0.45);
        }

        .card .unskew {
            display: block;
            transform: skewX(5deg);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 4px; height: 100%;
            background: var(--cyan-ruina);
        }

        .card:hover {
            transform: skewX(-5deg) translateY(-4px);
            border-color: var(--cyan-ruina);
            box-shadow: 0 10px 30px var(--cyan-glow);
            background: rgba(6, 6, 12, 0.35);
        }

        .card-title {
            font-size: 0.82rem;
            color: #E2E2F0;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            text-shadow: 0 2px 5px rgba(0,0,0,0.9);
        }

        .card-value {
            font-family: 'Cinzel', serif;
            font-size: 2.6rem;
            font-weight: 800;
            color: var(--gold-bright);
            margin-top: 6px;
            text-shadow: 0 3px 10px rgba(0,0,0,0.95);
        }

        .panel {
            background: var(--panel-glass);
            backdrop-filter: blur(3px);
            border: 1px solid var(--border-gold);
            padding: 28px;
            margin-bottom: 35px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.5);
            position: relative;
        }

        .panel-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--gold-primary);
            margin-bottom: 22px;
            border-bottom: 2px solid var(--border-gold);
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-shadow: 0 2px 8px rgba(0,0,0,0.9);
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }

        th, td {
            padding: 15px 18px;
            text-align: left;
            font-size: 0.92rem;
        }

        th {
            background: rgba(12, 12, 22, 0.4);
            color: var(--cyan-ruina);
            font-weight: 700;
            border-bottom: 2px solid var(--border-gold);
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
        }

        td {
            border-bottom: 1px solid rgba(255,255,255,0.12);
            color: var(--text-main);
            text-shadow: 0 1px 5px rgba(0,0,0,0.9);
        }

        tr:hover td {
            background: rgba(88, 178, 220, 0.22);
        }

        .badge {
            padding: 5px 14px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            transform: skewX(-8deg);
        }

        .badge-borrowed {
            background: rgba(230, 126, 34, 0.35);
            color: #FFB347;
            border: 1px solid rgba(230, 126, 34, 0.6);
        }

        .badge-overdue {
            background: rgba(231, 76, 60, 0.4);
            color: #FF6B6B;
            border: 1px solid rgba(231, 76, 60, 0.7);
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }

        .badge-returned {
            background: rgba(46, 204, 113, 0.35);
            color: #2ECC71;
            border: 1px solid rgba(46, 204, 113, 0.6);
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 22px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-size: 0.84rem;
            color: var(--text-muted);
            margin-bottom: 7px;
            font-weight: 500;
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
        }

        .form-control {
            background: rgba(6, 6, 12, 0.55);
            border: 1px solid var(--border-gold);
            color: var(--text-main);
            padding: 12px 16px;
            border-radius: 2px;
            font-family: inherit;
            outline: none;
            transition: all 0.25s ease;
        }

        .form-control:focus {
            border-color: var(--cyan-ruina);
            box-shadow: 0 0 12px var(--cyan-glow);
            background: rgba(10, 10, 20, 0.75);
        }

        .btn {
            padding: 11px 24px;
            border: none;
            font-weight: 700;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.25s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
            transform: skewX(-8deg);
        }

        .btn .unskew { display: inline-block; transform: skewX(8deg); }

        .btn-gold {
            background: linear-gradient(135deg, #FFD700 0%, #D4AF37 100%);
            color: #060609;
            box-shadow: 0 4px 16px rgba(212, 175, 55, 0.4);
        }

        .btn-gold:hover {
            transform: skewX(-8deg) translateY(-2px);
            box-shadow: 0 6px 22px rgba(255, 215, 0, 0.6);
        }

        .btn-crimson {
            background: linear-gradient(135deg, #E74C3C, #900C3F);
            color: white;
            box-shadow: 0 4px 16px rgba(231, 76, 60, 0.4);
        }

        .btn-green {
            background: linear-gradient(135deg, #2ECC71, #117A65);
            color: white;
            box-shadow: 0 4px 16px rgba(46, 204, 113, 0.4);
        }

        .alert {
            padding: 14px 22px;
            background: rgba(46, 204, 113, 0.25);
            border: 1px solid rgba(46, 204, 113, 0.6);
            color: #2ECC71;
            margin-bottom: 25px;
            font-size: 0.92rem;
            backdrop-filter: blur(4px);
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
        }

        .creators-gif {
            height: 110px;
            width: auto;
            border-radius: 6px;
            margin-bottom: 18px;
            border: 1px solid var(--border-gold);
            box-shadow: 0 0 20px var(--cyan-glow);
        }
    </style>
</head>
<body>

    <div id="welcome-splash">
        <div class="invitation-card">
            <div class="invitation-badge">
                <div class="invitation-sub-logo">BOOK, LIBRARIAN, STAR AND CITY</div>
            </div>
            <div class="invitation-header">INVITATION</div>
            <div class="ornament-divider">❖ ────── ✦ ────── ❖</div>
            
            <img src="/static/rien.gif" alt="Rien GIF" class="splash-gif" onerror="this.style.display='none'">

            <div class="invitation-quote">THE LIBRARY WILL LAST ON FOREVER</div>
            <div class="invitation-poem">
                ILLUMINATED, SOLITARY, INFINITE,<br>
                PERFECTLY IMMOVABLE,<br>
                FILLED WITH PRECIOUS VOLUMES,<br>
                USELESS, INCORRUPTIBLE, SECRET.
            </div>
        </div>
    </div>

    <div class="layout-wrapper">
        <aside class="sidebar">
            <div class="sidebar-brand">
                <img src="/static/book.png" alt="Library Logo" class="sidebar-logo" onerror="this.style.display='none'">
                <div>
                    <div class="brand-title">ระบบจัดการห้องสมุด</div>
                    <div class="brand-sub">INFORMATION SYSTEM</div>
                </div>
            </div>

            <div class="sidebar-menu">
                <div class="sidebar-menu-cat">เมนูหลัก (Navigation)</div>
                <a href="/" class="{{ 'active' if page=='dashboard' }}">
                    <span class="unskew">🏛️ ภาพรวม (Dashboard)</span>
                </a>
                <a href="/books" class="{{ 'active' if page=='books' }}">
                    <span class="unskew">📚 คลังทรัพยากร (Catalog)</span>
                </a>
                <a href="/members" class="{{ 'active' if page=='members' }}">
                    <span class="unskew">👥 ทะเบียนสมาชิก (Members)</span>
                </a>
                <a href="/circulation" class="{{ 'active' if page=='circulation' }}">
                    <span class="unskew">⚖️ โถงยืม-คืน (Reception)</span>
                </a>
                <a href="/reports" class="{{ 'active' if page=='reports' }}">
                    <span class="unskew">📜 รายงาน & ค้างส่ง (Reports)</span>
                </a>
                
                <div class="sidebar-menu-cat" style="margin-top: 18px;">เกี่ยวกับโครงงาน</div>
                <a href="/creators" class="{{ 'active' if page=='creators' }}">
                    <span class="unskew">✨ คณะผู้จัดทำ (Creators)</span>
                </a>
            </div>
        </aside>

        <main class="main-content">
            <header class="top-header">
                <div class="header-title-box">
                    <div class="header-tag">SYSTEM</div>
                    <div class="header-quote">"May you find your book in this place"</div>
                </div>
            </header>

            <div class="container">
                {% with messages = get_flashed_messages() %}
                    {% if messages %}
                        {% for msg in messages %}
                            <div class="alert">✨ {{ msg }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% if page == 'dashboard' %}
                    <div class="stats-grid">
                        <div class="card">
                            <div class="unskew">
                                <div class="card-title">ทรัพยากรสารสนเทศทั้งหมด</div>
                                <div class="card-value">{{ total_books }}</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="unskew">
                                <div class="card-title">สมาชิกในระบบทั้งหมด</div>
                                <div class="card-value">{{ total_members }}</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="unskew">
                                <div class="card-title">รายการที่กำลังถูกยืม</div>
                                <div class="card-value">{{ active_borrows }}</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="unskew">
                                <div class="card-title">รายการเกินกำหนดส่งคืน</div>
                                <div class="card-value" style="color: #FF6B6B;">{{ overdue_count }}</div>
                            </div>
                        </div>
                    </div>

                    <div class="panel">
                        <div class="panel-title">📖 รายการยืม-คืนค้างส่ง ณ ปัจจุบัน</div>
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>ชื่อหนังสือ</th>
                                    <th>ผู้ยืม</th>
                                    <th>วันที่ยืม</th>
                                    <th>กำหนดคืน</th>
                                    <th>สถานะ</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for r in borrow_list %}
                                <tr>
                                    <td>#{{ r.id }}</td>
                                    <td><b>{{ r.book_title }}</b></td>
                                    <td>{{ r.member_name }}</td>
                                    <td>{{ r.borrow_date }}</td>
                                    <td>{{ r.due_date }}</td>
                                    <td>
                                        {% if r.is_overdue %}
                                            <span class="badge badge-overdue">เกินกำหนด!</span>
                                        {% else %}
                                            <span class="badge badge-borrowed">กำลังยืม</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% else %}
                                <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 25px;">ไม่มีรายการยืมค้างอยู่ในระบบ</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                {% elif page == 'books' %}
                    <div class="panel">
                        <div class="panel-title">📝 ลงทะเบียนทรัพยากรใหม่เข้าคลัง</div>
                        <form action="/add_book" method="POST">
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>รหัสหนังสือ (Book Code)</label>
                                    <input type="text" name="code" class="form-control" required placeholder="เช่น BK005">
                                </div>
                                <div class="form-group">
                                    <label>ชื่อหนังสือ (Title)</label>
                                    <input type="text" name="title" class="form-control" required>
                                </div>
                                <div class="form-group">
                                    <label>ผู้แต่ง (Author)</label>
                                    <input type="text" name="author" class="form-control" required>
                                </div>
                                <div class="form-group">
                                    <label>หมวดหมู่ / ชั้นหนังสือ</label>
                                    <input type="text" name="category" class="form-control" required placeholder="เช่น หมวดวิทยาการคอมพิวเตอร์">
                                </div>
                                <div class="form-group">
                                    <label>รหัส ISBN</label>
                                    <input type="text" name="isbn" class="form-control">
                                </div>
                                <div class="form-group">
                                    <label>จำนวนรวม (เล่ม)</label>
                                    <input type="number" name="qty" class="form-control" value="1" min="1" required>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-gold"><span class="unskew">➕ บันทึกหนังสือใหม่</span></button>
                        </form>
                    </div>

                    <div class="panel">
                        <div class="panel-title">
                            <span>📚 รายการหนังสือทั้งหมดในคลัง</span>
                            <form method="GET" action="/books" style="display: inline-flex; gap: 8px;">
                                <input type="text" name="q" class="form-control" placeholder="🔍 ค้นหาหนังสือ..." value="{{ search_q }}">
                                <button type="submit" class="btn btn-gold"><span class="unskew">ค้นหา</span></button>
                            </form>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>รหัส</th>
                                    <th>ชื่อเรื่อง</th>
                                    <th>ผู้แต่ง</th>
                                    <th>หมวดหมู่</th>
                                    <th>ISBN</th>
                                    <th>คงเหลือ/ทั้งหมด</th>
                                    <th>จัดการ</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for b in books %}
                                <tr>
                                    <td><b>{{ b.code }}</b></td>
                                    <td>{{ b.title }}</td>
                                    <td>{{ b.author }}</td>
                                    <td>{{ b.category }}</td>
                                    <td>{{ b.isbn or '-' }}</td>
                                    <td><b style="color:var(--gold-bright)">{{ b.available_qty }}</b> / {{ b.total_qty }}</td>
                                    <td>
                                        <a href="/delete_book/{{ b.id }}" class="btn btn-crimson" onclick="return confirm('ยืนยันการลบหนังสือเล่มนี้?')" style="padding: 5px 12px; font-size:0.78rem;"><span class="unskew">🗑️ ลบ</span></a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                {% elif page == 'members' %}
                    <div class="panel">
                        <div class="panel-title">👤 ลงทะเบียนสมาชิกใหม่</div>
                        <form action="/add_member" method="POST">
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>รหัสสมาชิก</label>
                                    <input type="text" name="code" class="form-control" required placeholder="เช่น M68040999">
                                </div>
                                <div class="form-group">
                                    <label>ชื่อ - นามสกุล</label>
                                    <input type="text" name="name" class="form-control" required>
                                </div>
                                <div class="form-group">
                                    <label>ประเภทสมาชิก</label>
                                    <select name="role" class="form-control">
                                        <option value="นักเรียน">นักเรียน / นิสิต</option>
                                        <option value="อาจารย์">อาจารย์</option>
                                        <option value="บุคคลภายนอก">บุคคลภายนอก</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>เบอร์โทรศัพท์</label>
                                    <input type="text" name="phone" class="form-control">
                                </div>
                                <div class="form-group">
                                    <label>อีเมล</label>
                                    <input type="email" name="email" class="form-control">
                                </div>
                            </div>
                            <button type="submit" class="btn btn-gold"><span class="unskew">➕ ลงทะเบียนสมาชิก</span></button>
                        </form>
                    </div>

                    <div class="panel">
                        <div class="panel-title">👥 รายชื่อสมาชิกในระบบ</div>
                        <table>
                            <thead>
                                <tr>
                                    <th>รหัสสมาชิก</th>
                                    <th>ชื่อ - นามสกุล</th>
                                    <th>ประเภท</th>
                                    <th>เบอร์โทร</th>
                                    <th>อีเมล</th>
                                    <th>จัดการ</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for m in members %}
                                <tr>
                                    <td><b>{{ m.code }}</b></td>
                                    <td>{{ m.name }}</td>
                                    <td>{{ m.role }}</td>
                                    <td>{{ m.phone or '-' }}</td>
                                    <td>{{ m.email or '-' }}</td>
                                    <td>
                                        <a href="/delete_member/{{ m.id }}" class="btn btn-crimson" onclick="return confirm('ยืนยันการลบสมาชิกคนนี้?')" style="padding: 5px 12px; font-size:0.78rem;"><span class="unskew">🗑️ ลบ</span></a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                {% elif page == 'circulation' %}
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px;">
                        <div class="panel">
                            <div class="panel-title">📤 ทำรายการยืมหนังสือ (Check-Out)</div>
                            <form action="/borrow" method="POST">
                                <div class="form-group" style="margin-bottom: 15px;">
                                    <label>เลือกรหัส/ชื่อสมาชิกผู้ยืม:</label>
                                    <select name="member_id" class="form-control" required>
                                        {% for m in members %}
                                        <option value="{{ m.id }}">{{ m.code }} — {{ m.name }} ({{ m.role }})</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <div class="form-group" style="margin-bottom: 15px;">
                                    <label>เลือกหนังสือที่ต้องการยืม:</label>
                                    <select name="book_id" class="form-control" required>
                                        {% for b in available_books %}
                                        <option value="{{ b.id }}">{{ b.code }} — {{ b.title }} [ว่าง: {{ b.available_qty }}]</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <div class="form-group" style="margin-bottom: 22px;">
                                    <label>จำนวนวันกำหนดส่งคืน (วัน):</label>
                                    <input type="number" name="days" class="form-control" value="7" min="1" required>
                                </div>
                                <button type="submit" class="btn btn-gold" style="width: 100%; justify-content: center;"><span class="unskew">⚔️ ยืนยันทำรายการยืม</span></button>
                            </form>
                        </div>

                        <div class="panel">
                            <div class="panel-title">📥 ทำรายการคืนหนังสือ & ชำระค่าปรับ</div>
                            <form action="/return" method="POST">
                                <div class="form-group" style="margin-bottom: 20px;">
                                    <label>เลือกรายการยืมที่ต้องการรับคืน:</label>
                                    <select name="record_id" class="form-control" required>
                                        {% for r in active_records %}
                                        <option value="{{ r.id }}">Rec#{{ r.id }} | {{ r.book_title }} — {{ r.member_name }} (กำหนดคืน: {{ r.due_date }})</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <div style="background: rgba(120,0,0,0.25); border: 1px solid rgba(231,76,60,0.4); padding: 16px; margin-bottom: 22px; font-size: 0.88rem; color: #FF9999; backdrop-filter: blur(4px);">
                                    💡 ระบบจะคำนวณค่าปรับให้อัตโนมัติในอัตรา <b>5.00 บาท/วัน</b> กรณีคืนเกินกำหนดส่ง
                                </div>
                                <button type="submit" class="btn btn-green" style="width: 100%; justify-content: center;"><span class="unskew">⚖️ ยืนยันการรับคืนหนังสือ</span></button>
                            </form>
                        </div>
                    </div>

                {% elif page == 'reports' %}
                    <div class="panel">
                        <div class="panel-title">📜 ประวัติรายการยืม-คืนทั้งหมด & รายงานค่าปรับ</div>
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>ชื่อหนังสือ</th>
                                    <th>ผู้ยืม</th>
                                    <th>วันที่ยืม</th>
                                    <th>กำหนดคืน</th>
                                    <th>วันที่ส่งคืนจริง</th>
                                    <th>ค่าปรับ (บาท)</th>
                                    <th>สถานะ</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for r in records %}
                                <tr>
                                    <td>#{{ r.id }}</td>
                                    <td><b>{{ r.book_title }}</b></td>
                                    <td>{{ r.member_name }}</td>
                                    <td>{{ r.borrow_date }}</td>
                                    <td>{{ r.due_date }}</td>
                                    <td>{{ r.return_date or '-' }}</td>
                                    <td><b style="color:var(--gold-bright)">{{ "%.2f"|format(r.fine_amount) }}</b></td>
                                    <td>
                                        {% if r.status == 'RETURNED' %}
                                            <span class="badge badge-returned">คืนแล้ว</span>
                                        {% elif r.is_overdue %}
                                            <span class="badge badge-overdue">เกินกำหนด!</span>
                                        {% else %}
                                            <span class="badge badge-borrowed">กำลังยืม</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                {% elif page == 'creators' %}
                    <div class="panel" style="text-align: center;">
                        <img src="/static/book.gif" alt="Creators Magic Book GIF" class="creators-gif" onerror="this.style.display='none'">
                        <div class="panel-title" style="justify-content: center;">🎓 คณะผู้จัดทำโครงงาน (Project Creators)</div>
                        <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:25px; line-height: 1.6;">
                            โครงงานระบบจัดการห้องสมุด — รายวิชา 42520467 Information System Analysis and design<br>
                            คณะศึกษาศาสตร์ มหาวิทยาลัยบูรพา
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 20px;">
                            <div class="card" style="text-align: center; padding: 28px 18px;">
                                <div class="unskew">
                                    <div style="font-size: 2.2rem; margin-bottom: 10px;">👤</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--gold-bright); margin-bottom: 8px;">ณัฏฐณิชา คณารัตน์</div>
                                    <div style="font-size: 0.88rem; color: var(--text-main); background: rgba(212,175,55,0.2); border: 1px solid var(--border-gold); display: inline-block; padding: 4px 16px;">รหัสนิสิต: 68040264</div>
                                </div>
                            </div>
                            <div class="card" style="text-align: center; padding: 28px 18px;">
                                <div class="unskew">
                                    <div style="font-size: 2.2rem; margin-bottom: 10px;">👤</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--gold-bright); margin-bottom: 8px;">ศักย์ศรณ์ แก่นจันทร์</div>
                                    <div style="font-size: 0.88rem; color: var(--text-main); background: rgba(212,175,55,0.2); border: 1px solid var(--border-gold); display: inline-block; padding: 4px 16px;">รหัสนิสิต: 68040267</div>
                                </div>
                            </div>
                            <div class="card" style="text-align: center; padding: 28px 18px;">
                                <div class="unskew">
                                    <div style="font-size: 2.2rem; margin-bottom: 10px;">👤</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--gold-bright); margin-bottom: 8px;">ณัฐนนท์ พยมพฤกษ์</div>
                                    <div style="font-size: 0.88rem; color: var(--text-main); background: rgba(212,175,55,0.2); border: 1px solid var(--border-gold); display: inline-block; padding: 4px 16px;">รหัสนิสิต: 68040456</div>
                                </div>
                            </div>
                            <div class="card" style="text-align: center; padding: 28px 18px;">
                                <div class="unskew">
                                    <div style="font-size: 2.2rem; margin-bottom: 10px;">👤</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--gold-bright); margin-bottom: 8px;">ธีรภัทร รัตนา</div>
                                    <div style="font-size: 0.88rem; color: var(--text-main); background: rgba(212,175,55,0.2); border: 1px solid var(--border-gold); display: inline-block; padding: 4px 16px;">รหัสนิสิต: 68040459</div>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endif %}
            </div>
        </main>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var splash = document.getElementById('welcome-splash');
            if (sessionStorage.getItem('archive_visited')) {
                splash.style.display = 'none';
            } else {
                sessionStorage.setItem('archive_visited', 'true');
                setTimeout(function() {
                    splash.classList.add('fade-out');
                }, 1800);
            }
        });
    </script>

</body>
</html>
"""

# ---------------------------------------------------------
# ROUTES & CONTROLLERS
# ---------------------------------------------------------

@app.route('/')
def dashboard():
    init_db()
    try:
        books_col, members_col, borrows_col = get_collections()
        
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_qty"}}}]
        res = list(books_col.aggregate(pipeline))
        total_books = res[0]['total'] if res else 0

        total_members = members_col.count_documents({})
        active_borrows = borrows_col.count_documents({"status": "BORROWED"})
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        overdue_count = borrows_col.count_documents({"status": "BORROWED", "due_date": {"$lt": today_str}})

        active_records = list(borrows_col.find({"status": "BORROWED"}).sort("due_date", 1))
        borrow_list = []
        for r in active_records:
            bk = books_col.find_one({"_id": ObjectId(r['book_id'])}) if isinstance(r['book_id'], (ObjectId, str)) else None
            mb = members_col.find_one({"_id": ObjectId(r['member_id'])}) if isinstance(r['member_id'], (ObjectId, str)) else None
            borrow_list.append({
                'id': str(r['_id']),
                'book_title': bk['title'] if bk else 'ไม่พบข้อมูล',
                'member_name': mb['name'] if mb else 'ไม่พบข้อมูล',
                'borrow_date': r['borrow_date'],
                'due_date': r['due_date'],
                'is_overdue': r['due_date'] < today_str
            })
    except Exception as e:
        total_books, total_members, active_borrows, overdue_count = 0, 0, 0, 0
        borrow_list = []
        flash(f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {str(e)}")

    return render_template_string(HTML_TEMPLATE, page='dashboard', 
                                  total_books=total_books, total_members=total_members,
                                  active_borrows=active_borrows, overdue_count=overdue_count,
                                  borrow_list=borrow_list)

@app.route('/books')
def books():
    init_db()
    q = request.args.get('q', '').strip()
    try:
        books_col, _, _ = get_collections()
        if q:
            query = {
                "$or": [
                    {"title": {"$regex": q, "$options": "i"}},
                    {"author": {"$regex": q, "$options": "i"}},
                    {"category": {"$regex": q, "$options": "i"}},
                    {"code": {"$regex": q, "$options": "i"}}
                ]
            }
            books_cursor = books_col.find(query)
        else:
            books_cursor = books_col.find().sort("_id", -1)

        books_list = []
        for b in books_cursor:
            b['id'] = str(b['_id'])
            books_list.append(b)
    except Exception as e:
        books_list = []
        flash(f"ดึงข้อมูลหนังสือไม่สำเร็จ: {str(e)}")

    return render_template_string(HTML_TEMPLATE, page='books', books=books_list, search_q=q)

@app.route('/add_book', methods=['POST'])
def add_book():
    code = request.form['code'].strip()
    title = request.form['title'].strip()
    author = request.form['author'].strip()
    category = request.form['category'].strip()
    isbn = request.form.get('isbn', '').strip()
    qty = int(request.form.get('qty', 1))

    try:
        books_col, _, _ = get_collections()
        if books_col.find_one({"code": code}):
            flash("เกิดข้อผิดพลาด: รหัสหนังสือซ้ำในระบบ!")
        else:
            books_col.insert_one({
                "code": code,
                "title": title,
                "author": author,
                "category": category,
                "isbn": isbn,
                "total_qty": qty,
                "available_qty": qty
            })
            flash(f"บันทึกหนังสือ '{title}' เรียบร้อยแล้ว")
    except Exception as e:
        flash(f"เพิ่มหนังสือไม่สำเร็จ: {str(e)}")

    return redirect(url_for('books'))

@app.route('/delete_book/<book_id>')
def delete_book(book_id):
    try:
        books_col, _, _ = get_collections()
        books_col.delete_one({"_id": ObjectId(book_id)})
        flash("ลบหนังสือออกจากระบบแล้ว")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการลบ: {str(e)}")
    return redirect(url_for('books'))

@app.route('/members')
def members():
    init_db()
    try:
        _, members_col, _ = get_collections()
        members_cursor = members_col.find().sort("_id", -1)
        members_list = []
        for m in members_cursor:
            m['id'] = str(m['_id'])
            members_list.append(m)
    except Exception as e:
        members_list = []
        flash(f"ดึงข้อมูลสมาชิกไม่สำเร็จ: {str(e)}")
    return render_template_string(HTML_TEMPLATE, page='members', members=members_list)

@app.route('/add_member', methods=['POST'])
def add_member():
    code = request.form['code'].strip()
    name = request.form['name'].strip()
    role = request.form['role']
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    try:
        _, members_col, _ = get_collections()
        if members_col.find_one({"code": code}):
            flash("เกิดข้อผิดพลาด: รหัสสมาชิกซ้ำในระบบ!")
        else:
            members_col.insert_one({
                "code": code,
                "name": name,
                "role": role,
                "phone": phone,
                "email": email
            })
            flash(f"เพิ่มสมาชิก '{name}' เรียบร้อยแล้ว")
    except Exception as e:
        flash(f"เพิ่มสมาชิกไม่สำเร็จ: {str(e)}")

    return redirect(url_for('members'))

@app.route('/delete_member/<member_id>')
def delete_member(member_id):
    try:
        _, members_col, _ = get_collections()
        members_col.delete_one({"_id": ObjectId(member_id)})
        flash("ลบสมาชิกออกจากระบบแล้ว")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการลบ: {str(e)}")
    return redirect(url_for('members'))

@app.route('/circulation')
def circulation():
    init_db()
    try:
        books_col, members_col, borrows_col = get_collections()
        
        members_cursor = members_col.find()
        members_list = []
        for m in members_cursor:
            m['id'] = str(m['_id'])
            members_list.append(m)

        available_books_cursor = books_col.find({"available_qty": {"$gt": 0}})
        available_books = []
        for b in available_books_cursor:
            b['id'] = str(b['_id'])
            available_books.append(b)

        active_records_cursor = borrows_col.find({"status": "BORROWED"})
        active_records = []
        for r in active_records_cursor:
            bk = books_col.find_one({"_id": ObjectId(r['book_id'])}) if isinstance(r['book_id'], (ObjectId, str)) else None
            mb = members_col.find_one({"_id": ObjectId(r['member_id'])}) if isinstance(r['member_id'], (ObjectId, str)) else None
            active_records.append({
                'id': str(r['_id']),
                'book_title': bk['title'] if bk else 'ไม่พบข้อมูล',
                'member_name': mb['name'] if mb else 'ไม่พบข้อมูล',
                'due_date': r['due_date']
            })
    except Exception as e:
        members_list, available_books, active_records = [], [], []
        flash(f"ดึงข้อมูลงานยืม-คืนไม่สำเร็จ: {str(e)}")

    return render_template_string(HTML_TEMPLATE, page='circulation', 
                                  members=members_list, available_books=available_books, active_records=active_records)

@app.route('/borrow', methods=['POST'])
def borrow_book():
    member_id = request.form['member_id']
    book_id = request.form['book_id']
    days = int(request.form.get('days', 7))

    b_date = datetime.now()
    d_date = b_date + timedelta(days=days)

    try:
        books_col, _, borrows_col = get_collections()
        borrows_col.insert_one({
            "book_id": ObjectId(book_id),
            "member_id": ObjectId(member_id),
            "borrow_date": b_date.strftime("%Y-%m-%d"),
            "due_date": d_date.strftime("%Y-%m-%d"),
            "return_date": None,
            "fine_amount": 0.0,
            "status": "BORROWED"
        })

        books_col.update_one({"_id": ObjectId(book_id)}, {"$inc": {"available_qty": -1}})
        flash(f"ยืมหนังสือสำเร็จ! กำหนดคืนวันที่ {d_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        flash(f"ทำรายการยืมไม่สำเร็จ: {str(e)}")

    return redirect(url_for('circulation'))

@app.route('/return', methods=['POST'])
def return_book():
    record_id = request.form['record_id']
    try:
        books_col, _, borrows_col = get_collections()
        rec = borrows_col.find_one({"_id": ObjectId(record_id)})

        if rec:
            book_id = rec['book_id']
            due_date_str = rec['due_date']
            today = datetime.now()
            due_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
            overdue_days = (today - due_dt).days
            fine = overdue_days * 5.0 if overdue_days > 0 else 0.0

            borrows_col.update_one(
                {"_id": ObjectId(record_id)},
                {"$set": {
                    "return_date": today.strftime("%Y-%m-%d"),
                    "fine_amount": fine,
                    "status": "RETURNED"
                }}
            )

            books_col.update_one({"_id": ObjectId(book_id)}, {"$inc": {"available_qty": 1}})
            flash(f"รับคืนหนังสือเรียบร้อยแล้ว! (ค่าปรับ: {fine:.2f} บาท)")
        else:
            flash("ไม่พบข้อมูลรายการยืม")
    except Exception as e:
        flash(f"ทำรายการคืนไม่สำเร็จ: {str(e)}")

    return redirect(url_for('circulation'))

@app.route('/reports')
def reports():
    init_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        books_col, members_col, borrows_col = get_collections()
        rows = list(borrows_col.find().sort("_id", -1))
        records = []
        for r in rows:
            bk = books_col.find_one({"_id": ObjectId(r['book_id'])}) if isinstance(r['book_id'], (ObjectId, str)) else None
            mb = members_col.find_one({"_id": ObjectId(r['member_id'])}) if isinstance(r['member_id'], (ObjectId, str)) else None
            records.append({
                'id': str(r['_id']),
                'book_title': bk['title'] if bk else 'ไม่พบข้อมูล',
                'member_name': mb['name'] if mb else 'ไม่พบข้อมูล',
                'borrow_date': r['borrow_date'],
                'due_date': r['due_date'],
                'return_date': r['return_date'],
                'fine_amount': r['fine_amount'],
                'status': r['status'],
                'is_overdue': r['status'] == 'BORROWED' and r['due_date'] < today_str
            })
    except Exception as e:
        records = []
        flash(f"ดึงรายงานไม่สำเร็จ: {str(e)}")

    return render_template_string(HTML_TEMPLATE, page='reports', records=records)

@app.route('/creators')
def creators():
    return render_template_string(HTML_TEMPLATE, page='creators')

if __name__ == '__main__':
    print("Web Server is running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)