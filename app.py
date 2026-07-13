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
PREVIEW_EMAIL = os.environ.get("PREVIEW_EMAIL", FROM_EMAIL)

PREVIEW_PID = 0

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

ROSTER_IDS = [r[0] for r in ROSTER]

# ---------------------------------------------------------------------------
# Spot registry. The full three day course mapped to the app. Only spots
# flagged live are wired this build. The rest render a holding screen and
# appear in the admin selector marked coming, so each future build only flips
# one from coming to live.
# ---------------------------------------------------------------------------
SPOTS = [
    {"key": "who_next", "day": 0, "title": "Who's Next", "anchor": "Random name picker, all three days", "live": False},
    {"key": "bingo", "day": 0, "title": "Principle Bingo", "anchor": "All 30 Human Relations Principles", "live": False},
    {"key": "rollcall", "day": 1, "title": "Roll Call", "anchor": "1A Build a Foundation, Five Drivers of Success", "live": True},
    {"key": "namegame", "day": 1, "title": "Name Game", "anchor": "1B Recall and Use Names, Pause Part Punch", "live": False},
    {"key": "pegquiz", "day": 1, "title": "Peg Quiz", "anchor": "1C Peg Words 1 to 9", "live": False},
    {"key": "breakthrough", "day": 1, "title": "Breakthrough Board", "anchor": "1C Commit to Enhance Relationships", "live": False},
    {"key": "principledraw", "day": 2, "title": "Principle Draw", "anchor": "Day 2 principle assignments", "live": False},
    {"key": "clearcloudy", "day": 2, "title": "Clear or Cloudy", "anchor": "2B Make Our Ideas Clear, Magic Formula", "live": False},
    {"key": "energizer", "day": 2, "title": "Energizer", "anchor": "2C Energize Our Communications", "live": False},
    {"key": "worryvault", "day": 2, "title": "Worry Vault", "anchor": "2D Put Stress in Perspective", "live": False},
    {"key": "jeopardy", "day": 3, "title": "Jeopardy", "anchor": "3A Gain Willing Cooperation review", "live": False},
    {"key": "taketheturn", "day": 3, "title": "Take the Turn", "anchor": "3B Disagree Agreeably, the Cushion", "live": False},
    {"key": "disc", "day": 3, "title": "Your DISC Lean", "anchor": "3C Develop More Flexibility, How People View Us", "live": True},
    {"key": "recognition", "day": 3, "title": "Recognition Wall", "anchor": "3D Build Others Through Recognition", "live": False},
]

SPOT_BY_KEY = {s["key"]: s for s in SPOTS}
DEFAULT_ACTIVE = "disc"

# Roll Call, the Five Drivers for Success, grounded in the instructor manual.
DRIVERS = [
    {"key": "confidence", "label": "Build greater self confidence"},
    {"key": "people", "label": "Strengthen people skills"},
    {"key": "communication", "label": "Enhance communication skills"},
    {"key": "leadership", "label": "Develop leadership skills"},
    {"key": "attitude", "label": "Reduce stress and improve attitude"},
]
DRIVER_KEYS = [d["key"] for d in DRIVERS]
DRIVER_LABEL = {d["key"]: d["label"] for d in DRIVERS}

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    pid INTEGER NOT NULL,
                    spot_key TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT now(),
                    PRIMARY KEY (pid, spot_key)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY,
                    active_spot TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spot_state (
                    spot_key TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'open'
                )
            """)
            cur.execute("""
                INSERT INTO app_state (id, active_spot) VALUES (1, %s)
                ON CONFLICT (id) DO NOTHING
            """, (DEFAULT_ACTIVE,))
            for s in SPOTS:
                cur.execute("""
                    INSERT INTO spot_state (spot_key, status) VALUES (%s, 'open')
                    ON CONFLICT (spot_key) DO NOTHING
                """, (s["key"],))
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


# ---------------------------------------------------------------------------
# Active spot and status helpers
# ---------------------------------------------------------------------------
def get_active_spot():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT active_spot FROM app_state WHERE id = 1")
            row = cur.fetchone()
            return row[0] if row else DEFAULT_ACTIVE


def set_active_spot(key):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE app_state SET active_spot = %s WHERE id = 1", (key,))
        conn.commit()


def get_spot_status(key):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM spot_state WHERE spot_key = %s", (key,))
            row = cur.fetchone()
            return row[0] if row else "open"


def set_spot_status(key, status):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO spot_state (spot_key, status) VALUES (%s, %s)
                ON CONFLICT (spot_key) DO UPDATE SET status = EXCLUDED.status
            """, (key, status))
        conn.commit()


def spot_is_live(key):
    s = SPOT_BY_KEY.get(key)
    return bool(s and s["live"])


# ---------------------------------------------------------------------------
# Identity. pid 0 is the reserved PREVIEW identity, never a roster name.
# ---------------------------------------------------------------------------
def roster_row(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, first, last, company, email FROM roster WHERE id = %s", (pid,))
            return cur.fetchone()


def identity_for(pid):
    if pid == PREVIEW_PID:
        return (PREVIEW_PID, "Preview", "", "Preview run", PREVIEW_EMAIL)
    return roster_row(pid)


def joined_pid():
    pid = session.get("pid")
    if pid == PREVIEW_PID:
        return PREVIEW_PID
    if pid in ROSTER_IDS:
        return pid
    return None


# ---------------------------------------------------------------------------
# DISC scoring and plot, unchanged and unit tested
# ---------------------------------------------------------------------------
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


def disc_answers_for(pid):
    out = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT qnum, letter FROM answers WHERE pid = %s ORDER BY qnum", (pid,))
            for qnum, letter in cur.fetchall():
                out.append({"q": qnum, "letter": letter})
    return out


# ---------------------------------------------------------------------------
# Generic response helpers for poll style spots (Roll Call)
# ---------------------------------------------------------------------------
def save_response(pid, spot_key, payload):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO responses (pid, spot_key, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (pid, spot_key) DO UPDATE
                SET payload = EXCLUDED.payload, updated_at = now()
            """, (pid, spot_key, json.dumps(payload)))
        conn.commit()


def get_response(pid, spot_key):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT payload FROM responses WHERE pid = %s AND spot_key = %s", (pid, spot_key))
            row = cur.fetchone()
            if not row:
                return None
            val = row[0]
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return None
            return val


def rollcall_tally():
    counts = {d["key"]: 0 for d in DRIVERS}
    for rid in ROSTER_IDS:
        r = get_response(rid, "rollcall")
        if r and r.get("driver") in counts:
            counts[r["driver"]] += 1
    return [{"key": d["key"], "label": d["label"], "count": counts[d["key"]]} for d in DRIVERS]


def current_pid():
    return session.get("pid")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>CourseLive</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef2f5; font-family: Poppins, Arial, sans-serif; color: #0f2942; }
  .wrap { max-width: 480px; margin: 0 auto; min-height: 100vh; padding: 16px; }
  .ribbon { background: #d4a017; color: #3d2c00; text-align: center; font-size: 12px; font-weight: 600; border-radius: 10px; padding: 6px; margin-bottom: 10px; }
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
  .note { font-size: 13px; color: #5f6b76; margin-top: 12px; line-height: 1.5; }
  .hold { text-align: center; padding: 20px 6px; }
  .hold .big { font-size: 20px; font-weight: 600; margin: 6px 0 8px; }
  .hold .small { font-size: 14px; color: #5f6b76; line-height: 1.5; }
  .tag { display: inline-block; font-size: 11px; font-weight: 600; color: #0d6e63; background: #e1f5ee; border-radius: 999px; padding: 3px 10px; margin-bottom: 6px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="ribbon" id="ribbon" style="display:none">PREVIEW MODE, this run is not counted</div>
  <div class="card">
    <div class="head">
      <h1 id="title">CourseLive</h1>
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
var DRIVERS = __DRIVERS__;
var SPOT_TITLES = __SPOT_TITLES__;
var IS_PREVIEW = __PREVIEW__;

var joined = IS_PREVIEW;
var renderedKey = null;
var qi = 0;

function esc(s){ var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function el(id){ return document.getElementById(id); }
function setBar(pct){ el("fill").style.width = pct + "%"; }
function setTitle(t){ el("title").textContent = t; }
function shuffle(a){ a = a.slice(); for (var i=a.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=a[i]; a[i]=a[j]; a[j]=t; } return a; }

function api(path, body){
  return fetch(path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body || {})
  }).then(function(r){ return r.json(); });
}

// ----- join by name -----
function renderPick(){
  setBar(0);
  setTitle("CourseLive");
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
    if (res.ok){ joined = true; renderedKey = null; tick(); }
  });
}

// ----- lobby, follows the active spot -----
function tick(){
  if (!joined){ return; }
  fetch("/state").then(function(r){ return r.json(); }).then(function(st){
    if (st.active !== renderedKey){
      renderedKey = st.active;
      renderSpot(st.active);
    }
  }).catch(function(){});
}

function renderSpot(key){
  if (key === "disc"){ startDisc(); return; }
  if (key === "rollcall"){ startRollcall(); return; }
  renderHold(key);
}

function renderHold(key){
  setBar(0);
  var title = SPOT_TITLES[key] || "CourseLive";
  setTitle("CourseLive");
  el("sub").textContent = "Please wait";
  el("body").innerHTML =
    '<div class="hold">' +
    '<span class="tag">NEXT UP</span>' +
    '<p class="big">' + esc(title) + '</p>' +
    '<p class="small">We will do this one together. Watch the main screen, your phone will follow along.</p>' +
    '</div>';
}

// ----- Roll Call -----
function startRollcall(){
  setTitle("Roll Call");
  setBar(0);
  el("sub").textContent = "One tap";
  fetch("/spot/rollcall/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && mine.driver){ rollcallDone(mine.driver); return; }
    var h = '<p class="stem">Which of the Five Drivers for Success do you most want to grow?</p>';
    DRIVERS.forEach(function(d){
      h += '<div class="opt" onclick="pickDriver(\\'' + d.key + '\\')">' + esc(d.label) + '</div>';
    });
    el("body").innerHTML = h;
  });
}

function pickDriver(k){
  api("/spot/rollcall/submit", {driver: k}).then(function(res){
    if (res.ok){ rollcallDone(k); }
  });
}

function rollcallDone(k){
  setBar(100);
  el("sub").textContent = "Logged";
  var label = "";
  DRIVERS.forEach(function(d){ if (d.key === k){ label = d.label; } });
  el("body").innerHTML =
    '<div class="hold">' +
    '<span class="tag">YOUR DRIVER</span>' +
    '<p class="big">' + esc(label) + '</p>' +
    '<p class="small">Great choice. We will grow this over the three days. Watch the main screen.</p>' +
    '</div>';
}

// ----- DISC -----
function startDisc(){
  setTitle("Your DISC Lean");
  fetch("/result").then(function(r){ return r.json(); }).then(function(res){
    if (res.ok && res.answered >= QUESTIONS.length){ renderResult(res); return; }
    qi = res.ok ? res.answered : 0;
    renderQuestion();
  }).catch(function(){ qi = 0; renderQuestion(); });
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
  api("/answer", {qnum: qi, letter: letter}).then(function(res){
    if (res && res.ok === false && res.locked){ el("sub").textContent = "Closed for now"; return; }
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
  setBar(100);
  el("sub").textContent = "Your result";
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

// ----- boot -----
if (IS_PREVIEW){ el("ribbon").style.display = "block"; }
if (joined){ tick(); } else { renderPick(); }
setInterval(function(){ if (joined){ tick(); } }, 2500);
</script>
</body>
</html>
"""

HOST_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CourseLive, the stage</title>
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
  .tally { padding: 18px 22px 24px; }
  .trow { margin-bottom: 14px; }
  .trow .tl { font-size: 15px; font-weight: 500; margin-bottom: 5px; display: flex; justify-content: space-between; }
  .track { height: 20px; background: #e6ebef; border-radius: 6px; overflow: hidden; }
  .tf { height: 20px; background: #0d9488; border-radius: 6px; width: 0%; transition: width 0.4s; }
  .nextup { padding: 40px 22px; text-align: center; }
  .nextup .lab { font-size: 13px; font-weight: 600; letter-spacing: 1px; color: #0d6e63; }
  .nextup .big { font-size: 30px; font-weight: 600; margin: 10px 0 6px; }
  .nextup .an { font-size: 14px; color: #5f6b76; }
  .tools { display: flex; gap: 10px; margin-top: 14px; }
  .tbtn { background: #fff; color: #0f2942; border: 1px solid #d7dde3; border-radius: 10px; padding: 10px 16px; font-size: 13px; font-family: inherit; cursor: pointer; }
  a.link { color: #0d6e63; font-size: 13px; text-decoration: none; margin-left: auto; align-self: center; }
</style>
</head>
<body>
<div class="wrap">
  <div class="stage">
    <div class="head"><span class="ttl" id="stitle">CourseLive</span><span class="cnt" id="cnt"></span></div>
    <div id="stagebody"></div>
  </div>
  <div class="tools">
    <button class="tbtn" onclick="clearAll()">Clear all responses</button>
    <a class="link" href="/host/__SECRET__/admin">Open the admin console</a>
  </div>
</div>
<script>
var SECRET = "__SECRET__";
var GL = 120, GR = 600, GT = 70, GB = 430;

function esc(s){ var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function byid(id){ return document.getElementById(id); }

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

function drawPlot(data){
  var done = data.people.filter(function(p){ return p.done; }).length;
  byid("cnt").textContent = done + " of " + data.people.length + " in";
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
  var svg = '<div class="plot"><svg viewBox="0 0 680 470" width="100%">' + quadrants() + dots + '</svg></div>';
  byid("stagebody").innerHTML = svg;
}

function drawTally(data){
  var total = 0;
  data.rollcall.forEach(function(t){ total += t.count; });
  byid("cnt").textContent = total + " of 7 in";
  var max = 1;
  data.rollcall.forEach(function(t){ if (t.count > max){ max = t.count; } });
  var h = '<div class="tally">';
  data.rollcall.forEach(function(t){
    var pct = Math.round(t.count / max * 100);
    h += '<div class="trow"><div class="tl"><span>' + esc(t.label) + '</span><span>' + t.count + '</span></div>' +
         '<div class="track"><div class="tf" style="width:' + pct + '%"></div></div></div>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function drawNext(data){
  byid("cnt").textContent = "";
  byid("stagebody").innerHTML =
    '<div class="nextup"><div class="lab">NEXT UP</div>' +
    '<div class="big">' + esc(data.title) + '</div>' +
    '<div class="an">' + esc(data.anchor || "") + '</div></div>';
}

function draw(data){
  byid("stitle").textContent = data.title;
  if (data.active === "disc"){ drawPlot(data); }
  else if (data.active === "rollcall"){ drawTally(data); }
  else { drawNext(data); }
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

ADMIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CourseLive admin</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef2f5; font-family: Poppins, Arial, sans-serif; color: #0f2942; }
  .wrap { max-width: 960px; margin: 0 auto; padding: 18px; }
  h2 { font-size: 15px; font-weight: 600; margin: 22px 0 10px; }
  .panel { background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(15,41,66,0.08); padding: 14px 16px; }
  .top { background: #0f2942; color: #fff; border-radius: 12px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; }
  .top .t1 { font-size: 17px; font-weight: 600; }
  .top .t2 { font-size: 13px; color: #9fe1cb; }
  .spotgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
  .spot { border: 1px solid #d7dde3; border-radius: 10px; padding: 9px 11px; cursor: pointer; }
  .spot.active { border-color: #0d9488; background: #e1f5ee; }
  .spot.coming { opacity: 0.55; }
  .spot .sk { font-size: 13px; font-weight: 500; }
  .spot .sd { font-size: 11px; color: #5f6b76; }
  .spot .sc { font-size: 10px; color: #b26a00; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 8px; border-bottom: 1px solid #eef2f5; vertical-align: top; }
  th { font-size: 11px; text-transform: uppercase; color: #5f6b76; letter-spacing: 0.5px; }
  .pill { display: inline-block; font-size: 11px; border-radius: 999px; padding: 2px 9px; font-weight: 600; }
  .pill.in { background: #e1f5ee; color: #0d6e63; }
  .pill.out { background: #eef2f5; color: #8a97a3; }
  .mini { background: #fff; color: #0f2942; border: 1px solid #d7dde3; border-radius: 8px; padding: 5px 10px; font-size: 12px; font-family: inherit; cursor: pointer; }
  .mini.warn { color: #993556; border-color: #e3b8c4; }
  .row2 { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
  .statusline { font-size: 12px; color: #5f6b76; margin-top: 8px; }
  .toggle { font-size: 12px; font-family: inherit; border: 1px solid #d7dde3; background: #fff; border-radius: 8px; padding: 5px 10px; cursor: pointer; }
  .drill { font-size: 12px; color: #5f6b76; margin-top: 4px; }
  code { background: #f4f6f8; padding: 1px 5px; border-radius: 5px; font-size: 12px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div><div class="t1">CourseLive admin</div><div class="t2" id="activeline">loading</div></div>
    <div class="row2">
      <button class="mini" onclick="clearPreview()">Clear preview</button>
      <button class="mini warn" onclick="clearAll()">Clear all</button>
    </div>
  </div>

  <h2>Active spot, tap one to put it on every phone</h2>
  <div class="panel">
    <div class="spotgrid" id="spotgrid"></div>
    <div class="statusline" id="statusline"></div>
  </div>

  <h2>The room</h2>
  <div class="panel">
    <table>
      <thead><tr><th>Name</th><th>In</th><th>DISC</th><th>Lean</th><th>Roll Call</th><th></th></tr></thead>
      <tbody id="rosterbody"></tbody>
    </table>
  </div>

  <h2>Preview</h2>
  <div class="panel">
    <div class="drill">Open <code>/preview</code> on your own phone to run the active spot as a test identity. It never counts and never shows on the stage. Clear preview wipes only that test run.</div>
  </div>
</div>
<script>
var SECRET = "__SECRET__";

function esc(s){ var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function byid(id){ return document.getElementById(id); }

function post(path, body){
  return fetch("/host/" + SECRET + path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body || {})
  }).then(function(r){ return r.json(); });
}

function setActive(key){ post("/active", {key: key}).then(load); }
function toggleStatus(key, cur){ post("/status", {key: key, status: (cur === "open" ? "locked" : "open")}).then(load); }
function resend(pid){
  post("/resend", {pid: pid}).then(function(res){
    alert(res.ok ? "Result email sent." : "Could not send.");
  });
}
function clearSpot(key){
  if (!confirm("Clear all responses for this spot?")) return;
  post("/clear_spot", {key: key}).then(load);
}
function clearPreview(){ post("/clear_preview", {}).then(function(){ alert("Preview run cleared."); }); }
function clearAll(){
  if (!confirm("Clear every response in the whole room?")) return;
  post("/clear", {}).then(load);
}

function drawSpots(d){
  byid("activeline").textContent = "Active now, " + d.active_title;
  var h = "";
  d.spots.forEach(function(s){
    var cls = "spot" + (s.is_active ? " active" : "") + (s.live ? "" : " coming");
    var coming = s.live ? "" : '<div class="sc">COMING</div>';
    h += '<div class="' + cls + '" onclick="setActive(\\'' + s.key + '\\')">' +
         '<div class="sk">' + esc(s.title) + '</div>' +
         '<div class="sd">Day ' + (s.day === 0 ? "any" : s.day) + '</div>' + coming + '</div>';
  });
  byid("spotgrid").innerHTML = h;
  var st = d.spots.filter(function(s){ return s.is_active; })[0];
  var sl = "";
  if (st){
    sl = 'Input is <strong>' + (st.status === "open" ? "open" : "closed") + '</strong> for ' + esc(d.active_title) + '. ' +
      '<button class="toggle" onclick="toggleStatus(\\'' + st.key + '\\',\\'' + st.status + '\\')">' +
      (st.status === "open" ? "Lock input" : "Open input") + '</button> ' +
      '<button class="toggle" onclick="clearSpot(\\'' + st.key + '\\')">Clear this spot</button>';
  }
  byid("statusline").innerHTML = sl;
}

function drawRoster(d){
  var h = "";
  d.roster.forEach(function(p){
    var inpill = p.joined ? '<span class="pill in">in</span>' : '<span class="pill out">out</span>';
    var disc = p.disc_answered + " of " + p.disc_total;
    var lean = "";
    if (p.disc_primary){
      lean = p.disc_blend ? (p.disc_primary + " and " + p.disc_blend) : p.disc_primary;
    } else {
      lean = "-";
    }
    var roll = p.rollcall ? esc(p.rollcall) : "-";
    var actions = "";
    if (p.disc_answered >= p.disc_total && p.disc_total > 0){
      actions = '<button class="mini" onclick="resend(' + p.id + ')">Resend email</button>';
    }
    h += '<tr><td>' + esc(p.name) + '</td><td>' + inpill + '</td><td>' + disc + '</td><td>' +
         esc(lean) + '</td><td>' + roll + '</td><td>' + actions + '</td></tr>';
  });
  byid("rosterbody").innerHTML = h;
}

function load(){
  fetch("/host/" + SECRET + "/admin/data").then(function(r){ return r.json(); }).then(function(d){
    drawSpots(d);
    drawRoster(d);
  }).catch(function(){});
}

load();
setInterval(load, 3000);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Participant routes
# ---------------------------------------------------------------------------
def render_participant(is_preview):
    html = PAGE.replace("__QUESTIONS__", json.dumps(QUESTIONS))
    html = html.replace("__LEAN__", json.dumps(LEAN))
    html = html.replace("__UPSELL__", json.dumps(UPSELL))
    html = html.replace("__DRIVERS__", json.dumps(DRIVERS))
    html = html.replace("__SPOT_TITLES__", json.dumps({s["key"]: s["title"] for s in SPOTS}))
    html = html.replace("__PREVIEW__", "true" if is_preview else "false")
    return Response(html, mimetype="text/html")


@app.route("/")
def index():
    init_db()
    return render_participant(False)


@app.route("/preview")
def preview():
    init_db()
    session["pid"] = PREVIEW_PID
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO participants (pid) VALUES (%s) ON CONFLICT (pid) DO NOTHING", (PREVIEW_PID,))
        conn.commit()
    return render_participant(True)


@app.route("/roster")
def roster():
    init_db()
    out = []
    for rid, first, last, company, email in ROSTER:
        out.append({"id": rid, "name": first + " " + last, "company": company})
    return jsonify(out)


@app.route("/state")
def state():
    active = get_active_spot()
    return jsonify({"active": active, "status": get_spot_status(active)})


@app.route("/pick", methods=["POST"])
def pick():
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    if pid not in ROSTER_IDS:
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
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    if get_spot_status("disc") == "locked":
        return jsonify({"ok": False, "locked": True})
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
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    counts = tally_for(pid)
    primary, blend, answered = lean_from_counts(counts)
    return jsonify({"ok": True, "primary": primary, "blend": blend,
                    "counts": counts, "answered": answered})


@app.route("/spot/<key>/submit", methods=["POST"])
def spot_submit(key):
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    if not spot_is_live(key):
        return jsonify({"ok": False})
    if get_spot_status(key) == "locked":
        return jsonify({"ok": False, "locked": True})
    data = request.get_json(silent=True) or {}
    if key == "rollcall":
        driver = data.get("driver")
        if driver not in DRIVER_KEYS:
            return jsonify({"ok": False})
        save_response(pid, "rollcall", {"driver": driver})
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/spot/<key>/mine")
def spot_mine(key):
    pid = joined_pid()
    if pid is None:
        return jsonify({})
    r = get_response(pid, key)
    return jsonify(r or {})


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
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    row = identity_for(pid)
    if not row:
        return jsonify({"ok": False})
    rid, first, last, company, email = row
    counts = tally_for(pid)
    primary, blend, answered = lean_from_counts(counts)
    if answered == 0:
        return jsonify({"ok": False})
    name = (first + " " + last).strip()
    res = send_result_email(email, name, primary, blend)
    return jsonify({"ok": bool(res.get("ok"))})


# ---------------------------------------------------------------------------
# Host stage
# ---------------------------------------------------------------------------
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
    active = get_active_spot()
    spot = SPOT_BY_KEY.get(active, {"title": "CourseLive", "anchor": ""})
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
    return jsonify({
        "active": active,
        "title": spot["title"],
        "anchor": spot.get("anchor", ""),
        "people": people,
        "rollcall": rollcall_tally(),
    })


@app.route("/host/<secret>/clear", methods=["POST"])
def host_clear(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM answers")
            cur.execute("DELETE FROM responses")
            cur.execute("DELETE FROM participants")
        conn.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Admin console
# ---------------------------------------------------------------------------
@app.route("/host/<secret>/admin")
def admin(secret):
    if secret != HOST_SECRET:
        return Response("Not found", status=404)
    init_db()
    html = ADMIN_PAGE.replace("__SECRET__", HOST_SECRET)
    return Response(html, mimetype="text/html")


@app.route("/host/<secret>/admin/data")
def admin_data(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    active = get_active_spot()
    active_title = SPOT_BY_KEY.get(active, {"title": "CourseLive"})["title"]
    joined_set = set()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid FROM participants WHERE pid <> %s", (PREVIEW_PID,))
            for (p,) in cur.fetchall():
                joined_set.add(p)
    spots_out = []
    for s in SPOTS:
        spots_out.append({
            "key": s["key"], "title": s["title"], "day": s["day"], "live": s["live"],
            "is_active": s["key"] == active, "status": get_spot_status(s["key"]),
        })
    roster_out = []
    for rid, first, last, company, email in ROSTER:
        counts = tally_for(rid)
        primary, blend, answered = lean_from_counts(counts)
        rc = get_response(rid, "rollcall")
        rc_label = DRIVER_LABEL.get(rc.get("driver")) if rc else None
        roster_out.append({
            "id": rid,
            "name": first + " " + last,
            "joined": rid in joined_set,
            "disc_answered": answered,
            "disc_total": len(QUESTIONS),
            "disc_primary": primary if answered > 0 else None,
            "disc_blend": blend if answered > 0 else None,
            "rollcall": rc_label,
        })
    return jsonify({
        "active": active,
        "active_title": active_title,
        "spots": spots_out,
        "roster": roster_out,
    })


@app.route("/host/<secret>/active", methods=["POST"])
def host_active(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    if key not in SPOT_BY_KEY:
        return jsonify({"ok": False})
    set_active_spot(key)
    return jsonify({"ok": True})


@app.route("/host/<secret>/status", methods=["POST"])
def host_status(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    status = data.get("status")
    if key not in SPOT_BY_KEY or status not in ("open", "locked"):
        return jsonify({"ok": False})
    set_spot_status(key, status)
    return jsonify({"ok": True})


@app.route("/host/<secret>/resend", methods=["POST"])
def host_resend(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    if pid not in ROSTER_IDS:
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


@app.route("/host/<secret>/clear_spot", methods=["POST"])
def host_clear_spot(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    if key not in SPOT_BY_KEY:
        return jsonify({"ok": False})
    with get_conn() as conn:
        with conn.cursor() as cur:
            if key == "disc":
                cur.execute("DELETE FROM answers")
            else:
                cur.execute("DELETE FROM responses WHERE spot_key = %s", (key,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/host/<secret>/clear_preview", methods=["POST"])
def host_clear_preview(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM answers WHERE pid = %s", (PREVIEW_PID,))
            cur.execute("DELETE FROM responses WHERE pid = %s", (PREVIEW_PID,))
            cur.execute("DELETE FROM participants WHERE pid = %s", (PREVIEW_PID,))
        conn.commit()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
