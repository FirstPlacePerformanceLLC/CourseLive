import os
import json
import requests
import psycopg
from flask import Flask, request, session, jsonify, Response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "courselive_dev_secret")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "info@talklog.ai")
FROM_NAME = os.environ.get("FROM_NAME", "Dale Carnegie Nevada")
HOST_SECRET = os.environ.get("HOST_SECRET", "CARNEGIE")

NAVY = "#0f2942"
TEAL = "#0d9488"
GOLD = "#d4a017"

ROSTER = [
    (1, "Deiby", "Castiblanco", "Performance Contracting Group", "deiby.castiblanco@pcg.com"),
    (2, "Angie", "Castillo", "University of North Texas at Dallas", "angie.castillo@untdallas.edu"),
    (3, "Gabriel", "Smith", "Precision Resilience", "precision.resilience@gmail.com"),
    (4, "Joseph", "Margrave", "Veka West", "jmargrave@veka.com"),
    (5, "Ashley", "Easley", "Veka West", "aeasley@veka.com"),
    (6, "Anthony", "Patton", "Western Nevada Supply", "apatton@goblueteam.com"),
    (7, "John", "Westby", "Western Nevada Supply", "jwestby@goblueteam.com"),
]

QUESTIONS = [
    {
        "stem": "First morning of a job, you walk into a room of people you have not met. Your first move is to",
        "options": [
            {"t": "find whoever is running things and introduce yourself to them", "l": "D"},
            {"t": "work the room, learn names, get people smiling", "l": "I"},
            {"t": "find one or two people and have a real conversation", "l": "S"},
            {"t": "read the room first, then engage once you have a feel for it", "l": "C"},
        ],
    },
    {
        "stem": "A teammate hands you a plan. The first thing you notice is",
        "options": [
            {"t": "whether it moves fast enough to hit the goal", "l": "D"},
            {"t": "how the team is going to feel about it", "l": "I"},
            {"t": "whether it is realistic and can actually hold up", "l": "S"},
            {"t": "the one number or gap that does not add up", "l": "C"},
        ],
    },
    {
        "stem": "Under a tight deadline you",
        "options": [
            {"t": "make the call and drive it", "l": "D"},
            {"t": "rally the group and keep the energy up", "l": "I"},
            {"t": "put your head down and grind it out", "l": "S"},
            {"t": "get the facts straight so it is right the first time", "l": "C"},
        ],
    },
    {
        "stem": "People who know you would most likely call you",
        "options": [
            {"t": "driven and direct", "l": "D"},
            {"t": "warm and energizing", "l": "I"},
            {"t": "steady and dependable", "l": "S"},
            {"t": "sharp and thorough", "l": "C"},
        ],
    },
    {
        "stem": "In a disagreement your instinct is to",
        "options": [
            {"t": "state your position plainly and stand on it", "l": "D"},
            {"t": "find the common ground and keep it friendly", "l": "I"},
            {"t": "hear them out fully before you say anything", "l": "S"},
            {"t": "bring the evidence and let the facts settle it", "l": "C"},
        ],
    },
    {
        "stem": "The part of work that gives you the most energy is",
        "options": [
            {"t": "winning, hitting the target", "l": "D"},
            {"t": "the people, the connection", "l": "I"},
            {"t": "being the one who gets counted on", "l": "S"},
            {"t": "solving it right, mastering the detail", "l": "C"},
        ],
    },
    {
        "stem": "When you give someone feedback you tend to",
        "options": [
            {"t": "get to the point fast", "l": "D"},
            {"t": "lead with what they did well", "l": "I"},
            {"t": "pick your moment and say it gently", "l": "S"},
            {"t": "be specific and precise about what to fix", "l": "C"},
        ],
    },
    {
        "stem": "On a team, the role you slide into is",
        "options": [
            {"t": "the one who sets the direction", "l": "D"},
            {"t": "the one who lifts the mood", "l": "I"},
            {"t": "the one people rely on", "l": "S"},
            {"t": "the one who catches the mistakes", "l": "C"},
        ],
    },
    {
        "stem": "When something new and risky comes up, you",
        "options": [
            {"t": "go for it, decide fast", "l": "D"},
            {"t": "get excited and pull others in", "l": "I"},
            {"t": "want to know it is solid before you move", "l": "S"},
            {"t": "study it before you commit", "l": "C"},
        ],
    },
]

LEAN = {
    "D": {
        "name": "Dominance",
        "one": "You see the goal and you move.",
        "strength": "Your strength is drive and decisiveness. When the room stalls, you make the call.",
        "lead": "dramatizing your ideas and throwing down a challenge",
        "stretch": "being a good listener and showing respect for the other person's opinion. The driver who also listens is unstoppable.",
        "color": "#d4537e",
    },
    "I": {
        "name": "Influence",
        "one": "You bring the energy and win people over.",
        "strength": "Your strength is warmth. You make people feel good and pull them along with you.",
        "lead": "the smile, genuine interest in others, and honest sincere appreciation",
        "stretch": "getting the facts and weighing them before you commit. Your energy plus real evidence is a force.",
        "color": "#d4a017",
    },
    "S": {
        "name": "Steadiness",
        "one": "Steady, loyal, the one people count on.",
        "strength": "Your strength is dependability. You listen, you follow through, people trust you.",
        "lead": "being a good listener and seeing things from the other person's point of view",
        "stretch": "taking the risk and stating your opinion with evidence. The room needs to hear you.",
        "color": "#0d9488",
    },
    "C": {
        "name": "Conscientiousness",
        "one": "Precise, thorough, you get it right.",
        "strength": "Your strength is accuracy and depth. You catch what others miss.",
        "lead": "Evidence Defeats Doubt, you win with facts",
        "stretch": "giving honest appreciation and connecting first. Warmth makes your expertise land.",
        "color": "#378add",
    },
}

UPSELL = ("This is a quick lean, not the full picture. The complete validated DISC "
          "assessment goes deeper. Ask me about it after class.")


def get_conn():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roster (
                    id INTEGER PRIMARY KEY,
                    first TEXT NOT NULL,
                    last TEXT NOT NULL,
                    company TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    pid INTEGER PRIMARY KEY,
                    joined_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    pid INTEGER NOT NULL,
                    qnum INTEGER NOT NULL,
                    letter TEXT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT now(),
                    PRIMARY KEY (pid, qnum)
                )
            """)
            for rid, first, last, company, email in ROSTER:
                cur.execute("""
                    INSERT INTO roster (id, first, last, company, email)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET first = EXCLUDED.first,
                        last = EXCLUDED.last,
                        company = EXCLUDED.company,
                        email = EXCLUDED.email
                """, (rid, first, last, company, email))
        conn.commit()


def roster_row(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, first, last, company, email FROM roster WHERE id = %s", (pid,))
            return cur.fetchone()


def tally_for(pid):
    counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT letter FROM answers WHERE pid = %s", (pid,))
            for (letter,) in cur.fetchall():
                if letter in counts:
                    counts[letter] += 1
    return counts


def lean_from_counts(counts):
    answered = sum(counts.values())
    order = sorted(counts.items(), key=lambda kv: (-kv[1], "DISC".index(kv[0])))
    primary = order[0][0]
    blend = None
    if answered > 0 and order[0][1] == order[1][1]:
        blend = order[1][0]
    return primary, blend, answered


def plot_xy(counts):
    answered = sum(counts.values())
    if answered == 0:
        return 0.5, 0.5
    people = counts["I"] + counts["S"]
    fast = counts["D"] + counts["I"]
    return people / answered, fast / answered


def current_pid():
    return session.get("pid")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Your DISC Lean</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef2f5; font-family: Poppins, Arial, sans-serif; color: #0f2942; }
  .wrap { max-width: 480px; margin: 0 auto; min-height: 100vh; padding: 16px; }
  .card { background: #ffffff; border-radius: 18px; overflow: hidden; box-shadow: 0 2px 10px rgba(15,41,66,0.08); }
  .head { background: #0f2942; padding: 16px 18px; color: #fff; }
  .head h1 { font-size: 16px; font-weight: 600; margin: 0; }
  .head .sub { color: #9fe1cb; font-size: 12px; margin-top: 2px; }
  .bar { height: 5px; background: rgba(255,255,255,0.18); border-radius: 5px; margin-top: 12px; }
  .fill { height: 5px; background: #d4a017; border-radius: 5px; width: 0%; transition: width 0.3s; }
  .body { padding: 18px; }
  .stem { font-size: 17px; font-weight: 500; line-height: 1.5; margin: 0 0 16px; }
  .opt { border: 1px solid #d7dde3; border-radius: 12px; padding: 14px 15px; font-size: 15px; margin-bottom: 10px; cursor: pointer; line-height: 1.45; }
  .opt:active { background: #f4f6f8; }
  .name-btn { display: flex; justify-content: space-between; align-items: center; border: 1px solid #d7dde3; border-radius: 12px; padding: 14px 15px; margin-bottom: 10px; cursor: pointer; }
  .name-btn .nm { font-size: 16px; font-weight: 500; }
  .name-btn .co { font-size: 12px; color: #5f6b76; }
  .btn { width: 100%; background: #0d9488; color: #fff; border: none; border-radius: 12px; padding: 15px; font-size: 16px; font-weight: 500; font-family: inherit; cursor: pointer; }
  .btn.ghost { background: #fff; color: #0f2942; border: 1px solid #d7dde3; margin-top: 10px; }
  .btn.gold { background: #d4a017; color: #3d2c00; }
  .center { text-align: center; }
  .avatar { width: 70px; height: 70px; border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 600; color: #fff; }
  .lean-one { font-size: 15px; line-height: 1.5; margin: 0 0 14px; }
  .box { border-radius: 12px; padding: 13px 14px; margin-bottom: 10px; text-align: left; }
  .box .lbl { font-size: 12px; font-weight: 600; margin: 0 0 3px; }
  .box .txt { font-size: 14px; margin: 0; line-height: 1.45; }
  .foot { font-size: 12px; color: #5f6b76; line-height: 1.5; border-top: 1px solid #e6ebef; padding-top: 12px; margin-top: 4px; }
  .note { font-size: 12px; color: #5f6b76; margin-top: 12px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="head">
      <h1>Your DISC Lean</h1>
      <div class="sub" id="sub">Dale Carnegie Course, Reno</div>
      <div class="bar"><div class="fill" id="fill"></div></div>
    </div>
    <div class="body" id="body"></div>
  </div>
</div>
<script>
var QUESTIONS = __QUESTIONS__;
var LEAN = __LEAN__;
var UPSELL = __UPSELL__;
var state = "pick";
var qi = 0;
var picked = null;

function esc(s){ var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function el(id){ return document.getElementById(id); }
function setBar(pct){ el("fill").style.width = pct + "%"; }
function shuffle(a){ a = a.slice(); for (var i=a.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=a[i]; a[i]=a[j]; a[j]=t; } return a; }

function api(path, body){
  return fetch(path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body || {})
  }).then(function(r){ return r.json(); });
}

function renderPick(){
  setBar(0);
  el("sub").textContent = "Tap your name to begin";
  fetch("/roster").then(function(r){ return r.json(); }).then(function(list){
    var h = '<p class="stem">Who are you?</p>';
    list.forEach(function(p){
      h += '<div class="name-btn" onclick="choose(' + p.id + ')">' +
           '<span class="nm">' + esc(p.name) + '</span>' +
           '<span class="co">' + esc(p.company) + '</span></div>';
    });
    el("body").innerHTML = h;
  });
}

function choose(id){
  fetch("/roster").then(function(r){ return r.json(); }).then(function(list){
    var p = list.filter(function(x){ return x.id === id; })[0];
    picked = p;
    el("sub").textContent = "Confirm";
    el("body").innerHTML =
      '<p class="stem">Is this you?</p>' +
      '<div class="name-btn"><span class="nm">' + esc(p.name) + '</span>' +
      '<span class="co">' + esc(p.company) + '</span></div>' +
      '<button class="btn" onclick="confirmPick(' + id + ')">Yes, that is me</button>' +
      '<button class="btn ghost" onclick="renderPick()">No, go back</button>';
  });
}

function confirmPick(id){
  api("/pick", {pid: id}).then(function(res){
    if (res.ok){ qi = 0; state = "quiz"; renderQuestion(); }
  });
}

function renderQuestion(){
  var q = QUESTIONS[qi];
  el("sub").textContent = "Question " + (qi+1) + " of " + QUESTIONS.length;
  setBar(Math.round((qi) / QUESTIONS.length * 100));
  var opts = shuffle(q.options);
  var h = '<p class="stem">' + esc(q.stem) + '</p>';
  opts.forEach(function(o){
    h += '<div class="opt" onclick="answer(\\'' + o.l + '\\')">' + esc(o.t) + '</div>';
  });
  el("body").innerHTML = h;
}

function answer(letter){
  api("/answer", {qnum: qi, letter: letter}).then(function(){
    qi += 1;
    if (qi >= QUESTIONS.length){ loadResult(); }
    else { renderQuestion(); }
  });
}

function loadResult(){
  setBar(100);
  el("sub").textContent = "Your result";
  fetch("/result").then(function(r){ return r.json(); }).then(function(res){
    renderResult(res);
  });
}

function renderResult(res){
  var d = LEAN[res.primary];
  var headline = d.name;
  var leanLine = "you are leaning toward";
  if (res.blend){
    headline = d.name + " and " + LEAN[res.blend].name;
    leanLine = "you are a blend of";
  }
  var h = '<div class="center">' +
    '<div class="avatar" style="background:' + d.color + '">' + esc(res.primary) + '</div>' +
    '<p style="font-size:12px;color:' + d.color + ';margin:0 0 2px">' + leanLine + '</p>' +
    '<p style="font-size:20px;font-weight:600;margin:0 0 14px">' + esc(headline) + '</p>' +
    '</div>' +
    '<p class="lean-one">' + esc(d.one) + '</p>' +
    '<div class="box" style="background:#e1f5ee"><p class="lbl" style="color:#0d9488">You lead with</p>' +
    '<p class="txt" style="color:#0f6e56">' + esc(d.lead) + '</p></div>' +
    '<div class="box" style="background:#faeeda"><p class="lbl" style="color:#854f0b">Your stretch</p>' +
    '<p class="txt" style="color:#633806">' + esc(d.stretch) + '</p></div>' +
    '<button class="btn gold" id="emailbtn" onclick="emailMe()">Email me my result</button>' +
    '<p class="foot">' + esc(UPSELL) + '</p>';
  el("body").innerHTML = h;
}

function emailMe(){
  var b = el("emailbtn");
  b.textContent = "Sending...";
  api("/email_me", {}).then(function(res){
    if (res.ok){ b.textContent = "Sent to your inbox"; b.style.background = "#0d9488"; b.style.color = "#fff"; }
    else { b.textContent = "Could not send, try again"; }
  }).catch(function(){ b.textContent = "Could not send, try again"; });
}

renderPick();
</script>
</body>
</html>
"""

HOST_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your DISC Lean, the stage</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef2f5; font-family: Poppins, Arial, sans-serif; color: #0f2942; }
  .wrap { max-width: 900px; margin: 0 auto; padding: 18px; }
  .stage { background: #f4f6f8; border-radius: 14px; overflow: hidden; box-shadow: 0 2px 12px rgba(15,41,66,0.1); }
  .head { background: #0f2942; padding: 14px 22px; display: flex; align-items: center; justify-content: space-between; }
  .head .ttl { color: #fff; font-size: 18px; font-weight: 600; }
  .head .cnt { color: #9fe1cb; font-size: 13px; }
  .plot { padding: 10px 14px 16px; }
  .tools { display: flex; gap: 10px; margin-top: 14px; }
  .tbtn { background: #fff; color: #0f2942; border: 1px solid #d7dde3; border-radius: 10px; padding: 10px 16px; font-size: 13px; font-family: inherit; cursor: pointer; }
</style>
</head>
<body>
<div class="wrap">
  <div class="stage">
    <div class="head"><span class="ttl">Where the room lands</span><span class="cnt" id="cnt">0 of 7 in</span></div>
    <div class="plot"><div id="plotwrap"></div></div>
  </div>
  <div class="tools">
    <button class="tbtn" onclick="clearAll()">Clear all responses</button>
  </div>
</div>
<script>
var SECRET = "__SECRET__";
var GL = 120, GR = 600, GT = 70, GB = 430;

function esc(s){ var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function quadrants(){
  return '' +
    '<rect x="120" y="70" width="240" height="180" fill="#fbeef0"/>' +
    '<rect x="360" y="70" width="240" height="180" fill="#faeeda"/>' +
    '<rect x="120" y="250" width="240" height="180" fill="#e6f1fb"/>' +
    '<rect x="360" y="250" width="240" height="180" fill="#e1f5ee"/>' +
    '<text x="132" y="92" fill="#993556" font-size="15" font-weight="600">D  Dominance</text>' +
    '<text x="132" y="110" fill="#72243e" font-size="11">fast and task</text>' +
    '<text x="588" y="92" fill="#854f0b" font-size="15" font-weight="600" text-anchor="end">Influence  I</text>' +
    '<text x="588" y="110" fill="#633806" font-size="11" text-anchor="end">fast and people</text>' +
    '<text x="132" y="418" fill="#185fa5" font-size="15" font-weight="600">C  Conscientiousness</text>' +
    '<text x="132" y="400" fill="#0c447c" font-size="11">measured and task</text>' +
    '<text x="588" y="418" fill="#0f6e56" font-size="15" font-weight="600" text-anchor="end">Steadiness  S</text>' +
    '<text x="588" y="400" fill="#085041" font-size="11" text-anchor="end">measured and people</text>' +
    '<line x1="120" y1="250" x2="600" y2="250" stroke="#0f2942" stroke-width="1.5"/>' +
    '<line x1="360" y1="70" x2="360" y2="430" stroke="#0f2942" stroke-width="1.5"/>' +
    '<text x="360" y="58" fill="#5f6b76" font-size="11" text-anchor="middle">Fast, outgoing</text>' +
    '<text x="360" y="450" fill="#5f6b76" font-size="11" text-anchor="middle">Measured, reserved</text>';
}

function draw(data){
  el_cnt(data);
  var dots = "";
  data.people.forEach(function(p){
    if (!p.answered) return;
    var cx = GL + p.x * (GR - GL);
    var cy = GB - p.y * (GB - GT);
    var op = p.done ? "1" : "0.45";
    dots += '<g opacity="' + op + '">' +
      '<circle cx="' + cx.toFixed(0) + '" cy="' + cy.toFixed(0) + '" r="9" fill="' + p.color + '" stroke="#ffffff" stroke-width="2"/>' +
      '<text x="' + cx.toFixed(0) + '" y="' + (cy-13).toFixed(0) + '" text-anchor="middle" font-size="12" font-weight="500" fill="#0f2942">' + esc(p.first) + '</text>' +
      '</g>';
  });
  var svg = '<svg viewBox="0 0 680 470" width="100%">' + quadrants() + dots + '</svg>';
  document.getElementById("plotwrap").innerHTML = svg;
}

function el_cnt(data){
  var done = data.people.filter(function(p){ return p.done; }).length;
  document.getElementById("cnt").textContent = done + " of " + data.people.length + " in";
}

function poll(){
  fetch("/host/" + SECRET + "/data").then(function(r){ return r.json(); }).then(draw).catch(function(){});
}

function clearAll(){
  if (!confirm("Clear all responses and reset the room?")) return;
  fetch("/host/" + SECRET + "/clear", {method:"POST"}).then(function(){ poll(); });
}

poll();
setInterval(poll, 2500);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    init_db()
    html = PAGE.replace("__QUESTIONS__", json.dumps(QUESTIONS))
    html = html.replace("__LEAN__", json.dumps(LEAN))
    html = html.replace("__UPSELL__", json.dumps(UPSELL))
    return Response(html, mimetype="text/html")


@app.route("/roster")
def roster():
    init_db()
    out = []
    for rid, first, last, company, email in ROSTER:
        out.append({"id": rid, "name": first + " " + last, "company": company})
    return jsonify(out)


@app.route("/pick", methods=["POST"])
def pick():
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    valid = [r[0] for r in ROSTER]
    if pid not in valid:
        return jsonify({"ok": False})
    session["pid"] = pid
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO participants (pid) VALUES (%s)
                ON CONFLICT (pid) DO NOTHING
            """, (pid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/answer", methods=["POST"])
def answer():
    pid = current_pid()
    if not pid:
        return jsonify({"ok": False})
    data = request.get_json(silent=True) or {}
    qnum = data.get("qnum")
    letter = data.get("letter")
    if letter not in ("D", "I", "S", "C"):
        return jsonify({"ok": False})
    if not isinstance(qnum, int) or qnum < 0 or qnum >= len(QUESTIONS):
        return jsonify({"ok": False})
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO answers (pid, qnum, letter) VALUES (%s, %s, %s)
                ON CONFLICT (pid, qnum) DO UPDATE
                SET letter = EXCLUDED.letter, updated_at = now()
            """, (pid, qnum, letter))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/result")
def result():
    pid = current_pid()
    if not pid:
        return jsonify({"ok": False})
    counts = tally_for(pid)
    primary, blend, answered = lean_from_counts(counts)
    return jsonify({"ok": True, "primary": primary, "blend": blend,
                    "counts": counts, "answered": answered})


def send_result_email(to_email, to_name, primary, blend):
    if not SENDGRID_API_KEY:
        return {"ok": False, "status": "skipped"}
    d = LEAN[primary]
    headline = d["name"]
    lead_line = "You are leaning toward " + d["name"] + "."
    if blend:
        headline = d["name"] + " and " + LEAN[blend]["name"]
        lead_line = "You are a blend of " + headline + "."
    html = (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#0f2942">'
        '<div style="background:#0f2942;padding:20px;border-radius:12px 12px 0 0">'
        '<div style="color:#ffffff;font-size:18px;font-weight:bold">Your DISC Lean</div>'
        '<div style="color:#9fe1cb;font-size:13px">Dale Carnegie Course, Reno</div></div>'
        '<div style="border:1px solid #e6ebef;border-top:none;border-radius:0 0 12px 12px;padding:22px">'
        '<p style="font-size:16px;margin:0 0 4px"><strong>' + lead_line + '</strong></p>'
        '<p style="font-size:15px;line-height:1.5;margin:0 0 16px">' + d["strength"] + " " + d["one"] + '</p>'
        '<div style="background:#e1f5ee;border-radius:10px;padding:12px 14px;margin-bottom:10px">'
        '<div style="font-size:12px;font-weight:bold;color:#0d9488">You lead with</div>'
        '<div style="font-size:14px;color:#0f6e56">' + d["lead"] + '</div></div>'
        '<div style="background:#faeeda;border-radius:10px;padding:12px 14px;margin-bottom:16px">'
        '<div style="font-size:12px;font-weight:bold;color:#854f0b">Your stretch</div>'
        '<div style="font-size:14px;color:#633806">' + d["stretch"] + '</div></div>'
        '<p style="font-size:12px;color:#5f6b76;line-height:1.5;border-top:1px solid #e6ebef;padding-top:12px">'
        + UPSELL + '</p></div></div>'
    )
    payload = {
        "personalizations": [{"to": [{"email": to_email, "name": to_name}]}],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": "Your DISC lean from the Dale Carnegie Course",
        "content": [{"type": "text/html", "value": html}],
    }
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": "Bearer " + SENDGRID_API_KEY,
                     "Content-Type": "application/json"},
            json=payload, timeout=15,
        )
        ok = 200 <= resp.status_code < 300
        return {"ok": ok, "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "status": "error", "detail": str(e)}


@app.route("/email_me", methods=["POST"])
def email_me():
    pid = current_pid()
    if not pid:
        return jsonify({"ok": False})
    row = roster_row(pid)
    if not row:
        return jsonify({"ok": False})
    rid, first, last, company, email = row
    counts = tally_for(pid)
    primary, blend, answered = lean_from_counts(counts)
    if answered == 0:
        return jsonify({"ok": False})
    res = send_result_email(email, first + " " + last, primary, blend)
    return jsonify({"ok": bool(res.get("ok"))})


@app.route("/host/<secret>")
def host(secret):
    if secret != HOST_SECRET:
        return Response("Not found", status=404)
    init_db()
    html = HOST_PAGE.replace("__SECRET__", HOST_SECRET)
    return Response(html, mimetype="text/html")


@app.route("/host/<secret>/data")
def host_data(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    people = []
    for rid, first, last, company, email in ROSTER:
        counts = tally_for(rid)
        answered = sum(counts.values())
        primary, blend, _ = lean_from_counts(counts)
        x, y = plot_xy(counts)
        people.append({
            "id": rid, "first": first, "answered": answered,
            "done": answered >= len(QUESTIONS),
            "x": x, "y": y, "color": LEAN[primary]["color"],
        })
    return jsonify({"people": people})


@app.route("/host/<secret>/clear", methods=["POST"])
def host_clear(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM answers")
            cur.execute("DELETE FROM participants")
        conn.commit()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
