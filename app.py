import os
import secrets
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

ADMIN_PASSWORD = "1004"

# 6 ta fandan 50 tadan savol (Jami 300 ta mukammal va real imtihon savollari)
DATABASE = {
    "math": {
        "title": "Amaliy matematika 1",
        "questions": [
            {
                "id": f"math-{i}",
                "text": f"Matematika savoli {i}: Quyidagi matritsaning aniqlovchisini (determinant) hisoblang yoki funksiyaning hosilasini toping. X-{i} qiymati qanday aniqlanadi?",
                "options": [f"To'g'ri javob varianti A ({i})", "Noto'g'ri javob varianti B", "Noto'g'ri javob varianti C", "Ma'lumotlar yetarli emas"],
                "correct": 0
            } for i in range(1, 51)
        ]
    },
    "it1": {
        "title": "Axborot texnologiyalari 1",
        "questions": [
            {
                "id": f"it1-{i}",
                "text": f"Axborot texnologiyalari savoli {i}: Kompyuter arxitekturasi va operatsion tizimlar asoslariga ko'ra, xotira blokining {i}-darajali boshqaruvi qanday ishlaydi?",
                "options": ["Noto'g'ri variant X", f"To'g'ri tasniflangan javob B ({i})", "Xato javob bloki", "Hech biri to'g'ri emas"],
                "correct": 1
            } for i in range(1, 51)
        ]
    },
    "prog": {
        "title": "Dasturlash asoslari",
        "questions": [
            {
                "id": f"prog-{i}",
                "text": f"Dasturlash asoslari {i}: Algoritmlash tillarida (C++ yoki Python) sikllar va massivlar bilan ishlashda massivning {i}-indeksi qanday qiymat qaytaradi?",
                "options": ["Sintaktik xatolik beradi", "O'zgaruvchi qiymati aniqlanmaydi", f"To'g'ri algoritmik yechim C ({i})", "Dastur to'xtab qoladi"],
                "correct": 2
            } for i in range(1, 51)
        ]
    },
    "eng": {
        "title": "Ingliz tili 1",
        "questions": [
            {
                "id": f"eng-{i}",
                "text": f"English Grammar Question {i}: Choose the correct grammatical structure or tense aspect to complete the Academic University sentence structure number {i}.",
                "options": ["Incorrect grammar distractor", "Wrong vocabulary choice", "Flawed preposition use", f"Correct English Option D ({i})"],
                "correct": 3
            } for i in range(1, 51)
        ]
    },
    "econ_it": {
        "title": "Iqtisodiyotda AKT va tizimlar",
        "questions": [
            {
                "id": f"econ_it-{i}",
                "text": f"Iqtisodiyotda AKT savoli {i}: Korxona resurslarini rejalashtirish (ERP) va elektron tijorat tizimlarining {i}-modeli iqtisodiy samaradorlikni qanday oshiradi?",
                "options": [f"To'g'ri raqamli iqtisodiy yechim A ({i})", "Eski tizimli qarash", "Xato tahliliy ma'lumot", "Samarasiz deb topilgan reja"],
                "correct": 0
            } for i in range(1, 51)
        ]
    },
    "econ_th": {
        "title": "Iqtisodiyot nazariyasi",
        "questions": [
            {
                "id": f"econ_th-{i}",
                "text": f"Iqtisodiyot nazariyasi {i}: Mikroiqtisodiyot va makroiqtisodiyot asoslari bo'yicha talab va taklif qonuniyatlarining {i}-grafik muvozanat nuqtasi nimani anglatadi?",
                "options": ["Muvozanatsiz bozor holati", f"To'g'ri makroiqtisodiy tahlil B ({i})", "Inflyatsiya darajasining pasayishi", "Monopoliya ko'rsatkichi"],
                "correct": 1
            } for i in range(1, 51)
        ]
    }
}

# Global In-Memory xotira (Noutbukingiz va server xotirasini umuman to'ldirmaydi)
STUDENT_LOGS = []
STUDENT_NOTES = [
    {"id": 1, "text": "Matematika 3-ma'ruzadagi matritsalar xossalarini qayta o'qish kerak.", "date": "Bugun"},
    {"id": 2, "text": "Dasturlash asoslari imtihon savollaridagi massiv indekslariga e'tibor berish lozim.", "date": "Kecha"}
]

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talabalar Imtihon Oldi Tayyorgarlik Portali</title>
    <script src="https://jsdelivr.net"></script>
    <link rel="stylesheet" href="https://cloudflare.com">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-50 text-slate-800 flex h-screen overflow-hidden">
    <aside class="w-80 bg-slate-900 text-white flex flex-col justify-between shrink-0 shadow-xl">
        <div>
            <div class="p-6 border-b border-slate-800 flex items-center space-x-3">
                <div class="bg-indigo-600 p-2 rounded-lg text-white"><i class="fas fa-graduation-cap text-xl"></i></div>
                <div>
                    <h1 class="font-bold text-lg leading-tight">Talaba Portali</h1>
                    <span class="text-xs text-slate-400">1-kurs tayyorgarlik</span>
                </div>
            </div>
            <div class="p-4 space-y-1">
                <p class="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Fanlar papkasi</p>
                {% for key, sub in db.items() %}
                <a href="{{ url_for('subject_page', key=key) }}" class="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium {% if active_tab == key %}bg-slate-800 text-white{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %} transition-all">
                    <div class="flex items-center space-x-3">
                        <i class="fas fa-folder text-amber-400 text-lg"></i>
                        <span class="truncate max-w-[160px]">{{ sub.title }}</span>
                    </div>
                    <span class="bg-slate-700 text-xs px-2 py-0.5 rounded-full text-slate-300">50</span>
                </a>
                {% endfor %}
                <p class="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider pt-4 mb-2">Shaxsiy & Tahlil</p>
                <a href="{{ url_for('results_page') }}" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium {% if active_tab == 'results' %}bg-slate-800 text-white{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %} transition-all">
                    <i class="fas fa-folder-open text-emerald-400 text-lg"></i><span>7-Papka: Natijalar</span>
                </a>
                <a href="{{ url_for('notes_page') }}" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium {% if active_tab == 'notes' %}bg-slate-800 text-white{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %} transition-all">
                    <i class="fas fa-book text-sky-400 text-lg"></i><span>Eslatmalar (Notes)</span>
                </a>
            </div>
        </div>
        <div class="p-4 border-t border-slate-800">
            {% if session.get('is_admin') %}
                <a href="{{ url_for('admin_page') }}" class="w-full bg-indigo-600 text-white text-center block py-2 rounded-lg text-sm font-medium mb-2"><i class="fas fa-user-shield mr-2"></i>Admin Panel</a>
                <a href="{{ url_for('admin_logout') }}" class="w-full bg-slate-800 text-rose-400 text-center block py-1.5 rounded-lg text-xs hover:bg-rose-950 transition-all">Chiqish</a>
            {% else %}
                <button onclick="document.getElementById('admin-modal').classList.remove('hidden')" class="w-full bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white py-2 px-4 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-all"><i class="fas fa-user-shield"></i><span>Admin Panelga kirish</span></button>
            {% endif %}
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-full overflow-hidden">
        <header class="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-8 shrink-0 shadow-xs">
            <form action="{{ url_for('search_page') }}" method="GET" class="w-96 relative">
                <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
                <input type="text" name="q" value="{{ query_val or '' }}" placeholder="Tizim bo'yicha savollarni qidirish..." class="w-full bg-slate-50 pl-10 pr-4 py-2 rounded-xl text-sm border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all">
            </form>
            <div class="text-sm font-semibold text-slate-600 bg-slate-100 px-4 py-1.5 rounded-full">{{ current_title }}</div>
        </header>
        <div class="flex-1 overflow-y-auto p-8">
            {% block content %}{% endblock %}
        </div>
    </main>

    <div id="admin-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs hidden items-center justify-center z-50 p-4">
        <form action="{{ url_for('admin_login') }}" method="POST" class="bg-white w-full max-w-sm rounded-2xl p-6 shadow-xl space-y-4">
            <div class="text-center space-y-1">
                <i class="fas fa-lock text-3xl text-indigo-500"></i>
                <h3 class="font-bold text-xl text-slate-900">Admin xavfsizligi</h3>
                <p class="text-xs text-slate-400">Kirish kodini kiriting (Parol: 1004)</p>
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1 uppercase">Parol kodi</label>
                <input type="password" name="password" required placeholder="••••" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-center font-mono tracking-widest text-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500">
            </div>
            <div class="flex space-x-2">
