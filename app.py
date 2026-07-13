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
    {"key": "welcome", "day": 0, "title": "Welcome", "anchor": "Greet the room as students join", "live": True},
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
    {"key": "jeopardy", "day": 3, "title": "Quizo", "anchor": "Day Three review, all principle families plus Magic Formula, LIONS, and Worry", "live": True},
    {"key": "taketheturn", "day": 3, "title": "Take the Turn", "anchor": "3B Disagree Agreeably, the Cushion", "live": False},
    {"key": "disc", "day": 3, "title": "Your DISC Lean", "anchor": "3C Develop More Flexibility, How People View Us", "live": True},
    {"key": "recognition", "day": 3, "title": "Recognition Wall", "anchor": "3D Build Others Through Recognition", "live": True},
]

SPOT_BY_KEY = {s["key"]: s for s in SPOTS}
DEFAULT_ACTIVE = "welcome"

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


# ---------------------------------------------------------------------------
# Quizo, the Day Three review board. Internal spot key is jeopardy, the screen
# name is Quizo. Three teams, seven categories, four values, buzz decided
# server side by first arrival. Content grounded in the course deck.
# ---------------------------------------------------------------------------
JTEAMS = [
    {"n": 1, "name": "Team 1", "color": "#0d9488"},
    {"n": 2, "name": "Team 2", "color": "#d4a017"},
    {"n": 3, "name": "Team 3", "color": "#3aa9c9"},
]
JTEAM_NUMS = [t["n"] for t in JTEAMS]
JTEAM_BY_NUM = {t["n"]: t for t in JTEAMS}

JCATS = [
    {"key": "enhance", "title": "Enhance Relationships"},
    {"key": "cooperation", "title": "Gain Willing Cooperation"},
    {"key": "leader", "title": "Be a Leader"},
    {"key": "magic", "title": "Magic Formula"},
    {"key": "lions", "title": "LIONS"},
    {"key": "worry", "title": "Worry"},
    {"key": "potpourri", "title": "Potpourri"},
]
JVALS = [100, 200, 300, 400]

# Keyed category index then value index. Every clue grounded in the deck,
# except Potpourri which is clean general knowledge by design.
JCLUES = {
    "0_0": {"clue": "The three things Carnegie says never to do to people.", "answer": "Criticize, condemn, or complain"},
    "0_1": {"clue": "Carnegie calls this the sweetest and most important sound in any language.", "answer": "A person's own name"},
    "0_2": {"clue": "Principle five, the simple thing you do with your face to make people like you.", "answer": "Smile"},
    "0_3": {"clue": "Give appreciation that is honest and this.", "answer": "Sincere"},
    "1_0": {"clue": "The only way to get the best of an argument.", "answer": "Avoid it"},
    "1_1": {"clue": "When you are wrong, do this quickly and emphatically.", "answer": "Admit it"},
    "1_2": {"clue": "To win cooperation, let the other person feel the idea is this.", "answer": "His or hers"},
    "1_3": {"clue": "Appeal to these higher motives to move people.", "answer": "Nobler motives"},
    "2_0": {"clue": "A leader begins with praise and honest this.", "answer": "Appreciation"},
    "2_1": {"clue": "Call attention to people's mistakes this way, so they do not resent it.", "answer": "Indirectly"},
    "2_2": {"clue": "Talk about your own these before criticizing the other person.", "answer": "Mistakes"},
    "2_3": {"clue": "Give the other person one of these fine ones to live up to.", "answer": "Reputation"},
    "3_0": {"clue": "The Magic Formula has this many steps.", "answer": "Three"},
    "3_1": {"clue": "Step one, tell the incident or give this.", "answer": "Evidence"},
    "3_2": {"clue": "Step two, make a clear statement asking for this.", "answer": "Action"},
    "3_3": {"clue": "Step three, the positive result for the listener.", "answer": "The benefit"},
    "4_0": {"clue": "The L in LIONS, keep this easily understood.", "answer": "Language"},
    "4_1": {"clue": "The I in LIONS, use these to clarify.", "answer": "Illustrations"},
    "4_2": {"clue": "The O in LIONS, do this to your thoughts.", "answer": "Organize them"},
    "4_3": {"clue": "The S in LIONS, do this to your key points at the end.", "answer": "Summarize them"},
    "5_0": {"clue": "Carnegie says live in these tight compartments.", "answer": "Day tight compartments"},
    "5_1": {"clue": "The first question to ask facing trouble, what is the worst that can do this.", "answer": "Possibly happen"},
    "5_2": {"clue": "After you accept the worst, you try to do this to it.", "answer": "Improve on it"},
    "5_3": {"clue": "Worry can make you pay an exorbitant price in terms of this.", "answer": "Your health"},
    "6_0": {"clue": "This planet is known as the Red Planet.", "answer": "Mars"},
    "6_1": {"clue": "The number of strings on a standard guitar.", "answer": "Six"},
    "6_2": {"clue": "The largest ocean on Earth.", "answer": "The Pacific"},
    "6_3": {"clue": "The artist who painted the Mona Lisa.", "answer": "Leonardo da Vinci"},
}


def jcid(c, v):
    return str(c) + "_" + str(v)


def jvalue_for(cid):
    try:
        c, v = cid.split("_")
        return JVALS[int(v)]
    except Exception:
        return 0


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
                CREATE TABLE IF NOT EXISTS jeopardy_members (
                    pid INTEGER PRIMARY KEY,
                    team INTEGER NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jeopardy_state (
                    id INTEGER PRIMARY KEY,
                    active_cid TEXT,
                    phase TEXT NOT NULL DEFAULT 'board',
                    buzz_team INTEGER,
                    revealed BOOLEAN NOT NULL DEFAULT FALSE,
                    winner_shown BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jeopardy_results (
                    cid TEXT PRIMARY KEY,
                    win_team INTEGER,
                    value INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jeopardy_lockout (
                    cid TEXT NOT NULL,
                    team INTEGER NOT NULL,
                    PRIMARY KEY (cid, team)
                )
            """)
            cur.execute("""
                INSERT INTO jeopardy_state (id, phase) VALUES (1, 'board')
                ON CONFLICT (id) DO NOTHING
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


# ---------------------------------------------------------------------------
# Quizo helpers. Scores derive from won clues so nothing can drift.
# ---------------------------------------------------------------------------
def jeopardy_get_state():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT active_cid, phase, buzz_team, revealed, winner_shown
                FROM jeopardy_state WHERE id = 1
            """)
            row = cur.fetchone()
    if not row:
        return {"active_cid": None, "phase": "board", "buzz_team": None,
                "revealed": False, "winner_shown": False}
    return {"active_cid": row[0], "phase": row[1], "buzz_team": row[2],
            "revealed": bool(row[3]), "winner_shown": bool(row[4])}


def jeopardy_set_state(active_cid=None, phase=None, buzz_team="keep",
                       revealed=None, winner_shown=None):
    sets, vals = [], []
    if phase is not None:
        sets.append("phase = %s"); vals.append(phase)
    if buzz_team != "keep":
        sets.append("buzz_team = %s"); vals.append(buzz_team)
    if revealed is not None:
        sets.append("revealed = %s"); vals.append(revealed)
    if winner_shown is not None:
        sets.append("winner_shown = %s"); vals.append(winner_shown)
    if active_cid == "clear":
        sets.append("active_cid = %s"); vals.append(None)
    elif active_cid is not None:
        sets.append("active_cid = %s"); vals.append(active_cid)
    if not sets:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE jeopardy_state SET " + ", ".join(sets) + " WHERE id = 1", vals)
        conn.commit()


def jeopardy_member(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT team FROM jeopardy_members WHERE pid = %s", (pid,))
            row = cur.fetchone()
            return row[0] if row else None


def jeopardy_members_map():
    out = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid, team FROM jeopardy_members")
            for pid, team in cur.fetchall():
                out[pid] = team
    return out


def jeopardy_assign(pid, team):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jeopardy_members (pid, team) VALUES (%s, %s)
                ON CONFLICT (pid) DO UPDATE SET team = EXCLUDED.team
            """, (pid, team))
        conn.commit()


def jeopardy_results_map():
    out = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT cid, win_team, value FROM jeopardy_results")
            for cid, win_team, value in cur.fetchall():
                out[cid] = {"win_team": win_team, "value": value}
    return out


def jeopardy_scores():
    scores = {t["n"]: 0 for t in JTEAMS}
    for r in jeopardy_results_map().values():
        wt = r["win_team"]
        if wt in scores:
            scores[wt] += r["value"] or 0
    return scores


def jeopardy_record_result(cid, win_team, value):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jeopardy_results (cid, win_team, value) VALUES (%s, %s, %s)
                ON CONFLICT (cid) DO UPDATE
                SET win_team = EXCLUDED.win_team, value = EXCLUDED.value
            """, (cid, win_team, value))
        conn.commit()


def jeopardy_locked_teams(cid):
    out = set()
    if not cid:
        return out
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT team FROM jeopardy_lockout WHERE cid = %s", (cid,))
            for (team,) in cur.fetchall():
                out.add(team)
    return out


def jeopardy_add_lockout(cid, team):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jeopardy_lockout (cid, team) VALUES (%s, %s)
                ON CONFLICT (cid, team) DO NOTHING
            """, (cid, team))
        conn.commit()


def jeopardy_clear_lockout(cid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jeopardy_lockout WHERE cid = %s", (cid,))
        conn.commit()


def jeopardy_try_buzz(team):
    # First arrival for the armed clue wins through one guarded write.
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jeopardy_state SET buzz_team = %s, phase = 'buzzed'
                WHERE id = 1 AND phase = 'armed' AND buzz_team IS NULL
            """, (team,))
            won = cur.rowcount == 1
        conn.commit()
    return won


def jeopardy_reset(keep_members=True):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jeopardy_results")
            cur.execute("DELETE FROM jeopardy_lockout")
            cur.execute("""
                UPDATE jeopardy_state
                SET active_cid = NULL, phase = 'board', buzz_team = NULL,
                    revealed = FALSE, winner_shown = FALSE
                WHERE id = 1
            """)
            if not keep_members:
                cur.execute("DELETE FROM jeopardy_members")
        conn.commit()


def jeopardy_board(for_host):
    st = jeopardy_get_state()
    results = jeopardy_results_map()
    cats = [c["title"] for c in JCATS]
    cells = []
    for c in range(len(JCATS)):
        for v in range(len(JVALS)):
            cid = jcid(c, v)
            cells.append({
                "cid": cid, "c": c, "v": v, "value": JVALS[v],
                "done": cid in results,
                "win_team": results.get(cid, {}).get("win_team"),
            })
    cur_clue = None
    active = st["active_cid"]
    if active and active in JCLUES:
        cur_clue = {"cid": active, "clue": JCLUES[active]["clue"]}
        if for_host or st["revealed"]:
            cur_clue["answer"] = JCLUES[active]["answer"]
        cur_clue["value"] = jvalue_for(active)
    block = {
        "phase": st["phase"],
        "active": active,
        "buzz_team": st["buzz_team"],
        "revealed": st["revealed"],
        "winner_shown": st["winner_shown"],
        "cats": cats,
        "vals": JVALS,
        "cells": cells,
        "clue": cur_clue,
        "scores": jeopardy_scores(),
        "teams": JTEAMS,
    }
    if for_host:
        block["locked"] = sorted(jeopardy_locked_teams(active))
    return block


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
  .peeropt { transition: border-color 0.15s, background 0.15s; }
  textarea.note { width: 100%; border: 1px solid #d7dde3; border-radius: 12px; padding: 12px 14px; font-size: 15px; font-family: inherit; min-height: 84px; margin: 4px 0 12px; resize: vertical; }
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
var lastRecStatus = null;
var qi = 0;
var recPeer = null;
var jTimer = null;
var jMounted = false;

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
    var changed = st.active !== renderedKey;
    if (st.active === "recognition" && st.status !== lastRecStatus){ changed = true; }
    if (st.active === "recognition"){ lastRecStatus = st.status; }
    if (changed){
      renderedKey = st.active;
      renderSpot(st.active, st.status);
    }
  }).catch(function(){});
}

function renderSpot(key, status){
  if (jTimer && key !== "jeopardy"){ clearInterval(jTimer); jTimer = null; jMounted = false; }
  if (key === "welcome"){ renderJoined(); return; }
  if (key === "disc"){ startDisc(); return; }
  if (key === "rollcall"){ startRollcall(); return; }
  if (key === "jeopardy"){ startJeopardy(); return; }
  if (key === "recognition"){
    if (status === "locked"){ recWallUp(); } else { startRecognition(); }
    return;
  }
  renderHold(key);
}

function renderJoined(){
  setBar(0);
  setTitle("CourseLive");
  el("sub").textContent = "You are in";
  el("body").innerHTML =
    '<div class="hold">' +
    '<span class="tag">YOU ARE IN</span>' +
    '<p class="big">See your name on the screen?</p>' +
    '<p class="small">You are all set. Watch the main screen, your phone will follow along when we start.</p>' +
    '</div>';
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

// ----- Recognition Wall -----
function startRecognition(){
  setTitle("Recognition Wall");
  setBar(0);
  el("sub").textContent = "A note for a classmate";
  recPeer = null;
  fetch("/spot/recognition/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && mine.to){ recSent(); return; }
    fetch("/spot/recognition/peers").then(function(r){ return r.json(); }).then(function(peers){
      var h = '<p class="stem">Send a sincere, specific note to someone in the room. Keep it warm and brief.</p><div>';
      peers.forEach(function(p){
        h += '<div class="opt peeropt" data-id="' + p.id + '" onclick="selPeer(' + p.id + ')">' + esc(p.name) + '</div>';
      });
      h += '</div><textarea class="note" id="note" placeholder="What do you appreciate about them?"></textarea>' +
           '<button class="btn" onclick="sendRec()">Send it</button>';
      el("body").innerHTML = h;
    });
  });
}

function selPeer(id){
  recPeer = id;
  var opts = document.querySelectorAll(".peeropt");
  for (var i=0;i<opts.length;i++){
    var on = parseInt(opts[i].getAttribute("data-id"), 10) === id;
    opts[i].style.borderColor = on ? "#0d9488" : "#d7dde3";
    opts[i].style.background = on ? "#e1f5ee" : "#fff";
  }
}

function sendRec(){
  var note = (el("note").value || "").trim();
  if (recPeer === null){ el("sub").textContent = "Pick a name first"; return; }
  if (!note){ el("sub").textContent = "Add a short note"; return; }
  api("/spot/recognition/submit", {to: recPeer, note: note}).then(function(res){
    if (res.ok){ recSent(); }
    else if (res.locked){ el("sub").textContent = "The wall is closed now"; }
  });
}

function recSent(){
  setBar(100);
  el("sub").textContent = "Sent";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">SENT</span>' +
    '<p class="big">Your note is in.</p>' +
    '<p class="small">We will put the wall on the screen. Watch the main display.</p></div>';
}

function recWallUp(){
  setBar(100);
  el("sub").textContent = "On the screen";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">RECOGNITION WALL</span>' +
    '<p class="big">Look up at the screen.</p>' +
    '<p class="small">The notes the room wrote are up on the main display.</p></div>';
}

// ----- Quizo, the team buzzer -----
var jLastSig = "";

function startJeopardy(){
  setTitle("Quizo");
  setBar(0);
  el("sub").textContent = "Team play";
  el("body").innerHTML =
    '<div id="jbanner" style="text-align:center;margin-bottom:14px"></div>' +
    '<div id="jbuzzarea"></div>';
  jMounted = true;
  jLastSig = "";
  jPoll();
  if (jTimer){ clearInterval(jTimer); }
  jTimer = setInterval(jPoll, 900);
}

function jPoll(){
  fetch("/spot/jeopardy/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ return; }
    drawJParticipant(d);
  }).catch(function(){});
}

function jMsg(big, small, color){
  return '<div style="text-align:center;padding:26px 10px;border:1px solid #e6ebef;border-radius:16px">' +
    '<p style="font-size:19px;font-weight:600;margin:0 0 6px;color:' + color + '">' + esc(big) + '</p>' +
    '<p style="font-size:14px;color:#5f6b76;margin:0">' + esc(small) + '</p></div>';
}

function drawJParticipant(d){
  var ban = el("jbanner");
  if (!ban){ return; }
  if (!d.team){
    ban.innerHTML = '<span class="tag">QUIZO</span>' +
      '<p style="font-size:20px;font-weight:600;margin:6px 0 4px">Getting your team</p>' +
      '<p style="font-size:14px;color:#5f6b76;margin:0">Your host is placing you on a team. Watch the screen.</p>';
    el("jbuzzarea").innerHTML = "";
    jLastSig = "noteam";
    return;
  }
  ban.innerHTML =
    '<div style="display:inline-block;background:' + d.team_color + ';color:#fff;border-radius:999px;padding:6px 16px;font-size:14px;font-weight:600">' + esc(d.team_name) + '</div>' +
    '<div style="font-size:34px;font-weight:700;margin-top:10px">' + d.score + '</div>' +
    '<div style="font-size:12px;color:#5f6b76">your team score</div>';
  var sig = d.phase + "|" + (d.buzz_team || 0) + "|" + (d.locked ? "L" : "") + "|" + d.team;
  if (sig === jLastSig){ return; }
  jLastSig = sig;
  var area = el("jbuzzarea");
  if (d.phase === "armed" && !d.locked){
    area.innerHTML = '<button id="buzzbtn" onclick="buzz()" style="width:100%;background:' + d.team_color + ';color:#fff;border:none;border-radius:18px;padding:40px 12px;font-size:30px;font-weight:700;font-family:inherit;cursor:pointer;letter-spacing:3px">BUZZ</button>';
  } else if (d.phase === "armed" && d.locked){
    area.innerHTML = jMsg("Your team already answered", "Let the other teams try this one.", "#8a97a3");
  } else if (d.phase === "buzzed" && d.buzz_team === d.team){
    area.innerHTML = jMsg("You buzzed first", "Say your answer out loud to the room.", "#0d9488");
  } else if (d.phase === "buzzed"){
    area.innerHTML = jMsg((d.buzz_name || "Another team") + " buzzed first", "Listen in, you may get the next one.", "#8a97a3");
  } else if (d.phase === "answer"){
    area.innerHTML = jMsg("Answer is on the screen", "Look up at the board.", "#8a97a3");
  } else {
    area.innerHTML = jMsg("Watch the board", "Your host will put the next clue up.", "#8a97a3");
  }
}

function buzz(){
  var b = el("buzzbtn");
  if (b){ b.textContent = "..."; b.disabled = true; }
  api("/spot/jeopardy/buzz", {}).then(function(){ jLastSig = ""; jPoll(); })
    .catch(function(){ jLastSig = ""; jPoll(); });
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
  .welcome { background: #0f2942; padding: 46px 30px 40px; text-align: center; color: #fff; }
  .welcome .ey { font-size: 14px; font-weight: 600; letter-spacing: 3px; color: #9fe1cb; text-transform: uppercase; }
  .welcome .big { font-size: 40px; font-weight: 600; margin: 14px 0 6px; line-height: 1.15; }
  .welcome .dt { font-size: 15px; color: #b9c6d4; margin-bottom: 4px; }
  .welcome .cue { font-size: 14px; color: #7fd8c0; margin-top: 14px; }
  .chiprow { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 26px; min-height: 40px; }
  .chip { background: rgba(255,255,255,0.08); border: 1px solid rgba(159,225,203,0.35); color: #fff; border-radius: 999px; padding: 9px 18px; font-size: 16px; font-weight: 500; animation: pop 0.55s cubic-bezier(0.2,0.8,0.3,1.2) both; }
  .chip .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #0d9488; margin-right: 8px; vertical-align: middle; }
  @keyframes pop { 0% { opacity: 0; transform: translateY(14px) scale(0.9); } 100% { opacity: 1; transform: translateY(0) scale(1); } }
  .wcount { font-size: 13px; color: #9fe1cb; margin-top: 20px; letter-spacing: 1px; }
  .nextup { padding: 40px 22px; text-align: center; }
  .nextup .lab { font-size: 13px; font-weight: 600; letter-spacing: 1px; color: #0d6e63; }
  .recintro { padding: 40px 22px; text-align: center; }
  .recintro .lab { font-size: 13px; font-weight: 600; letter-spacing: 1px; color: #0d6e63; }
  .recintro .big { font-size: 30px; font-weight: 600; margin: 10px 0 6px; }
  .recintro .an { font-size: 14px; color: #5f6b76; }
  .wall { padding: 18px 20px 26px; column-count: 2; column-gap: 16px; }
  .rcard { break-inside: avoid; background: #fff; border: 1px solid #e4e9ee; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; box-shadow: 0 1px 5px rgba(15,41,66,0.06); }
  .rcard .rto { font-size: 12px; font-weight: 600; color: #0d6e63; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .rnote { font-size: 14px; line-height: 1.45; margin: 0 0 8px; }
  .rnote .rfrom { display: block; font-size: 11px; color: #8a97a3; margin-top: 3px; }
  .nextup .big { font-size: 30px; font-weight: 600; margin: 10px 0 6px; }
  .nextup .an { font-size: 14px; color: #5f6b76; }
  .jboard { padding: 14px 16px 18px; background: #0f2942; }
  .jhead { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 12px; }
  .jgrid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
  .jcat { background: #d4a017; color: #0f2942; font-weight: 600; font-size: 11px; text-align: center; padding: 10px 4px; border-radius: 6px; min-height: 52px; display: flex; align-items: center; justify-content: center; line-height: 1.2; }
  .jcell { background: #0d9488; color: #fff; font-weight: 700; font-size: 20px; text-align: center; padding: 14px 4px; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
  .jcell.done { background: #0b2035; color: #0b2035; }
  .jcell.active { background: #d4a017; color: #0f2942; }
  .jclue { background: #12324f; border: 2px solid #d4a017; border-radius: 12px; padding: 26px 24px; text-align: center; margin-bottom: 12px; }
  .jclue .jcv { font-size: 13px; color: #d4a017; font-weight: 600; letter-spacing: 1px; }
  .jclue .jcq { font-size: 26px; color: #fff; font-weight: 600; line-height: 1.35; margin: 8px 0 0; }
  .jclue .jca { font-size: 21px; color: #9fe1cb; font-weight: 600; margin-top: 14px; }
  .jbuzzline { font-size: 16px; font-weight: 600; margin-top: 14px; }
  .jscores { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
  .jscore { background: #12324f; border-radius: 8px; padding: 12px 14px; }
  .jscore .jsn { font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
  .jscore .jsv { font-size: 26px; font-weight: 700; color: #fff; }
  .jwinner { background: #0f2942; padding: 44px 24px; text-align: center; }
  .jwinner .wl { font-size: 14px; font-weight: 600; letter-spacing: 2px; color: #d4a017; text-transform: uppercase; }
  .jwinner .wt { font-size: 40px; font-weight: 700; color: #fff; margin: 12px 0 18px; }
  .jrank { max-width: 420px; margin: 0 auto; }
  .jrankrow { display: flex; justify-content: space-between; align-items: center; background: #12324f; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
  .jrankrow .rn { font-size: 16px; font-weight: 600; color: #fff; }
  .jrankrow .rv { font-size: 20px; font-weight: 700; color: #9fe1cb; }
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

var welcomeMounted = false;
var welcomeShown = {};

function mountWelcome(){
  byid("stagebody").innerHTML =
    '<div class="welcome">' +
    '<div class="ey">Dale Carnegie Course</div>' +
    '<div class="big">Welcome</div>' +
    '<div class="dt">Reno, July 14 to 16 2026</div>' +
    '<div class="cue">Pick your name on your phone to join</div>' +
    '<div class="chiprow" id="chiprow"></div>' +
    '<div class="wcount" id="wcount"></div>' +
    '</div>';
  welcomeMounted = true;
  welcomeShown = {};
}

function drawWelcome(data){
  byid("cnt").textContent = "";
  if (!welcomeMounted){ mountWelcome(); }
  var row = byid("chiprow");
  (data.joined || []).forEach(function(p){
    if (welcomeShown[p.id]){ return; }
    welcomeShown[p.id] = true;
    var chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = '<span class="dot"></span>' + esc(p.first);
    row.appendChild(chip);
  });
  var n = (data.joined || []).length;
  byid("wcount").textContent = n === 0 ? "Waiting for the room" : (n + " of 7 here");
}

function drawRecognition(data){
  if (data.status !== "locked"){
    var n = (data.recognition || []).length;
    byid("cnt").textContent = n + " of 7 sent";
    byid("stagebody").innerHTML =
      '<div class="recintro"><div class="lab">RECOGNITION WALL</div>' +
      '<div class="big">Notes are coming in</div>' +
      '<div class="an">When the room is ready, lock input on your phone to reveal the wall.</div></div>';
    return;
  }
  byid("cnt").textContent = (data.recognition || []).length + " notes";
  var groups = {};
  var order = [];
  (data.recognition || []).forEach(function(r){
    if (!groups[r.to]){ groups[r.to] = []; order.push(r.to); }
    groups[r.to].push(r);
  });
  var h = '<div class="wall">';
  order.forEach(function(name){
    h += '<div class="rcard"><div class="rto">For ' + esc(name) + '</div>';
    groups[name].forEach(function(r){
      h += '<p class="rnote">' + esc(r.note) + '<span class="rfrom">from ' + esc(r["from"]) + '</span></p>';
    });
    h += '</div>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function jTeamByNum(teams, n){ for (var i=0;i<teams.length;i++){ if (teams[i].n === n){ return teams[i]; } } return null; }
function jCellFor(cells, cid){ for (var i=0;i<cells.length;i++){ if (cells[i].cid === cid){ return cells[i]; } } return null; }

function drawJWinner(j){
  var ranked = j.teams.slice().sort(function(a,b){ return (j.scores[b.n]||0) - (j.scores[a.n]||0); });
  var topScore = j.scores[ranked[0].n] || 0;
  var tie = ranked.filter(function(t){ return (j.scores[t.n]||0) === topScore; });
  var wname = tie.length > 1 ? "It is a tie" : ranked[0].name;
  var wcolor = tie.length > 1 ? "#fff" : ranked[0].color;
  var h = '<div class="jwinner"><div class="wl">Quizo champion</div>' +
    '<div class="wt" style="color:' + wcolor + '">' + esc(wname) + '</div><div class="jrank">';
  ranked.forEach(function(t){
    h += '<div class="jrankrow" style="border-left:6px solid ' + t.color + '">' +
      '<span class="rn">' + esc(t.name) + '</span><span class="rv">' + (j.scores[t.n]||0) + '</span></div>';
  });
  h += '</div></div>';
  byid("stagebody").innerHTML = h;
}

function drawJeopardy(data){
  var j = data.jeopardy;
  byid("cnt").textContent = "";
  if (!j){ byid("stagebody").innerHTML = ""; return; }
  if (j.winner_shown){ drawJWinner(j); return; }
  var h = '<div class="jboard">';
  if (j.clue){
    h += '<div class="jclue"><div class="jcv">' + j.clue.value + ' points</div>' +
      '<div class="jcq">' + esc(j.clue.clue) + '</div>';
    if (j.revealed && j.clue.answer){ h += '<div class="jca">' + esc(j.clue.answer) + '</div>'; }
    if (j.buzz_team){
      var bt = jTeamByNum(j.teams, j.buzz_team);
      h += '<div class="jbuzzline" style="color:' + (bt ? bt.color : "#fff") + '">' + esc(bt ? bt.name : "A team") + ' buzzed first</div>';
    } else if (j.phase === "armed"){
      h += '<div class="jbuzzline" style="color:#9fe1cb">Buzzers are open</div>';
    }
    h += '</div>';
  }
  h += '<div class="jgrid">';
  j.cats.forEach(function(c){ h += '<div class="jcat">' + esc(c) + '</div>'; });
  for (var v=0; v<j.vals.length; v++){
    for (var c=0; c<j.cats.length; c++){
      var cid = c + "_" + v;
      var cell = jCellFor(j.cells, cid);
      var cls = "jcell";
      if (cell && cell.done){ cls += " done"; }
      else if (cid === j.active && j.phase !== "board"){ cls += " active"; }
      h += '<div class="' + cls + '">' + ((cell && cell.done) ? "" : j.vals[v]) + '</div>';
    }
  }
  h += '</div><div class="jscores">';
  j.teams.forEach(function(t){
    h += '<div class="jscore" style="border-top:4px solid ' + t.color + '">' +
      '<div class="jsn" style="color:' + t.color + '">' + esc(t.name) + '</div>' +
      '<div class="jsv">' + (j.scores[t.n]||0) + '</div></div>';
  });
  h += '</div></div>';
  byid("stagebody").innerHTML = h;
}

function draw(data){
  byid("stitle").textContent = data.title;
  if (data.active !== "welcome"){ welcomeMounted = false; }
  if (data.active === "welcome"){ drawWelcome(data); }
  else if (data.active === "disc"){ drawPlot(data); }
  else if (data.active === "rollcall"){ drawTally(data); }
  else if (data.active === "jeopardy"){ drawJeopardy(data); }
  else if (data.active === "recognition"){ drawRecognition(data); }
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
setInterval(poll, 1500);
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
  .teamrow { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #eef2f5; }
  .teamrow .tn { font-size: 13px; font-weight: 500; }
  .teamrow .tc { font-size: 11px; color: #5f6b76; }
  .tbtns { display: flex; gap: 5px; }
  .tpick { border: 1px solid #d7dde3; background: #fff; border-radius: 7px; padding: 5px 10px; font-size: 12px; font-family: inherit; cursor: pointer; }
  .tpick.on1 { background: #0d9488; color: #fff; border-color: #0d9488; }
  .tpick.on2 { background: #d4a017; color: #3d2c00; border-color: #d4a017; }
  .tpick.on3 { background: #3aa9c9; color: #fff; border-color: #3aa9c9; }
  .jbgrid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 6px; }
  .jbcat { font-size: 9px; text-align: center; color: #5f6b76; padding: 2px; line-height: 1.1; min-height: 26px; display: flex; align-items: center; justify-content: center; }
  .jbcell { background: #0d9488; color: #fff; font-size: 13px; font-weight: 600; text-align: center; padding: 10px 2px; border-radius: 5px; cursor: pointer; }
  .jbcell.done { background: #e6ebef; color: #b6c0ca; cursor: default; }
  .jbcell.active { background: #d4a017; color: #3d2c00; }
  .jcluebox { background: #f4f6f8; border-radius: 10px; padding: 12px 14px; margin-top: 12px; }
  .jcluebox .cq { font-size: 14px; font-weight: 500; }
  .jcluebox .ca { font-size: 13px; color: #0d6e63; font-weight: 600; margin-top: 6px; }
  .jcluebox .cb { font-size: 12px; color: #5f6b76; margin-top: 6px; }
  .jact { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
  .jact .b { border: 1px solid #d7dde3; background: #fff; border-radius: 8px; padding: 9px 13px; font-size: 13px; font-family: inherit; cursor: pointer; }
  .jact .b.good { background: #0d9488; color: #fff; border-color: #0d9488; }
  .jact .b.bad { background: #fff; color: #993556; border-color: #e3b8c4; }
  .jscoremini { display: flex; gap: 8px; margin-top: 12px; }
  .jscoremini .s { flex: 1; border-radius: 8px; padding: 8px 10px; text-align: center; color: #fff; }
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

  <div id="jsection" style="display:none">
    <h2>Quizo, the review board</h2>
    <div class="panel">
      <div id="jadmin"></div>
    </div>
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
  if (st && st.key === "jeopardy"){
    sl = 'Quizo runs from the panel below. ' +
      '<button class="toggle" onclick="clearSpot(\\'jeopardy\\')">Reset Quizo</button>';
  } else if (st){
    var isRec = st.key === "recognition";
    var openLbl = isRec ? "Hide the wall" : "Lock input";
    var lockLbl = isRec ? "Reveal the wall" : "Open input";
    var stateLbl = isRec
      ? (st.status === "open" ? "collecting notes" : "wall is showing")
      : (st.status === "open" ? "open" : "closed");
    sl = 'Status, <strong>' + stateLbl + '</strong> for ' + esc(d.active_title) + '. ' +
      '<button class="toggle" onclick="toggleStatus(\\'' + st.key + '\\',\\'' + st.status + '\\')">' +
      (st.status === "open" ? openLbl : lockLbl) + '</button> ' +
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

var jAdminSig = "";

function setTeam(pid, team){ post("/jeopardy/team", {pid: pid, team: team}).then(load); }
function previewTeam(team){ post("/jeopardy/preview_team", {team: team}).then(load); }
function autoSplit(){ post("/jeopardy/autosplit", {}).then(load); }
function revealCell(c, v){ post("/jeopardy/reveal", {cid: c + "_" + v}).then(load); }
function judgeCorrect(){ post("/jeopardy/judge", {result: "correct"}).then(load); }
function judgeIncorrect(){ post("/jeopardy/judge", {result: "incorrect"}).then(load); }
function revealAnswer(){ post("/jeopardy/answer", {}).then(load); }
function closeClue(){ post("/jeopardy/close", {}).then(load); }
function showWinner(){ post("/jeopardy/winner", {show: true}).then(load); }
function hideWinner(){ post("/jeopardy/winner", {show: false}).then(load); }
function resetGame(){ if (!confirm("Reset the Quizo board and scores? Team assignments stay.")) return; post("/jeopardy/reset", {}).then(function(){ jAdminSig = ""; load(); }); }

function jaCell(cells, cid){ for (var i=0;i<cells.length;i++){ if (cells[i].cid === cid){ return cells[i]; } } return null; }
function jaTeam(teams, n){ for (var i=0;i<teams.length;i++){ if (teams[i].n === n){ return teams[i]; } } return null; }

function drawJeopardyAdmin(d){
  var j = d.jeopardy;
  var mem = d.jmembers || {};
  var sig = JSON.stringify(j) + "|" + JSON.stringify(mem);
  if (sig === jAdminSig){ return; }
  jAdminSig = sig;
  var h = '<div style="font-size:12px;color:#5f6b76;margin-bottom:8px">Assign each person to a team, then tap a clue. <button class="tpick" onclick="autoSplit()">Auto split into 3</button></div>';
  d.roster.forEach(function(p){
    var t = mem[p.id] || 0;
    h += '<div class="teamrow"><div><div class="tn">' + esc(p.name) + '</div><div class="tc">' + (p.joined ? "in" : "out") + '</div></div>' +
      '<div class="tbtns">' +
      '<button class="tpick ' + (t===1?"on1":"") + '" onclick="setTeam(' + p.id + ',1)">1</button>' +
      '<button class="tpick ' + (t===2?"on2":"") + '" onclick="setTeam(' + p.id + ',2)">2</button>' +
      '<button class="tpick ' + (t===3?"on3":"") + '" onclick="setTeam(' + p.id + ',3)">3</button>' +
      '</div></div>';
  });
  var pt = mem[0] || 0;
  h += '<div class="teamrow"><div><div class="tn">Preview run</div><div class="tc">for your dry run on /preview</div></div>' +
    '<div class="tbtns">' +
    '<button class="tpick ' + (pt===1?"on1":"") + '" onclick="previewTeam(1)">1</button>' +
    '<button class="tpick ' + (pt===2?"on2":"") + '" onclick="previewTeam(2)">2</button>' +
    '<button class="tpick ' + (pt===3?"on3":"") + '" onclick="previewTeam(3)">3</button>' +
    '</div></div>';
  h += '<h2 style="margin:16px 0 4px;font-size:13px">Tap a clue to put it on the screen</h2><div class="jbgrid">';
  j.cats.forEach(function(c){ h += '<div class="jbcat">' + esc(c) + '</div>'; });
  for (var v=0; v<j.vals.length; v++){
    for (var c=0; c<j.cats.length; c++){
      var cid = c + "_" + v;
      var cell = jaCell(j.cells, cid);
      var cls = "jbcell";
      var oc = 'onclick="revealCell(' + c + ',' + v + ')"';
      if (cell && cell.done){ cls += " done"; oc = ""; }
      else if (cid === j.active && j.phase !== "board"){ cls += " active"; }
      h += '<div class="' + cls + '" ' + oc + '>' + ((cell && cell.done) ? "" : j.vals[v]) + '</div>';
    }
  }
  h += '</div>';
  if (j.clue){
    h += '<div class="jcluebox"><div class="cq">' + esc(j.clue.clue) + '</div>' +
      '<div class="ca">Answer, ' + esc(j.clue.answer || "") + '</div>';
    var status = "";
    if (j.buzz_team){
      var bt = jaTeam(j.teams, j.buzz_team);
      status = (bt ? bt.name : "A team") + " buzzed first. They answer out loud, then you rule.";
    } else if (j.phase === "armed"){
      status = "Buzzers are open. Waiting for a team.";
    } else if (j.phase === "answer"){
      status = "Answer is on the screen.";
    }
    h += '<div class="cb">' + esc(status) + '</div><div class="jact">';
    if (j.buzz_team){
      h += '<button class="b good" onclick="judgeCorrect()">Correct</button>' +
        '<button class="b bad" onclick="judgeIncorrect()">Incorrect</button>';
    }
    if (!j.revealed){ h += '<button class="b" onclick="revealAnswer()">Reveal answer</button>'; }
    h += '<button class="b" onclick="closeClue()">Close, no winner</button></div></div>';
  }
  h += '<div class="jscoremini">';
  j.teams.forEach(function(t){
    h += '<div class="s" style="background:' + t.color + '"><div style="font-size:11px">' + esc(t.name) + '</div>' +
      '<div style="font-size:18px;font-weight:700">' + (j.scores[t.n]||0) + '</div></div>';
  });
  h += '</div><div class="jact" style="margin-top:12px">';
  if (j.winner_shown){ h += '<button class="b good" onclick="hideWinner()">Hide winner</button>'; }
  else { h += '<button class="b good" onclick="showWinner()">Reveal winner</button>'; }
  h += '<button class="b bad" onclick="resetGame()">Reset Quizo</button></div>';
  byid("jadmin").innerHTML = h;
}

function load(){
  fetch("/host/" + SECRET + "/admin/data").then(function(r){ return r.json(); }).then(function(d){
    drawSpots(d);
    drawRoster(d);
    var js = byid("jsection");
    if (d.active === "jeopardy"){ js.style.display = "block"; drawJeopardyAdmin(d); }
    else { js.style.display = "none"; jAdminSig = ""; }
  }).catch(function(){});
}

load();
setInterval(load, 1500);
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
    if key == "recognition":
        to = data.get("to")
        note = (data.get("note") or "").strip()
        if to not in ROSTER_IDS or to == pid or not note:
            return jsonify({"ok": False})
        save_response(pid, "recognition", {"to": to, "note": note[:240]})
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/spot/recognition/peers")
def recognition_peers():
    pid = joined_pid()
    if pid is None:
        return jsonify([])
    out = []
    for rid, first, last, company, email in ROSTER:
        if rid == pid:
            continue
        out.append({"id": rid, "name": first + " " + last})
    return jsonify(out)


@app.route("/spot/<key>/mine")
def spot_mine(key):
    pid = joined_pid()
    if pid is None:
        return jsonify({})
    r = get_response(pid, key)
    return jsonify(r or {})


@app.route("/spot/jeopardy/me")
def jeopardy_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    team = jeopardy_member(pid)
    if not team:
        return jsonify({"ok": True, "team": None})
    st = jeopardy_get_state()
    scores = jeopardy_scores()
    tm = JTEAM_BY_NUM.get(team, {"name": "Team", "color": TEAL})
    locked = team in jeopardy_locked_teams(st["active_cid"])
    buzz_name = None
    if st["buzz_team"]:
        buzz_name = JTEAM_BY_NUM.get(st["buzz_team"], {}).get("name")
    return jsonify({
        "ok": True,
        "team": team,
        "team_name": tm["name"],
        "team_color": tm["color"],
        "score": scores.get(team, 0),
        "phase": st["phase"],
        "buzz_team": st["buzz_team"],
        "buzz_name": buzz_name,
        "locked": locked,
        "revealed": st["revealed"],
    })


@app.route("/spot/jeopardy/buzz", methods=["POST"])
def jeopardy_buzz():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    if get_active_spot() != "jeopardy":
        return jsonify({"ok": False})
    team = jeopardy_member(pid)
    if not team:
        return jsonify({"ok": False, "reason": "noteam"})
    st = jeopardy_get_state()
    if st["phase"] != "armed" or st["active_cid"] is None:
        return jsonify({"ok": True, "won": False})
    if team in jeopardy_locked_teams(st["active_cid"]):
        return jsonify({"ok": True, "won": False, "locked": True})
    won = jeopardy_try_buzz(team)
    return jsonify({"ok": True, "won": won})


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
    joined = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid FROM participants WHERE pid <> %s", (PREVIEW_PID,))
            jset = set(p for (p,) in cur.fetchall())
    for rid, first, last, company, email in ROSTER:
        if rid in jset:
            joined.append({"id": rid, "first": first})
    first_by_id = {r[0]: r[1] for r in ROSTER}
    recognition = []
    for rid, first, last, company, email in ROSTER:
        r = get_response(rid, "recognition")
        if r and r.get("to") in first_by_id and (r.get("note") or "").strip():
            recognition.append({
                "to": first_by_id.get(r["to"], ""),
                "from": first,
                "note": r["note"],
            })
    payload = {
        "active": active,
        "status": get_spot_status(active),
        "title": spot["title"],
        "anchor": spot.get("anchor", ""),
        "people": people,
        "rollcall": rollcall_tally(),
        "joined": joined,
        "recognition": recognition,
    }
    if active == "jeopardy":
        payload["jeopardy"] = jeopardy_board(for_host=False)
    return jsonify(payload)


@app.route("/host/<secret>/clear", methods=["POST"])
def host_clear(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM answers")
            cur.execute("DELETE FROM responses")
            cur.execute("DELETE FROM participants")
            cur.execute("DELETE FROM jeopardy_results")
            cur.execute("DELETE FROM jeopardy_lockout")
            cur.execute("DELETE FROM jeopardy_members")
            cur.execute("""
                UPDATE jeopardy_state
                SET active_cid = NULL, phase = 'board', buzz_team = NULL,
                    revealed = FALSE, winner_shown = FALSE
                WHERE id = 1
            """)
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
        "jeopardy": jeopardy_board(for_host=True),
        "jmembers": jeopardy_members_map(),
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
    if key == "jeopardy":
        jeopardy_reset(keep_members=True)
        return jsonify({"ok": True})
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
            cur.execute("DELETE FROM jeopardy_members WHERE pid = %s", (PREVIEW_PID,))
        conn.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Quizo host controls
# ---------------------------------------------------------------------------
@app.route("/host/<secret>/jeopardy/team", methods=["POST"])
def jeopardy_team(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    team = data.get("team")
    if pid not in (ROSTER_IDS + [PREVIEW_PID]) or team not in JTEAM_NUMS:
        return jsonify({"ok": False})
    jeopardy_assign(pid, team)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/preview_team", methods=["POST"])
def jeopardy_preview_team(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    team = data.get("team")
    if team not in JTEAM_NUMS:
        return jsonify({"ok": False})
    jeopardy_assign(PREVIEW_PID, team)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/autosplit", methods=["POST"])
def jeopardy_autosplit(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    # Balanced three way split that puts each coworker pair on different teams.
    plan = {1: 1, 4: 1, 6: 1, 2: 2, 5: 2, 3: 3, 7: 3}
    for pid, team in plan.items():
        jeopardy_assign(pid, team)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/reveal", methods=["POST"])
def jeopardy_reveal(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    cid = data.get("cid")
    if cid not in JCLUES:
        return jsonify({"ok": False})
    if cid in jeopardy_results_map():
        return jsonify({"ok": False, "done": True})
    jeopardy_clear_lockout(cid)
    jeopardy_set_state(active_cid=cid, phase="armed", buzz_team=None,
                       revealed=False, winner_shown=False)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/judge", methods=["POST"])
def jeopardy_judge(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    result = data.get("result")
    st = jeopardy_get_state()
    active = st["active_cid"]
    bt = st["buzz_team"]
    if not active or not bt:
        return jsonify({"ok": False})
    if result == "correct":
        jeopardy_record_result(active, bt, jvalue_for(active))
        jeopardy_set_state(active_cid="clear", phase="board", buzz_team=None, revealed=False)
        return jsonify({"ok": True})
    if result == "incorrect":
        jeopardy_add_lockout(active, bt)
        jeopardy_set_state(phase="armed", buzz_team=None)
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/host/<secret>/jeopardy/answer", methods=["POST"])
def jeopardy_answer(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    st = jeopardy_get_state()
    if not st["active_cid"]:
        return jsonify({"ok": False})
    jeopardy_set_state(phase="answer", revealed=True)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/close", methods=["POST"])
def jeopardy_close(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    st = jeopardy_get_state()
    active = st["active_cid"]
    if active and active not in jeopardy_results_map():
        jeopardy_record_result(active, None, jvalue_for(active))
    jeopardy_set_state(active_cid="clear", phase="board", buzz_team=None, revealed=False)
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/winner", methods=["POST"])
def jeopardy_winner(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    jeopardy_set_state(winner_shown=bool(data.get("show")))
    return jsonify({"ok": True})


@app.route("/host/<secret>/jeopardy/reset", methods=["POST"])
def jeopardy_reset_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    jeopardy_reset(keep_members=True)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
