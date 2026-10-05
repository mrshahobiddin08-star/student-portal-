import os
import secrets
from datetime import datetime
from flask import Flask, render_html, render_template_string, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ADMIN CONFIGURATION
ADMIN_PASSWORD = "1004"

# QUESTION DATABASE GENERATOR (6 Subjects x 50 Questions = 300 Questions)
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

# IN-MEMORY STORAGE (Safe for serverless/temporary hosting like free Render, avoids heavy local IO)
if not hasattr(app, '_student_logs'):
    app._student_logs = []
if not hasattr(app, '_student_notes'):
    app._student_notes = [
        {"id": 1, "text": "Matematika 3-ma'ruzadagi matritsalar xossalarini qayta o'qish kerak.", "date": "Bugun"},
        {"id": 2, "text": "Dasturlash asoslari imtihon savollaridagi massiv indekslariga e'tibor berish lozim.", "date": "Kecha"}
    ]

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talabalar Imtihon Oldi Tayyorgarlik Portali</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 flex h-screen overflow-hidden">

    <!-- SIDEBAR -->
    <aside class="w-80 bg-slate-900 text-white flex flex-col justify-between shrink-0 shadow-xl">
        <div>
            <div class="p-6 border-b border-slate-800 flex items-center space-x-3">
                <div class="bg-indigo-600 p-2 rounded-lg text-white">
                    <i class="fas fa-graduation-cap text-xl"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg leading-tight">Talaba Portali</h1>
                    <span class="text-xs text-slate-400">Render & GitHub Python App</span>
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
                    <i class="fas fa-folder-open text-emerald-400 text-lg"></i>
                    <span>7-Papka: Natijalar</span>
                </a>

                <a href="{{ url_for('notes_page') }}" class="w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium {% if active_tab == 'notes' %}bg-slate-800 text-white{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %} transition-all">
                    <i class="fas fa-book text-sky-400 text-lg"></i>
                    <span>Eslatmalar (Notes)</span>
                </a>
            </div>
        </div>

        <div class="p-4 border-t border-slate-800">
            {% if session.get('is_admin') %}
                <a href="{{ url_for('admin_page') }}" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-all mb-2">
                    <i class="fas fa-user-shield"></i>
                    <span>Admin Panel</span>
                </a>
                <a href="{{ url_for('admin_logout') }}" class="w-full bg-slate-800 text-rose-400 text-center block py-1.5 rounded-lg text-xs hover:bg-rose-950 transition-all">
                    Chiqish
                </a>
            {% else %}
                <button onclick="document.getElementById('admin-modal').classList.remove('hidden')" class="w-full bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white py-2 px-4 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-all">
                    <i class="fas fa-user-shield"></i>
                    <span>Admin Panelga kirish</span>
                </button>
            {% endif %}
        </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col h-full overflow-hidden">
        <header class="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-8 shrink-0 shadow-xs">
            <form action="{{ url_for('search_page') }}" method="GET" class="w-96 relative">
                <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
                <input type="text" name="q" value="{{ query_val or '' }}" placeholder="Tizim bo'yicha savollarni qidirish..." class="w-full bg-slate-50 pl-10 pr-4 py-2 rounded-xl text-sm border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all">
            </form>
            <div class="text-sm font-semibold text-slate-600 bg-slate-100 px-4 py-1.5 rounded-full">
                {{ current_title }}
            </div>
        </header>

        <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            {% block content %}{% endblock %}
        </div>
    </main>

    <!-- ADMIN LOGIN MODAL -->
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
                <button type="button" onclick="document.getElementById('admin-modal').classList.add('hidden')" class="flex-1 bg-slate-100 text-slate-600 py-2.5 rounded-xl text-sm font-medium">Bekor qilish</button>
                <button type="submit" class="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl text-sm font-medium shadow-xs">Kirish</button>
            </div>
        </form>
    </div>

</body>
</html>
'''

SUBJECT_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <div class="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-2xl p-6 text-white shadow-md flex justify-between items-center">
        <div>
            <h2 class="text-2xl font-bold mb-1">{{ sub_data.title }}</h2>
            <p class="text-indigo-100 text-sm">Imtihondan oldingi faol test tizimi. Savollarga 30 soniyadan vaqt beriladi.</p>
        </div>
        <button onclick="startQuizClient()" class="bg-white text-indigo-600 hover:bg-indigo-50 font-semibold px-6 py-3 rounded-xl transition-all shadow-sm flex items-center space-x-2">
            <i class="fas fa-play"></i>
            <span>Testni Boshlash (Interactive)</span>
        </button>
    </div>

    <!-- Live Interactive Quiz Area via Javascript to maintain high speed and 30s precision -->
    <div id="quiz-panel" class="hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
        <div class="flex justify-between items-center border-b border-slate-100 pb-4">
            <span class="text-sm font-semibold text-slate-500">Savol: <span id="current-q-index" class="text-indigo-600 text-lg">1</span>/50</span>
            <div class="flex items-center space-x-2 bg-rose-50 text-rose-600 font-bold px-4 py-1.5 rounded-full">
                <i class="fas fa-clock animate-pulse"></i>
                <span id="timer">30</span> soniya
            </div>
        </div>
        <div id="quiz-question-text" class="text-lg font-medium text-slate-900 py-2">Yuklanmoqda...</div>
        <div id="quiz-options" class="grid grid-cols-1 gap-3"></div>
    </div>

    <div>
        <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Papkadagi barcha savollar to'liq ro'yxati</h3>
        <div class="grid grid-cols-1 gap-3">
            {% for q in sub_data.questions %}
            <div class="bg-white border border-slate-200 rounded-xl p-4 flex items-start space-x-3 shadow-2xs">
                <div class="bg-indigo-50 text-indigo-600 font-semibold px-2 py-0.5 rounded-sm text-xs mt-0.5">{{ loop.index }}</div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-slate-800 mb-2">{{ q.text }}</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-500">
                        {% for opt in q.options %}
                        <div class="{% if loop.index0 == q.correct %}text-emerald-600 font-semibold bg-emerald-50 px-2 py-1 rounded-sm{% else %}bg-slate-50 px-2 py-1 rounded-sm{% endif %}">✓ {{ opt }}</div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<form id="submit-result-form" action="{{ url_for('submit_result') }}" method="POST" class="hidden">
    <input type="hidden" name="subject_title" value="{{ sub_data.title }}">
    <input type="hidden" name="correct_count" id="form-correct-count">
</form>

<script>
    let questions = {{ questions_json | safe }};
    let activeQuiz = null;
    let timerInterval = None;

    function startQuizClient() {
        document.getElementById('quiz-panel').classList.remove('hidden');
        activeQuiz = { currentIndex: 0, correctCount: 0, timeLeft: 30 };
        loadQuestion();
    }

    function loadQuestion() {
        if(activeQuiz.currentIndex >= questions.length) {
            clearInterval(timerInterval);
            document.getElementById('form-correct-count').value = activeQuiz.correctCount;
            document.getElementById('submit-result-form').submit();
            return;
        }
        activeQuiz.timeLeft = 30;
        document.getElementById('timer').innerText = activeQuiz.timeLeft;
        
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            activeQuiz.timeLeft--;
            document.getElementById('timer').innerText = activeQuiz.timeLeft;
            if(activeQuiz.timeLeft <= 0) {
                activeQuiz.currentIndex++;
                loadQuestion();
            }
        }, 1000);

        let q = questions[activeQuiz.currentIndex];
        document.getElementById('current-q-index').innerText = activeQuiz.currentIndex + 1;
        document.getElementById('quiz-question-text').innerText = q.text;

        let optContainer = document.getElementById('quiz-options');
        optContainer.innerHTML = '';
        q.options.forEach((opt, idx) => {
            let btn = document.createElement('button');
            btn.className = "w-full text-left px-5 py-3 rounded-xl border border-slate-200 text-sm font-medium hover:bg-slate-50 transition-all";
            btn.innerText = opt;
            btn.onclick = () => {
                if(idx === q.correct) activeQuiz.correctCount++;
                activeQuiz.currentIndex++;
                loadQuestion();
            };
            optContainer.appendChild(btn);
        });
    }
</script>
{% endblock %}
'''

RESULTS_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <h2 class="text-xl font-bold text-slate-900 flex items-center space-x-2">
        <i class="fas fa-chart-line text-emerald-500"></i>
        <span>Sizning test yechish natijalaringiz (7-Papka)</span>
    </h2>
    <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                    <th class="p-4">Fan nomi</th>
                    <th class="p-4">Sana va Vaqt</th>
                    <th class="p-4">To'g'ri javoblar</th>
                    <th class="p-4">Foiz ko'rsatkichi</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-sm text-slate-600">
                {% for log in logs %}
                <tr class="hover:bg-slate-50/80 transition-all">
                    <td class="p-4 font-medium text-slate-900">{{ log.subjectTitle }}</td>
                    <td class="p-4 text-slate-400 text-xs">{{ log.date }}</td>
                    <td class="p-4 font-semibold text-slate-700">{{ log.score }}</td>
                    <td class="p-4"><span class="bg-emerald-50 text-emerald-600 font-bold px-2 py-0.5 rounded text-xs">{{ log.percent }}%</span></td>
                </tr>
                {% else %}
                <tr><td colspan="4" class="p-8 text-center text-slate-400">Hali hech qanday test topshirilmadi. Fanlardan testlarni bajaring.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
'''

NOTES_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <i class="fas fa-sticky-note text-sky-500"></i>
            <span>Shaxsiy Eslatmalar (Taking Notes)</span>
        </h2>
        <form action="{{ url_for('add_note') }}" method="POST" class="flex items-center space-x-2">
            <input type="text" name="note_text" required placeholder="Yangi eslatma yozing..." class="border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-hidden focus:ring-2 focus:ring-indigo-500 w-64 bg-white">
            <button type="submit" class="bg-sky-500 text-white font-medium text-sm px-4 py-2 rounded-xl flex items-center space-x-2 shadow-xs">
                <i class="fas fa-plus"></i> <span>Qo'shish</span>
            </button>
        </form>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {% for note in notes %}
        <div class="bg-amber-50 border border-amber-200 rounded-2xl p-5 shadow-2xs relative flex flex-col justify-between h-40">
            <p class="text-sm text-slate-700 font-medium line-clamp-4">{{ note.text }}</p>
            <div class="flex justify-between items-center mt-4 pt-2 border-t border-amber-200/60 text-xs text-slate-400">
                <span>{{ note.date }}</span>
                <a href="{{ url_for('delete_note', note_id=note.id) }}" class="text-rose-500"><i class="fas fa-trash"></i></a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
'''

SEARCH_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <h2 class="text-xl font-bold text-slate-900 flex items-center space-x-2">
        <i class="fas fa-search text-indigo-500"></i>
        <span>Qidiruv natijalari: "{{ query }}"</span>
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {% for res in results %}
        <a href="{{ url_for('subject_page', key=res.sub_key) }}" class="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-2 hover:border-indigo-400 block transition-all">
            <div class="flex justify-between items-center text-xs">
                <span class="font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-sm">{{ res.sub_title }}</span>
                <span class="text-slate-400">ID: {{ res.id }}</span>
            </div>
            <p class="text-sm font-medium text-slate-800 line-clamp-2">{{ res.text }}</p>
        </a>
        {% else %}
        <div class="col-span-full text-center py-12 text-slate-400 text-sm">Mos keladigan birorta savol topilmadi.</div>
        {% endfor %}
    </div>
</div>
{% endblock %}
'''

ADMIN_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <h2 class="text-2xl font-bold text-slate-900">Admin Boshqaruv Paneli</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
            <div class="text-slate-400 text-sm font-medium mb-1">Umumiy urinishlar soni</div>
            <div class="text-3xl font-bold text-slate-900">{{ total_attempts }} ta</div>
        </div>
        <div class="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
            <div class="text-slate-400 text-sm font-medium mb-1">O'rtacha o'zlashtirish</div>
            <div class="text-3xl font-bold text-emerald-500">{{ avg_percent }}%</div>
        </div>
        <div class="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
            <div class="text-slate-400 text-sm font-medium mb-1">Himoyalangan rejim</div>
            <div class="text-md font-bold text-indigo-600">In-Memory Active</div>
        </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div class="p-5 border-b border-slate-100 font-bold text-slate-800">Barcha talabalar yechgan testlar monitoringi</div>
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                    <th class="p-4">Vaqt</th>
                    <th class="p-4">Fan</th>
                    <th class="p-4">Yechilgan testlar</th>
                    <th class="p-4">Foiz</th>
                    <th class="p-4">Holat</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-sm text-slate-600">
                {% for log in logs %}
                <tr class="hover:bg-slate-50 transition-all">
                    <td class="p-4 text-xs text-slate-400">{{ log.date }}</td>
                    <td class="p-4 font-medium text-slate-900">{{ log.subjectTitle }}</td>
                    <td class="p-4">{{ log.score }} ta</td>
                    <td class="p-4 font-semibold text-indigo-600">{{ log.percent }}%</td>
                    <td class="p-4">
                        <span class="{% if log.percent >= 60 %}bg-emerald-100 text-emerald-700{% else %}bg-amber-100 text-amber-700{% endif %} text-xs px-2.5 py-1 rounded-full font-medium">
                            {% if log.percent >= 60 %}Muvaffaqiyatli{% else %}Qayta topshirish{% endif %}
                        </span>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="5" class="p-8 text-center text-slate-400">Hali hech kim test yechmadi.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
'''

@app.route('/')
def index():
    return redirect(url_for('subject_page', key='math'))

@app.route('/subject/<key>')
def subject_page(key):
    if key not in DATABASE:
        return redirect(url_for('index'))
    import json
    questions_json = json.dumps(DATABASE[key]['questions'])
    return render_template_string(BASE_TEMPLATE, content=render_template_string(SUBJECT_TEMPLATE, sub_data=DATABASE[key], questions_json=questions_json), db=DATABASE, active_tab=key, current_title=DATABASE[key]['title'], query_val="")

@app.route('/submit-result', methods=['POST'])
def submit_result():
    sub_title = request.form.get('subject_title')
    correct_count = int(request.form.get('correct_count', 0))
    percent = int((correct_count / 50) * 100)
    
    app._student_logs.insert(0, {
        "id": f"session_{int(datetime.now().timestamp())}",
        "subjectTitle": sub_title,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": f"{correct_count}/50",
        "percent": percent
    })
    return redirect(url_for('results_page'))

@app.route('/results')
def results_page():
    return render_template_string(BASE_TEMPLATE, content=render_template_string(RESULTS_TEMPLATE, logs=app._student_logs), db=DATABASE, active_tab='results', current_title="7-Papka: Natijalar", query_val="")

@app.route('/notes')
def notes_page():
    return render_template_string(BASE_TEMPLATE, content=render_template_string(NOTES_TEMPLATE, notes=app._student_notes), db=DATABASE, active_tab='notes', current_title="Eslatmalar", query_val="")

@app.route('/add-note', methods=['POST'])
def add_note():
    txt = request.form.get('note_text')
    if txt:
        app._student_notes.insert(0, {
            "id": int(datetime.now().timestamp()),
            "text": txt,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    return redirect(url_for('notes_page'))

@app.route('/delete-note/<int:note_id>')
def delete_note(note_id):
    app._student_notes = [n for n in app._student_notes if n['id'] != note_id]
    return redirect(url_for('notes_page'))

@app.route('/search')
def search_page():
    query = request.args.get('q', '').lower().strip()
    results = []
    if query:
        for sub_key, sub in DATABASE.items():
            for q in sub['questions']:
                if query in q['text'].lower() or query in sub['title'].lower():
                    results.append({
                        "sub_key": sub_key,
                        "sub_title": sub['title'],
                        "id": q['id'],
                        "text": q['text']
                    })
    return render_template_string(BASE_TEMPLATE, content=render_template_string(SEARCH_TEMPLATE, results=results, query=query), db=DATABASE, active_tab='', current_title="Qidiruv natijalari", query_val=query)

@app.route('/admin-login', methods=['POST'])
def admin_login():
    pwd = request.form.get('password')
    if pwd == ADMIN_PASSWORD:
        session['is_admin'] = True
    return redirect(request.referrer or url_for('index'))

@app.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin_page():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    total = len(app._student_logs)
    avg = int(sum(l['percent'] for l in app._student_logs) / total) if total > 0 else 0
    return render_template_string(BASE_TEMPLATE, content=render_template_string(ADMIN_TEMPLATE, logs=app._student_logs, total_attempts=total, avg_percent=avg), db=DATABASE, active_tab='admin', current_title="Admin Panel", query_val="")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
