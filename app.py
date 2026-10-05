import os
import secrets
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

ADMIN_PASSWORD = "1004"

# Savollarni tashqi yengil JSON fayldan yuklash
def load_db():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

DATABASE = load_db()
STUDENT_LOGS = []
STUDENT_NOTES = []

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <title>Talaba Portali</title>
    <script src="https://jsdelivr.net"></script>
    <link rel="stylesheet" href="https://cloudflare.com">
</head>
<body class="bg-slate-50 flex h-screen overflow-hidden text-slate-800">
    <aside class="w-80 bg-slate-900 text-white flex flex-col justify-between p-4 shadow-xl">
        <div>
            <div class="p-4 border-b border-slate-800 font-bold text-lg flex items-center space-x-2">
                <i class="fas fa-graduation-cap text-indigo-500"></i><span>Talaba Portali</span>
            </div>
            <div class="space-y-1 mt-4">
                {% for key, sub in db.items() %}
                <a href="{{ url_for('subject_page', key=key) }}" class="flex justify-between p-2 rounded-sm text-sm {% if active_tab == key %}bg-slate-800 text-white{% else %}text-slate-400 hover:bg-slate-800{% endif %}">
                    <span>{{ sub.title }}</span><span class="bg-slate-700 text-xs px-2 rounded-full">Test</span>
                </a>
                {% endfor %}
                <div class="border-t border-slate-800 my-2"></div>
                <a href="{{ url_for('results_page') }}" class="block p-2 text-sm text-emerald-400 hover:bg-slate-800 rounded-sm">7-Papka: Natijalar</a>
                <a href="{{ url_for('notes_page') }}" class="block p-2 text-sm text-sky-400 hover:bg-slate-800 rounded-sm">Eslatmalar (Notes)</a>
            </div>
        </div>
        <div class="border-t border-slate-800 pt-2">
            {% if session.get('is_admin') %}
                <a href="{{ url_for('admin_page') }}" class="block bg-indigo-600 text-white text-center py-2 rounded-sm text-sm">Admin Panel</a>
                <a href="{{ url_for('admin_logout') }}" class="block text-center text-xs text-rose-400 mt-1">Chiqish</a>
            {% else %}
                <button onclick="document.getElementById('admin-modal').classList.remove('hidden')" class="w-full bg-slate-800 py-2 rounded-sm text-sm">Admin Kirish</button>
            {% endif %}
        </div>
    </aside>
    <main class="flex-1 flex flex-col">
        <header class="bg-white border-b h-16 flex items-center justify-between px-6">
            <form action="{{ url_for('search_page') }}" method="GET" class="relative">
                <input type="text" name="q" placeholder="Qidiruv..." class="bg-slate-100 px-4 py-1.5 rounded-lg text-sm w-64 focus:outline-hidden">
            </form>
            <div class="text-sm font-semibold bg-slate-100 px-3 py-1 rounded-full">{{ current_title }}</div>
        </header>
        <div class="flex-1 overflow-y-auto p-6">{% block content %}{% endblock %}</div>
    </main>
    <div id="admin-modal" class="fixed inset-0 bg-slate-900/50 hidden items-center justify-center p-4">
        <form action="{{ url_for('admin_login') }}" method="POST" class="bg-white p-6 rounded-lg w-full max-w-sm space-y-4">
            <h3 class="font-bold text-center">Admin Kodini kiriting</h3>
            <input type="password" name="password" required class="w-full border p-2 text-center font-mono" placeholder="••••">
            <div class="flex space-x-2">
                <button type="button" onclick="document.getElementById('admin-modal').classList.add('hidden')" class="w-1/2 bg-slate-100 py-2 rounded-sm">Bekor qilish</button>
                <button type="submit" class="w-1/2 bg-indigo-600 text-white py-2 rounded-sm">Kirish</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

SUBJECT_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <div class="bg-indigo-600 rounded-xl p-6 text-white flex justify-between items-center shadow-md">
        <div>
            <h2 class="text-xl font-bold">{{ sub_data.title }}</h2>
            <p class="text-xs text-indigo-100 mt-1">Har bir savolga 30 soniya vaqt beriladi.</p>
        </div>
        <button onclick="startQuiz()" class="bg-white text-indigo-600 font-semibold px-4 py-2 rounded-lg text-sm shadow-sm">Testni Boshlash</button>
    </div>
    <div id="quiz-panel" class="hidden bg-white border rounded-xl p-6 space-y-4 shadow-xs">
        <div class="flex justify-between text-sm font-medium border-b pb-2">
            <span>Savol: <span id="q-idx" class="text-indigo-600 font-bold">1</span></span>
            <span class="text-rose-600 font-bold"><i class="fas fa-clock mr-1"></i><span id="timer">30</span>s</span>
        </div>
        <div id="q-text" class="font-medium text-lg text-slate-900"></div>
        <div id="q-opts" class="grid grid-cols-1 gap-2"></div>
    </div>
</div>
<form id="res-form" action="{{ url_for('submit_result') }}" method="POST" class="hidden">
    <input type="hidden" name="subject_title" value="{{ sub_data.title }}">
    <input type="hidden" name="correct_count" id="c-count">
</form>
<script>
    let questions = {{ questions_json | safe }};
    let idx = 0, correct = 0, timer = 30, interval = null;
    function startQuiz() { document.getElementById('quiz-panel').classList.remove('hidden'); idx=0; correct=0; showQ(); }
    function showQ() {
        if(idx >= questions.length) { clearInterval(interval); document.getElementById('c-count').value = correct; document.getElementById('res-form').submit(); return; }
        timer = 30; document.getElementById('timer').innerText = timer;
        clearInterval(interval);
        interval = setInterval(() => { timer--; document.getElementById('timer').innerText = timer; if(timer<=0) { idx++; showQ(); } }, 1000);
        let q = questions[idx];
        document.getElementById('q-idx').innerText = (idx + 1);
        document.getElementById('q-text').innerText = q.text;
        let container = document.getElementById('q-opts'); container.innerHTML = '';
        q.options.forEach((opt, oIdx) => {
            let btn = document.createElement('button');
            btn.className = "w-full text-left p-3 border rounded-xl text-sm hover:bg-slate-50 transition-all";
            btn.innerText = opt;
            btn.onclick = () => { if(oIdx === q.correct) correct++; idx++; showQ(); };
            container.appendChild(btn);
        });
    }
</script>
{% endblock %}
"""

RESULTS_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="space-y-4">
    <h2 class="text-lg font-bold text-slate-900">7-Papka: Natijalar</h2>
    <div class="bg-white border rounded-xl overflow-hidden shadow-xs">
        <table class="w-full text-left text-sm">
            <tr class="bg-slate-50 border-b text-xs text-slate-500 uppercase font-semibold"><th class="p-3">Fan</th><th class="p-3">Sana</th><th class="p-3">Natija</th><th class="p-3">Foiz</th></tr>
            {% for log in logs %}<tr class="border-b"><td class="p-3 font-medium">{{ log.subjectTitle }}</td><td class="p-3 text-xs text-slate-400">{{ log.date }}</td><td class="p-3">{{ log.score }}</td><td class="p-3 font-bold text-emerald-600">{{ log.percent }}%</td></tr>
            {% else %}<tr><td colspan="4" class="p-4 text-center text-slate-400">Hali natijalar yo'q.</td></tr>{% endfor %}
        </table>
    </div>
</div>
{% endblock %}
"""

NOTES_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="space-y-4">
    <div class="flex justify-between items-center">
        <h2 class="text-lg font-bold">Eslatmalar</h2>
        <form action="{{ url_for('add_note') }}" method="POST" class="flex space-x-2">
            <input type="text" name="note_text" required placeholder="Yangi qayd..." class="border px-3 py-1 text-sm rounded-lg">
            <button type="submit" class="bg-sky-500 text-white px-3 py-1 text-sm rounded-lg">+</button>
        </form>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {% for note in notes %}<div class="bg-amber-50 border border-amber-200 p-4 rounded-xl flex flex-col justify-between h-32"><p class="text-sm text-slate-700 font-medium">{{ note.text }}</p><div class="flex justify-between items-center text-xs text-slate-400 mt-2"><span>{{ note.date }}</span><a href="{{ url_for('delete_note', note_id=note.id) }}" class="text-rose-500"><i class="fas fa-trash"></i></a></div></div>{% endfor %}
    </div>
</div>
{% endblock %}
"""

SEARCH_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="space-y-4">
    <h2 class="text-lg font-bold">Qidiruv natijalari: "{{ query }}"</h2>
    <div class="grid grid-cols-1 gap-2">
        {% for res in results %}<a href="{{ url_for('subject_page', key=res.sub_key) }}" class="bg-white border p-4 rounded-xl block hover:border-indigo-500"><span class="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-sm mr-2 font-semibold">{{ res.sub_title }}</span><span class="text-sm text-slate-700 font-medium">{{ res.text }}</span></a>
        {% else %}<div class="text-slate-400 text-sm">Hech narsa topilmadi.</div>{% endfor %}
    </div>
</div>
{% endblock %}
"""

ADMIN_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="space-y-6">
    <h2 class="text-xl font-bold">Admin Panel (Monitoring)</h2>
    <div class="grid grid-cols-2 gap-4">
        <div class="bg-white border p-4 rounded-xl">
            <div class="text-xs text-slate-400">Umumiy urinishlar</div>
            <div class="text-2xl font-bold mt-1">{{ total_attempts }} ta</div>
        </div>
        <div class="bg-white border p-4 rounded-xl">
