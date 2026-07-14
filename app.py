import os
import json
import base64
import random
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
JOIN_URL = "https://courselive-production.up.railway.app"
JOIN_QR_SVG_B64 = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OTIiIGhlaWdodD0iNDkyIiBjbGFzcz0ic2Vnbm8iPjxnIHRyYW5zZm9ybT0ic2NhbGUoMTIpIj48cGF0aCBmaWxsPSIjZmZmIiBkPSJNMCAwaDQxdjQxaC00MXoiLz48cGF0aCBjbGFzcz0icXJsaW5lIiBzdHJva2U9IiMwZjI5NDIiIGQ9Ik00IDQuNWg3bTEgMGgzbTIgMGgxbTEgMGgxbTIgMGgybTEgMGgzbTIgMGg3bS0zMyAxaDFtNSAwaDFtMSAwaDFtMSAwaDFtMyAwaDRtMSAwaDFtMSAwaDRtMSAwaDFtNSAwaDFtLTMzIDFoMW0xIDBoM20xIDBoMW0xIDBoMW0yIDBoMW00IDBoMW0xIDBoM20xIDBoM20xIDBoMW0xIDBoM20xIDBoMW0tMzMgMWgxbTEgMGgzbTEgMGgxbTEgMGgxbTIgMGgybTIgMGgzbTEgMGgxbTIgMGgybTIgMGgxbTEgMGgzbTEgMGgxbS0zMyAxaDFtMSAwaDNtMSAwaDFtMSAwaDFtMiAwaDJtMSAwaDVtMSAwaDFtMiAwaDFtMiAwaDFtMSAwaDNtMSAwaDFtLTMzIDFoMW01IDBoMW0yIDBoMm0yIDBoMW0yIDBoMW0xIDBoMm0xIDBoNG0xIDBoMW01IDBoMW0tMzMgMWg3bTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGg3bS0yNSAxaDJtMSAwaDJtMSAwaDFtMSAwaDRtMSAwaDNtLTIzIDFoMm0xIDBoMW0xIDBoMm00IDBoMm0zIDBoMW0zIDBoMW0xIDBoMW0yIDBoMW0xIDBoNW0tMzIgMWgxbTIgMGgybTEgMGgzbTIgMGgybTYgMGgybTIgMGg0bTQgMGgxbS0zMiAxaDFtMSAwaDJtMSAwaDFtMSAwaDVtMyAwaDJtMiAwaDJtMiAwaDRtMiAwaDNtLTMzIDFoNG0xIDBoMW0xIDBoMW0xIDBoMW00IDBoMW0xIDBoMW0yIDBoMW0xIDBoMm01IDBoMW0zIDBoMW0tMzIgMWgxbTIgMGgzbTIgMGgxbTEgMGgxbTEgMGg0bTQgMGgxbTIgMGg0bTEgMGgxbTIgMGgxbS0yOSAxaDJtMSAwaDJtMSAwaDNtNCAwaDFtMiAwaDFtMyAwaDFtMSAwaDFtNSAwaDFtLTMzIDFoMW0yIDBoMW0yIDBoMW0xIDBoMm0yIDBoMW00IDBoMm0xIDBoMW00IDBoMW00IDBoM20tMzAgMWgxbTMgMGg0bTIgMGgxbTEgMGgxbTMgMGgxbTEgMGgxbTEgMGgxbTIgMGgxbTEgMGgxbTIgMGgxbS0zMiAxaDNtMSAwaDFtMSAwaDJtMiAwaDJtMSAwaDFtNyAwaDFtMyAwaDJtLTI3IDFoMW0xIDBoMW0xIDBoMm0xIDBoM20xIDBoM20zIDBoMm0xIDBoMm0yIDBoNG0zIDBoMm0tMzEgMWgzbTEgMGgxbTIgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTYgMGgxbTMgMGgxbTMgMGgzbS0zMyAxaDFtMSAwaDNtMiAwaDFtMSAwaDRtMiAwaDJtMSAwaDhtMSAwaDJtLTI4IDFoMm0xIDBoM20yIDBoMm0zIDBoM20yIDBoMW0xIDBoMW0yIDBoMW0xIDBoMW0yIDBoMW0xIDBoMm0tMjkgMWgybTUgMGgxbTEgMGgybTUgMGgxbTEgMGgxbTEgMGg0bTEgMGg0bS0zMyAxaDFtMiAwaDFtMSAwaDJtMSAwaDJtMSAwaDNtMSAwaDFtMSAwaDJtMyAwaDFtMSAwaDFtMSAwaDFtMiAwaDRtLTMyIDFoMW0xIDBoMW0zIDBoMm0xIDBoMW0zIDBoMW0yIDBoM20xIDBoMm0zIDBoMW0xIDBoMW0yIDBoMW0tMzIgMWgxbTEgMGgxbTIgMGgzbTEgMGgxbTEgMGgxbTEgMGgxbTYgMGgybTIgMGg1bTIgMGgxbS0yNCAxaDFtMSAwaDFtMSAwaDFtMSAwaDJtMSAwaDFtNCAwaDFtMSAwaDFtMyAwaDJtMiAwaDFtLTMzIDFoN20xIDBoMm0yIDBoMm0xIDBoMm0xIDBoMW0zIDBoM20xIDBoMW0xIDBoMW0xIDBoM20tMzMgMWgxbTUgMGgxbTMgMGgzbTEgMGg5bTEgMGgxbTMgMGgxbTIgMGgxbS0zMiAxaDFtMSAwaDNtMSAwaDFtMSAwaDJtMiAwaDJtMyAwaDFtMiAwaDNtMSAwaDZtMSAwaDJtLTMzIDFoMW0xIDBoM20xIDBoMW0yIDBoM20xIDBoMW0xIDBoMW0xIDBoMW0yIDBoMm0yIDBoMW0zIDBoMW0xIDBoM20tMzMgMWgxbTEgMGgzbTEgMGgxbTEgMGgxbTYgMGgxbTEgMGgybTEgMGgybTEgMGgxbTQgMGgybTIgMGgxbS0zMyAxaDFtNSAwaDFtMSAwaDJtMSAwaDJtMiAwaDFtNCAwaDJtMiAwaDFtMSAwaDFtMSAwaDFtMiAwaDFtLTMyIDFoN20yIDBoNG0xIDBoMW00IDBoM20xIDBoMm0zIDBoMW0yIDBoMiIvPjwvZz48L3N2Zz4K"

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
    {"key": "holding", "day": 0, "title": "Holding", "anchor": "", "live": True},
    {"key": "who_next", "day": 0, "title": "Who's Next", "anchor": "Random name picker, all three days", "live": True},
    {"key": "rollcall", "day": 1, "title": "Roll Call", "anchor": "1A Build a Foundation, Five Drivers of Success", "live": True},
    {"key": "namegame", "day": 1, "title": "Name Game", "anchor": "1B Recall and Use Names, Pause Part Punch", "live": True},
    {"key": "pegquiz", "day": 1, "title": "Peg Quiz", "anchor": "1C Peg Words 1 to 9", "live": True},
    {"key": "breakthrough", "day": 1, "title": "Breakthrough Board", "anchor": "1C Commit to Enhance Relationships", "live": True},
    {"key": "principledraw", "day": 2, "title": "Principle Draw", "anchor": "2A Motivate Others and Enhance Relationships", "live": True},
    {"key": "clearcloudy", "day": 2, "title": "Clear or Cloudy", "anchor": "2B Make Our Ideas Clear, Magic Formula", "live": True},
    {"key": "energizer", "day": 2, "title": "Energizer", "anchor": "2C Energize Our Communications", "live": True},
    {"key": "worryvault", "day": 2, "title": "Worry Vault", "anchor": "2D Put Stress in Perspective", "live": True},
    {"key": "jeopardy", "day": 3, "title": "Quizo", "anchor": "3A Gain Cooperation and Leadership review, plus Magic Formula, LIONS, and Worry", "live": True},
    {"key": "taketheturn", "day": 3, "title": "Take the Turn", "anchor": "3B Disagree Agreeably, the Cushion", "live": True},
    {"key": "disc", "day": 3, "title": "Your DISC Lean", "anchor": "3C Develop More Flexibility, How People View Us", "live": True},
    {"key": "recognition", "day": 3, "title": "Recognition Wall", "anchor": "3D Build Others Through Recognition", "live": True},
    {"key": "review", "day": 3, "title": "Your Recap", "anchor": "Each person's own three days, bundled with your note", "live": True},
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


# ---------------------------------------------------------------------------
# Self scored quiz spots. Same engine, one bank per spot. Answers are checked
# on the phone, a final score is submitted. Content grounded in the deck.
# ---------------------------------------------------------------------------
QUIZ_BANKS = {
    "pegquiz": {
        "title": "Peg Quiz",
        "intro": "Match each number to its peg word. One tap per number.",
        "questions": [
            {"stem": "Peg word for 1?", "options": [{"t": "Run", "correct": True}, {"t": "Zoo"}, {"t": "Door"}, {"t": "Gate"}]},
            {"stem": "Peg word for 2?", "options": [{"t": "Zoo", "correct": True}, {"t": "Tree"}, {"t": "Hive"}, {"t": "Wine"}]},
            {"stem": "Peg word for 3?", "options": [{"t": "Tree", "correct": True}, {"t": "Door"}, {"t": "Run"}, {"t": "Sick"}]},
            {"stem": "Peg word for 4?", "options": [{"t": "Door", "correct": True}, {"t": "Hive"}, {"t": "Zoo"}, {"t": "Heaven"}]},
            {"stem": "Peg word for 5?", "options": [{"t": "Hive", "correct": True}, {"t": "Sick"}, {"t": "Tree"}, {"t": "Gate"}]},
            {"stem": "Peg word for 6?", "options": [{"t": "Sick", "correct": True}, {"t": "Heaven"}, {"t": "Door"}, {"t": "Run"}]},
            {"stem": "Peg word for 7?", "options": [{"t": "Heaven", "correct": True}, {"t": "Gate"}, {"t": "Hive"}, {"t": "Zoo"}]},
            {"stem": "Peg word for 8?", "options": [{"t": "Gate", "correct": True}, {"t": "Wine"}, {"t": "Sick"}, {"t": "Tree"}]},
            {"stem": "Peg word for 9?", "options": [{"t": "Wine", "correct": True}, {"t": "Run"}, {"t": "Heaven"}, {"t": "Door"}]},
        ],
    },
    "namegame": {
        "title": "Name Game",
        "intro": "Stating your name with impact, and why names matter.",
        "questions": [
            {"stem": "Dale Carnegie's way to state your name with impact is called...", "options": [
                {"t": "Pause, Part, Punch", "correct": True},
                {"t": "Stop, Start, Shout"},
                {"t": "Say it and move on"},
                {"t": "Spell it out slowly"}]},
            {"stem": "In Pause, Part, Punch, you punch your...", "options": [
                {"t": "Last name", "correct": True},
                {"t": "First name"},
                {"t": "Job title"},
                {"t": "Company"}]},
            {"stem": "A person's name is to them the sweetest and most important...", "options": [
                {"t": "Sound in any language", "correct": True},
                {"t": "Word to forget"},
                {"t": "Title to earn"},
                {"t": "Fact to skip"}]},
            {"stem": "Using someone's name in conversation makes them feel...", "options": [
                {"t": "Important", "correct": True},
                {"t": "Watched"},
                {"t": "Pressured"},
                {"t": "Ignored"}]},
        ],
    },
    "taketheturn": {
        "title": "Take the Turn",
        "intro": "Disagree Agreeably. Pick the best answer for each.",
        "questions": [
            {"stem": "Which is a Cushion phrase?", "options": [
                {"t": "I appreciate your view on that", "correct": True},
                {"t": "But that misses the point"},
                {"t": "However, you are mistaken"},
                {"t": "Nevertheless, I disagree"}]},
            {"stem": "Which words should you avoid when you disagree?", "options": [
                {"t": "But, However, Nevertheless", "correct": True},
                {"t": "I hear you saying"},
                {"t": "I understand you said"},
                {"t": "I appreciate your point"}]},
            {"stem": "What is the first step when you take the turn?", "options": [
                {"t": "Think", "correct": True},
                {"t": "Cushion"},
                {"t": "Speak"},
                {"t": "Punch"}]},
            {"stem": "In the Speak step, you back your opinion with this.", "options": [
                {"t": "Evidence", "correct": True},
                {"t": "Volume"},
                {"t": "Emotion"},
                {"t": "Repetition"}]},
            {"stem": "What does a Cushion do?", "options": [
                {"t": "Acknowledges their view before you respond", "correct": True},
                {"t": "Tells them they are wrong"},
                {"t": "Ends the conversation"},
                {"t": "Raises your voice"}]},
        ],
    },
}

WORRY_PRINCIPLE = "Live in day tight compartments. Ask what is the worst that can happen, accept it, then improve on it."

# The 30 Human Relations Principles, grounded in the deck, for Principle Draw.
PRINCIPLES = [
    "Do not criticize, condemn, or complain",
    "Give honest, sincere appreciation",
    "Arouse in the other person an eager want",
    "Become genuinely interested in other people",
    "Smile",
    "Remember that a person's name is the sweetest sound to them",
    "Be a good listener, encourage others to talk about themselves",
    "Talk in terms of the other person's interests",
    "Make the other person feel important, and do it sincerely",
    "The only way to get the best of an argument is to avoid it",
    "Show respect for the other person's opinion, never say you are wrong",
    "If you are wrong, admit it quickly and emphatically",
    "Begin in a friendly way",
    "Get the other person saying yes, yes immediately",
    "Let the other person do a great deal of the talking",
    "Let the other person feel the idea is theirs",
    "Try honestly to see things from the other person's point of view",
    "Be sympathetic with the other person's ideas and desires",
    "Appeal to nobler motives",
    "Dramatize your ideas",
    "Throw down a challenge",
    "Begin with praise and honest appreciation",
    "Call attention to people's mistakes indirectly",
    "Talk about your own mistakes before criticizing the other person",
    "Ask questions instead of giving direct orders",
    "Let the other person save face",
    "Praise the slightest improvement and praise every improvement",
    "Give the other person a fine reputation to live up to",
    "Use encouragement, make the fault seem easy to correct",
    "Make the other person happy about doing the thing you suggest",
]

# Short tags for the same 30 principles, same order, for the Bingo card face.
PRINCIPLE_SHORT = [
    "Don't criticize",
    "Sincere appreciation",
    "Arouse a want",
    "Be interested",
    "Smile",
    "Use their name",
    "Listen well",
    "Their interests",
    "Feel important",
    "Avoid arguments",
    "Respect opinions",
    "Admit if wrong",
    "Be friendly",
    "Get a yes",
    "Let them talk",
    "Their idea",
    "Their point of view",
    "Be sympathetic",
    "Nobler motives",
    "Dramatize",
    "A challenge",
    "Begin with praise",
    "Correct indirectly",
    "Own mistakes first",
    "Ask, don't order",
    "Save face",
    "Praise improvement",
    "Fine reputation",
    "Make it easy",
    "Happy to help",
]

# Principle Bingo card pool. The 30 Human Relations Principles PLUS the signature
# moves and models taught across the three days, so a full board cannot fill on
# day one. Each item is a short tag for the card face and the full wording for
# the console. Some items only surface on day two and three by design.
BINGO_ITEMS = [{"short": PRINCIPLE_SHORT[i], "full": PRINCIPLES[i]} for i in range(len(PRINCIPLES))]
BINGO_ITEMS += [
    {"short": "Magic Formula", "full": "Magic Formula, Evidence then Action then Benefit"},
    {"short": "Evidence Defeats Doubt", "full": "Evidence Defeats Doubt, back a claim with proof"},
    {"short": "LIONS", "full": "LIONS, Language, Illustrations, Organize, Narrow, Summarize"},
    {"short": "Name with impact", "full": "State your name with impact"},
    {"short": "Pause, Part, Punch", "full": "Pause, Part, Punch when you say your name"},
    {"short": "Five Drivers", "full": "The Five Drivers of Success"},
    {"short": "The Cushion", "full": "The Cushion, I hear you saying"},
    {"short": "Disagree Agreeably", "full": "Disagree Agreeably, Cushion, Evidence, Opinion"},
    {"short": "Worst case, accept, improve", "full": "Ask the worst that can happen, accept it, then improve on it"},
    {"short": "Get the facts", "full": "Get the facts before you worry"},
    {"short": "Day tight compartments", "full": "Live in day tight compartments"},
    {"short": "Memory Linking", "full": "Memory Linking to remember"},
    {"short": "Conversation Links", "full": "Conversation Links, Home, Family, Work, Travel, Hobby"},
    {"short": "Four channels", "full": "How People View Us, the four channels of perception"},
    {"short": "Sincere Specific Brief", "full": "Recognition, Sincere, Specific, Brief, Quiet"},
    {"short": "Cycle of Improvement", "full": "The Cycle of Performance Improvement"},
]
BINGO_N = len(BINGO_ITEMS)

# Bingo win lines over a 5 by 5 board, positions 0 to 24, center 12 is free.
BINGO_LINES = [
    [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19], [20, 21, 22, 23, 24],
    [0, 5, 10, 15, 20], [1, 6, 11, 16, 21], [2, 7, 12, 17, 22], [3, 8, 13, 18, 23], [4, 9, 14, 19, 24],
    [0, 6, 12, 18, 24], [4, 8, 12, 16, 20],
]
CC_LIONS = [
    {"key": "L", "label": "Language, keep it easily understood"},
    {"key": "I", "label": "Illustrations, use them to clarify"},
    {"key": "O", "label": "Organize your thoughts"},
    {"key": "N", "label": "Narrow to key points"},
    {"key": "S", "label": "Summarize the key points"},
]
CC_LIONS_KEYS = [x["key"] for x in CC_LIONS]


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
                CREATE TABLE IF NOT EXISTS whonext_done (
                    pid INTEGER PRIMARY KEY,
                    picked_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS whonext_state (
                    id INTEGER PRIMARY KEY,
                    current_pid INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS principle_draw (
                    pid INTEGER PRIMARY KEY,
                    idx INTEGER NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bingo_state (
                    id INTEGER PRIMARY KEY,
                    nonce INTEGER NOT NULL DEFAULT 0,
                    winner_pid INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bingo_called (
                    idx INTEGER PRIMARY KEY,
                    called_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bingo_marks (
                    pid INTEGER NOT NULL,
                    item_idx INTEGER NOT NULL,
                    PRIMARY KEY (pid, item_idx)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bingo_done (
                    pid INTEGER NOT NULL,
                    nonce INTEGER NOT NULL,
                    done_at TIMESTAMPTZ DEFAULT now(),
                    announced BOOLEAN NOT NULL DEFAULT FALSE,
                    PRIMARY KEY (pid, nonce)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS instructor_notes (
                    pid INTEGER PRIMARY KEY,
                    note TEXT NOT NULL DEFAULT ''
                )
            """)
            cur.execute("""
                INSERT INTO bingo_state (id, nonce) VALUES (1, 0)
                ON CONFLICT (id) DO NOTHING
            """)
            cur.execute("""
                INSERT INTO whonext_state (id, current_pid) VALUES (1, NULL)
                ON CONFLICT (id) DO NOTHING
            """)
            cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name = 'whonext_state' AND column_name = 'pick_seq'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE whonext_state ADD COLUMN IF NOT EXISTS pick_seq INTEGER NOT NULL DEFAULT 0")
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


# ---------------------------------------------------------------------------
# Who's Next helpers. Fair pick, no repeat until everyone has had a turn.
# ---------------------------------------------------------------------------
def whonext_joined_ids():
    ids = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid FROM participants WHERE pid <> %s", (PREVIEW_PID,))
            joined = set(p for (p,) in cur.fetchall())
    for rid in ROSTER_IDS:
        if rid in joined:
            ids.append(rid)
    return ids


def whonext_done_ids():
    out = set()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid FROM whonext_done")
            for (p,) in cur.fetchall():
                out.add(p)
    return out


def whonext_current():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_pid FROM whonext_state WHERE id = 1")
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None


def whonext_clear_done():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM whonext_done")
        conn.commit()


def whonext_reset():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM whonext_done")
            cur.execute("UPDATE whonext_state SET current_pid = NULL WHERE id = 1")
        conn.commit()


def whonext_pick():
    pool = list(ROSTER_IDS)
    if not pool:
        return None
    cur_pid = whonext_current()
    done = whonext_done_ids()
    eligible = [p for p in pool if p not in done]
    if not eligible:
        whonext_clear_done()
        eligible = [p for p in pool if p != cur_pid] or pool[:]
    pid = random.choice(eligible)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO whonext_done (pid) VALUES (%s) ON CONFLICT (pid) DO NOTHING", (pid,))
            cur.execute("UPDATE whonext_state SET current_pid = %s, pick_seq = pick_seq + 1 WHERE id = 1", (pid,))
        conn.commit()
    return pid


def whonext_seq():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pick_seq FROM whonext_state WHERE id = 1")
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0


def whonext_public():
    pool = list(ROSTER_IDS)
    done = whonext_done_ids()
    cur = whonext_current()
    remaining = len([p for p in pool if p not in done])
    name = None
    if cur is not None:
        for rid, first, last, company, email in ROSTER:
            if rid == cur:
                name = first + " " + last
                break
    names = [{"id": rid, "first": first} for rid, first, last, company, email in ROSTER]
    return {
        "current_pid": cur,
        "current_name": name,
        "remaining": remaining,
        "total": len(pool),
        "done": sorted(done),
        "seq": whonext_seq(),
        "names": names,
    }


def breakthrough_list():
    out = []
    for rid, first, last, company, email in ROSTER:
        r = get_response(rid, "breakthrough")
        if r and (r.get("action") or "").strip():
            out.append({
                "name": first + " " + last,
                "person": r.get("person", ""),
                "breakthrough": r.get("breakthrough", ""),
                "action": r.get("action", ""),
            })
    return out


def quiz_list(key):
    out = []
    for rid, first, last, company, email in ROSTER:
        r = get_response(rid, key)
        if r and r.get("score") is not None:
            try:
                out.append({"name": first + " " + last,
                            "score": int(r["score"]),
                            "total": int(r.get("total", 0))})
            except (TypeError, ValueError):
                continue
    return out


def worry_list():
    out = []
    for rid, first, last, company, email in ROSTER:
        r = get_response(rid, "worryvault")
        if r and (r.get("note") or "").strip():
            out.append({"note": r["note"]})
    random.shuffle(out)  # break any positional link to identity
    return out


# ----- Principle Draw -----
def principledraw_map():
    out = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid, idx FROM principle_draw")
            for pid, idx in cur.fetchall():
                out[pid] = idx
    return out


def principledraw_for(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT idx FROM principle_draw WHERE pid = %s", (pid,))
            row = cur.fetchone()
            if not row:
                return None
    idx = row[0]
    if 0 <= idx < len(PRINCIPLES):
        return {"idx": idx, "text": PRINCIPLES[idx]}
    return None


def principledraw_deal():
    joined = whonext_joined_ids()
    if not joined:
        return 0
    idxs = list(range(len(PRINCIPLES)))
    random.shuffle(idxs)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM principle_draw")
            for i, pid in enumerate(joined):
                cur.execute("INSERT INTO principle_draw (pid, idx) VALUES (%s, %s)", (pid, idxs[i % len(idxs)]))
        conn.commit()
    return len(joined)


def principledraw_reset():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM principle_draw")
        conn.commit()


def principledraw_public():
    m = principledraw_map()
    rows = []
    for rid, first, last, company, email in ROSTER:
        if rid in m:
            idx = m[rid]
            rows.append({"name": first + " " + last,
                         "text": PRINCIPLES[idx] if 0 <= idx < len(PRINCIPLES) else ""})
    return {"dealt": len(m), "rows": rows}


# ----- Clear or Cloudy -----
def clearcloudy_tally():
    clear = 0
    cloudy = 0
    lions = {x["key"]: 0 for x in CC_LIONS}
    for rid in ROSTER_IDS:
        r = get_response(rid, "clearcloudy")
        if not r:
            continue
        if r.get("verdict") == "clear":
            clear += 1
        elif r.get("verdict") == "cloudy":
            cloudy += 1
            k = r.get("lions")
            if k in lions:
                lions[k] += 1
    lions_out = [{"key": x["key"], "label": x["label"], "count": lions[x["key"]]} for x in CC_LIONS]
    return {"clear": clear, "cloudy": cloudy, "total": clear + cloudy, "lions": lions_out}


def energizer_list():
    out = []
    for rid, first, last, company, email in ROSTER:
        r = get_response(rid, "energizer")
        if r and (r.get("word") or "").strip():
            out.append({"name": first, "word": r["word"]})
    return out


# ----- Principle Bingo -----
def bingo_get_state():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nonce, winner_pid FROM bingo_state WHERE id = 1")
            row = cur.fetchone()
    if not row:
        return {"nonce": 0, "winner_pid": None}
    return {"nonce": row[0], "winner_pid": row[1]}


def bingo_called_list():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT idx FROM bingo_called ORDER BY called_at")
            return [i for (i,) in cur.fetchall()]


def bingo_card_positions(pid, nonce):
    rng = random.Random(str(pid) + "_" + str(nonce))
    idxs = list(range(BINGO_N))
    rng.shuffle(idxs)
    picked = idxs[:24]
    positions = []
    pi = 0
    for pos in range(25):
        if pos == 12:
            positions.append(None)
        else:
            positions.append(picked[pi])
            pi += 1
    return positions


def bingo_marks_for(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_idx FROM bingo_marks WHERE pid = %s", (pid,))
            return set(i for (i,) in cur.fetchall())


def bingo_marked(positions, marked_set):
    return [(pos == 12) or (positions[pos] is not None and positions[pos] in marked_set) for pos in range(25)]


def bingo_has_line(marked):
    for line in BINGO_LINES:
        if all(marked[p] for p in line):
            return True
    return False


def bingo_is_full(marked):
    return all(marked)


def bingo_toggle_mark(pid, item_idx):
    if item_idx is None or item_idx < 0 or item_idx >= BINGO_N:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM bingo_marks WHERE pid = %s AND item_idx = %s", (pid, item_idx))
            exists = cur.fetchone() is not None
            if exists:
                cur.execute("DELETE FROM bingo_marks WHERE pid = %s AND item_idx = %s", (pid, item_idx))
            else:
                cur.execute(
                    "INSERT INTO bingo_marks (pid, item_idx) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (pid, item_idx),
                )
        conn.commit()


def bingo_record_done_if_full(pid):
    st = bingo_get_state()
    nonce = st["nonce"]
    positions = bingo_card_positions(pid, nonce)
    marked = bingo_marked(positions, bingo_marks_for(pid))
    full = bingo_is_full(marked)
    if full and pid != PREVIEW_PID:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO bingo_done (pid, nonce) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (pid, nonce),
                )
            conn.commit()
    return full


def bingo_name_for(pid):
    for rid, first, last, company, email in ROSTER:
        if rid == pid:
            return first + " " + last
    return None


def bingo_pending_celebration():
    st = bingo_get_state()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pid FROM bingo_done WHERE nonce = %s AND announced = FALSE ORDER BY done_at LIMIT 1",
                (st["nonce"],),
            )
            row = cur.fetchone()
    if not row:
        return None
    return bingo_name_for(row[0])


def bingo_announce_next():
    st = bingo_get_state()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pid FROM bingo_done WHERE nonce = %s AND announced = FALSE ORDER BY done_at LIMIT 1",
                (st["nonce"],),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE bingo_done SET announced = TRUE WHERE pid = %s AND nonce = %s",
                    (row[0], st["nonce"]),
                )
        conn.commit()


def bingo_done_names():
    st = bingo_get_state()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pid FROM bingo_done WHERE nonce = %s ORDER BY done_at",
                (st["nonce"],),
            )
            pids = [p for (p,) in cur.fetchall()]
    return [bingo_name_for(p) for p in pids if bingo_name_for(p)]


def bingo_new_game():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bingo_marks")
            cur.execute("DELETE FROM bingo_done")
            cur.execute("DELETE FROM bingo_called")
            cur.execute("UPDATE bingo_state SET nonce = nonce + 1, winner_pid = NULL WHERE id = 1")
        conn.commit()


def bingo_host_public():
    return {
        "celebrate": bingo_pending_celebration(),
        "done": bingo_done_names(),
    }


# ----- Your Recap, the per person end of course review -----
def get_note(pid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT note FROM instructor_notes WHERE pid = %s", (pid,))
            row = cur.fetchone()
            return row[0] if row and row[0] else None


def set_note(pid, note):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO instructor_notes (pid, note) VALUES (%s, %s)
                ON CONFLICT (pid) DO UPDATE SET note = EXCLUDED.note
            """, (pid, note))
        conn.commit()


def notes_map():
    out = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pid, note FROM instructor_notes")
            for pid, note in cur.fetchall():
                out[pid] = note
    return out


def review_bundle(pid):
    row = identity_for(pid)
    if not row:
        return None
    rid, first, last, company, email = row
    name = (first + " " + last).strip()
    first_by_id = {r[0]: r[1] + " " + r[2] for r in ROSTER}

    counts = tally_for(pid)
    primary, blend, answered = lean_from_counts(counts)
    disc = None
    if answered > 0:
        disc = {
            "primary": primary,
            "primary_name": LEAN[primary]["name"],
            "blend_name": LEAN[blend]["name"] if blend else None,
            "lead": LEAN[primary]["lead"],
            "stretch": LEAN[primary]["stretch"],
        }

    rc = get_response(pid, "rollcall")
    driver = DRIVER_LABEL.get(rc.get("driver")) if rc else None

    bt = get_response(pid, "breakthrough")
    breakthrough = None
    if bt and (bt.get("action") or "").strip():
        breakthrough = {"person": bt.get("person", ""), "breakthrough": bt.get("breakthrough", ""), "action": bt.get("action", "")}

    wv = get_response(pid, "worryvault")
    worry = wv.get("note") if wv and (wv.get("note") or "").strip() else None

    quizzes = []
    for key in ("namegame", "pegquiz", "taketheturn"):
        r = get_response(pid, key)
        if r and r.get("score") is not None:
            try:
                quizzes.append({"title": QUIZ_BANKS[key]["title"], "score": int(r["score"]), "total": int(r.get("total", 0))})
            except (TypeError, ValueError):
                pass

    rg = get_response(pid, "recognition")
    recognition_given = None
    if rg and (rg.get("note") or "").strip() and rg.get("to") in first_by_id:
        recognition_given = {"to": first_by_id.get(rg["to"], ""), "note": rg["note"]}
    recognition_received = []
    for oid, ofirst, olast, ocompany, oemail in ROSTER:
        if oid == pid:
            continue
        orr = get_response(oid, "recognition")
        if orr and orr.get("to") == pid and (orr.get("note") or "").strip():
            recognition_received.append({"from": ofirst + " " + olast, "note": orr["note"]})

    pdr = principledraw_for(pid)
    principle = pdr["text"] if pdr else None

    return {
        "name": name,
        "email": email,
        "disc": disc,
        "driver": driver,
        "breakthrough": breakthrough,
        "worry": worry,
        "quizzes": quizzes,
        "recognition_given": recognition_given,
        "recognition_received": recognition_received,
        "principle": principle,
        "note": get_note(pid),
    }


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>CourseLive</title>
<link rel="icon" href="/brand/icon.png">
<link rel="apple-touch-icon" href="/brand/icon.png">
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
  .bgrid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; }
  .bcell { background: #f4f6f8; border: 1px solid #e0e6ec; border-radius: 8px; min-height: 62px; padding: 4px 3px; font-size: 10px; font-weight: 500; color: #33475b; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 1.15; }
  .bcell.on { background: #0d9488; border-color: #0d9488; color: #ffffff; font-weight: 600; }
  .bcell.free { background: #d4a017; border-color: #d4a017; color: #3d2c00; font-weight: 700; }
  .bcell.tap { cursor: pointer; touch-action: manipulation; -webkit-tap-highlight-color: rgba(13,148,136,0.25); }
  .bcell.tap:active { transform: scale(0.96); }
  #bingobtn { position: fixed; right: 16px; bottom: 16px; z-index: 40; background: #d4a017; color: #3d2c00; border: none; border-radius: 999px; padding: 13px 20px; font-size: 15px; font-weight: 700; font-family: inherit; box-shadow: 0 4px 14px rgba(15,41,66,0.28); cursor: pointer; touch-action: manipulation; }
  #bingobtn:active { transform: scale(0.97); }
  #bingoover { position: fixed; inset: 0; z-index: 60; background: #0f2942; overflow-y: auto; }
  #bingoover .bwrap { max-width: 520px; margin: 0 auto; padding: 16px 16px 40px; }
  #bingoover .bhead { display: flex; align-items: center; justify-content: space-between; padding: 6px 0 12px; }
  #bingoover .bhead .bt { color: #fff; font-size: 18px; font-weight: 700; }
  #bingoover .bback { background: #fff; color: #0f2942; border: none; border-radius: 10px; padding: 10px 16px; font-size: 14px; font-weight: 600; font-family: inherit; cursor: pointer; touch-action: manipulation; }
  #bingoover .bhint { color: #9fe1cb; font-size: 13px; line-height: 1.5; margin: 0 0 12px; }
  #bingoover .bnote { background: #12324f; border-radius: 10px; padding: 12px 14px; color: #fff; text-align: center; margin-bottom: 12px; }
  #bingoover .bnote .n1 { font-size: 17px; font-weight: 700; margin-bottom: 2px; }
  #bingoover .bnote .n2 { font-size: 13px; color: #cfe6de; }
  #bingoover .bnote.win { background: #d4a017; color: #3d2c00; }
  #bingoover .bnote.win .n2 { color: #5a4200; }
  #bingoover .bcell { min-height: 74px; font-size: 11px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="ribbon" id="ribbon" style="display:none">PREVIEW MODE, this run is not counted</div>
  <div class="card">
    <div class="head">
      <img src="/brand/logo.png" alt="Dale Carnegie Nevada" style="height:26px;display:block;margin-bottom:10px">
      <h1 id="title">CourseLive</h1>
      <div class="sub" id="sub">Dale Carnegie Course, Reno</div>
      <div class="bar"><div class="fill" id="fill"></div></div>
    </div>
    <div class="body" id="body"></div>
  </div>
  <button id="bingobtn" onclick="openBingo()" style="display:none">My Bingo</button>
  <div id="bingoover" style="display:none">
    <div class="bwrap">
      <div class="bhead"><span class="bt">Your Bingo Card</span><button class="bback" onclick="closeBingo()">Back to class</button></div>
      <p class="bhint">Watch and listen across all three days. When you hear or use a principle or a skill on your card, tap that square. Fill the whole board for a shout out on the big screen.</p>
      <div id="bingonote"></div>
      <div class="bgrid" id="bingogrid"></div>
    </div>
  </div>
</div>
<script>
var QUESTIONS = __QUESTIONS__;
var LEAN = __LEAN__;
var UPSELL = __UPSELL__;
var DRIVERS = __DRIVERS__;
var SPOT_TITLES = __SPOT_TITLES__;
var QUIZBANKS = __QUIZBANKS__;
var CCLIONS = __CCLIONS__;
var IS_PREVIEW = __PREVIEW__;
var BOOTPID = __BOOTPID__;

var joined = IS_PREVIEW || (BOOTPID !== null && BOOTPID !== 0);
var renderedKey = null;
var lastRecStatus = null;
var qi = 0;
var recPeer = null;
var jTimer = null;
var jMounted = false;
var wnTimer = null;
var wnLastSig = "";
var quizKey = null;
var quizI = 0;
var quizScore = 0;
var quizBank = null;
var pdTimer = null;
var pdLastSig = "";
var ccTimer = null;
var ccLastSig = "";
var ccBusy = false;
var bgTimer = null;
var bgLastSig = "";

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
    if (res.ok){ joined = true; renderedKey = null; showBingoBtn(); tick(); }
  });
}

// ----- lobby, follows the active spot -----
function tick(){
  if (!joined){ return; }
  fetch("/state").then(function(r){ return r.json(); }).then(function(st){
    var changed = st.active !== renderedKey;
    var revealKey = (st.active === "recognition" || st.active === "breakthrough" || st.active === "worryvault" || st.active === "energizer");
    if (revealKey && st.status !== lastRecStatus){ changed = true; }
    if (revealKey){ lastRecStatus = st.status; }
    if (changed){
      renderedKey = st.active;
      renderSpot(st.active, st.status);
    }
  }).catch(function(){});
}

function renderSpot(key, status){
  if (jTimer && key !== "jeopardy"){ clearInterval(jTimer); jTimer = null; jMounted = false; }
  if (wnTimer && key !== "who_next"){ clearInterval(wnTimer); wnTimer = null; }
  if (pdTimer && key !== "principledraw"){ clearInterval(pdTimer); pdTimer = null; }
  if (ccTimer && key !== "clearcloudy"){ clearInterval(ccTimer); ccTimer = null; }
  if (key === "welcome"){ renderJoined(); return; }
  if (key === "holding"){ renderHoldScreen(); return; }
  if (key === "disc"){ startDisc(); return; }
  if (key === "rollcall"){ startRollcall(); return; }
  if (key === "jeopardy"){ startJeopardy(); return; }
  if (key === "who_next"){ startWhoNext(); return; }
  if (key === "review"){ startReview(); return; }
  if (key === "pegquiz" || key === "taketheturn" || key === "namegame"){ startQuiz(key); return; }
  if (key === "principledraw"){ startPrincipleDraw(); return; }
  if (key === "clearcloudy"){ startClearCloudy(); return; }
  if (key === "worryvault"){
    if (status === "locked"){ worryUp(); } else { startWorry(); }
    return;
  }
  if (key === "energizer"){
    if (status === "locked"){ energizerUp(); } else { startEnergizer(); }
    return;
  }
  if (key === "breakthrough"){
    if (status === "locked"){ breakthroughUp(); } else { startBreakthrough(); }
    return;
  }
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

function renderHoldScreen(){
  setBar(0);
  setTitle("CourseLive");
  el("sub").textContent = "";
  el("body").innerHTML =
    '<div class="hold">' +
    '<span class="tag">STAND BY</span>' +
    '<p class="big">Eyes on the front</p>' +
    '<p class="small">Keep this open. Your phone jumps back in the second we start the next one.</p>' +
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

// ----- Who's Next, the picker -----
function startWhoNext(){
  setTitle("Who's Next");
  setBar(0);
  el("sub").textContent = "Watch the screen";
  el("body").innerHTML = '<div id="wnbody"></div>';
  wnLastSig = "";
  wnPoll();
  if (wnTimer){ clearInterval(wnTimer); }
  wnTimer = setInterval(wnPoll, 1200);
}

function wnPoll(){
  fetch("/spot/whonext/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ return; }
    drawWhoNextMe(d);
  }).catch(function(){});
}

function drawWhoNextMe(d){
  var b = el("wnbody");
  if (!b){ return; }
  var sig = (d.you ? "Y" : "N") + "|" + (d.current_pid || 0);
  if (sig === wnLastSig){ return; }
  wnLastSig = sig;
  if (d.you){
    setBar(100);
    b.innerHTML = '<div class="hold"><span class="tag">YOUR TURN</span>' +
      '<p class="big">You are up</p>' +
      '<p class="small">Stand and take the floor. The room is with you.</p></div>';
  } else if (d.current_name){
    b.innerHTML = '<div class="hold"><span class="tag">WHO IS NEXT</span>' +
      '<p class="big">' + esc(d.current_name) + '</p>' +
      '<p class="small">All eyes up front. You could be next.</p></div>';
  } else {
    b.innerHTML = '<div class="hold"><span class="tag">WHO IS NEXT</span>' +
      '<p class="big">Get ready</p>' +
      '<p class="small">Your host is about to pick someone. It could be you.</p></div>';
  }
}

// ----- Breakthrough Board, commit to enhance relationships -----
function startBreakthrough(){
  setTitle("Breakthrough");
  setBar(0);
  el("sub").textContent = "Your commitment";
  fetch("/spot/breakthrough/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && mine.action){ breakthroughSent(); return; }
    el("body").innerHTML =
      '<p class="stem">Commit to one relationship breakthrough. Keep it specific.</p>' +
      '<textarea class="note" id="bwho" placeholder="Person at work I want a stronger relationship with"></textarea>' +
      '<textarea class="note" id="bwhat" placeholder="The breakthrough I want"></textarea>' +
      '<textarea class="note" id="baction" placeholder="What I will do differently, starting now"></textarea>' +
      '<button class="btn" onclick="sendBreakthrough()">Commit it</button>';
  });
}

function sendBreakthrough(){
  var person = (el("bwho").value || "").trim();
  var what = (el("bwhat").value || "").trim();
  var action = (el("baction").value || "").trim();
  if (!person || !what || !action){ el("sub").textContent = "Fill in all three"; return; }
  api("/spot/breakthrough/submit", {person: person, breakthrough: what, action: action}).then(function(res){
    if (res.ok){ breakthroughSent(); }
    else if (res.locked){ el("sub").textContent = "The board is closed now"; }
  });
}

function breakthroughSent(){
  setBar(100);
  el("sub").textContent = "Committed";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">COMMITTED</span>' +
    '<p class="big">Your commitment is in.</p>' +
    '<p class="small">We will put the board on the screen. Watch the main display.</p></div>';
}

function breakthroughUp(){
  setBar(100);
  el("sub").textContent = "On the screen";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">BREAKTHROUGH BOARD</span>' +
    '<p class="big">Look up at the screen.</p>' +
    '<p class="small">The commitments the room made are on the main display.</p></div>';
}

// ----- Self scored quiz engine, shared by Peg Quiz and Take the Turn -----
function startQuiz(key){
  quizKey = key;
  quizBank = QUIZBANKS[key];
  if (!quizBank){ renderHold(key); return; }
  setTitle(quizBank.title);
  setBar(0);
  el("sub").textContent = "Quick check";
  fetch("/spot/" + key + "/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && typeof mine.score === "number"){ quizResult(mine.score, mine.total); return; }
    quizI = 0; quizScore = 0; quizQuestion();
  }).catch(function(){ quizI = 0; quizScore = 0; quizQuestion(); });
}

function quizQuestion(){
  var q = quizBank.questions[quizI];
  el("sub").textContent = "Question " + (quizI + 1) + " of " + quizBank.questions.length;
  setBar(Math.round(quizI / quizBank.questions.length * 100));
  var opts = shuffle(q.options);
  var h = '<p class="stem">' + esc(q.stem) + '</p>';
  opts.forEach(function(o){
    h += '<div class="opt" data-correct="' + (o.correct ? "1" : "0") + '" onclick="quizAnswer(this)">' + esc(o.t) + '</div>';
  });
  el("body").innerHTML = h;
}

function quizAnswer(elm){
  var opts = document.querySelectorAll(".opt");
  for (var i = 0; i < opts.length; i++){ opts[i].onclick = null; }
  var correct = elm.getAttribute("data-correct") === "1";
  if (correct){ quizScore += 1; }
  for (var j = 0; j < opts.length; j++){
    if (opts[j].getAttribute("data-correct") === "1"){ opts[j].style.background = "#e1f5ee"; opts[j].style.borderColor = "#0d9488"; }
  }
  if (!correct){ elm.style.background = "#fbeef0"; elm.style.borderColor = "#c65b73"; }
  setTimeout(function(){
    quizI += 1;
    if (quizI >= quizBank.questions.length){ submitQuiz(); }
    else { quizQuestion(); }
  }, 700);
}

function submitQuiz(){
  setBar(100);
  el("sub").textContent = "Your score";
  api("/spot/" + quizKey + "/submit", {score: quizScore, total: quizBank.questions.length})
    .then(function(){ quizResult(quizScore, quizBank.questions.length); })
    .catch(function(){ quizResult(quizScore, quizBank.questions.length); });
}

function quizResult(score, total){
  setBar(100);
  el("sub").textContent = "Done";
  var pct = total ? Math.round(score / total * 100) : 0;
  var msg = pct >= 80 ? "Sharp. You know these." : (pct >= 50 ? "Good start. Run it again to lock them in." : "Keep at it. Repetition is the trick.");
  el("body").innerHTML =
    '<div class="center">' +
    '<div class="avatar" style="background:#0d9488">' + score + '</div>' +
    '<p style="font-size:20px;font-weight:600;margin:6px 0 2px">' + score + ' of ' + total + '</p>' +
    '<p style="font-size:13px;color:#5f6b76;margin:0 0 14px">' + esc(msg) + '</p></div>' +
    '<button class="btn ghost" onclick="retakeQuiz()">Try again</button>';
}

function retakeQuiz(){ quizI = 0; quizScore = 0; quizQuestion(); }

// ----- Worry Vault, anonymous stress in perspective -----
function startWorry(){
  setTitle("Worry Vault");
  setBar(0);
  el("sub").textContent = "In confidence";
  fetch("/spot/worryvault/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && mine.note){ worrySent(); return; }
    el("body").innerHTML =
      '<p class="stem">Name one worry or stress you have carried. It goes up anonymously, no name attached.</p>' +
      '<textarea class="note" id="worrynote" placeholder="A worry I have carried"></textarea>' +
      '<button class="btn" onclick="sendWorry()">Put it in the vault</button>';
  });
}

function sendWorry(){
  var note = (el("worrynote").value || "").trim();
  if (!note){ el("sub").textContent = "Add a short note"; return; }
  api("/spot/worryvault/submit", {note: note}).then(function(res){
    if (res.ok){ worrySent(); }
    else if (res.locked){ el("sub").textContent = "The vault is closed now"; }
  });
}

function worrySent(){
  setBar(100);
  el("sub").textContent = "In the vault";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">IN THE VAULT</span>' +
    '<p class="big">Your worry is in, anonymously.</p>' +
    '<p class="small">Watch the screen. You will see you are not carrying it alone.</p></div>';
}

function worryUp(){
  setBar(100);
  el("sub").textContent = "On the screen";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">WORRY VAULT</span>' +
    '<p class="big">Look up at the screen.</p>' +
    '<p class="small">The room put its worries up. None of them have names.</p></div>';
}

// ----- Energizer, one action word to light up your next report -----
function startEnergizer(){
  setTitle("Energizer");
  setBar(0);
  el("sub").textContent = "One word";
  fetch("/spot/energizer/mine").then(function(r){ return r.json(); }).then(function(mine){
    if (mine && mine.word){ energizerSent(); return; }
    el("body").innerHTML =
      '<p class="stem">Name one action word or move you will add to make your next report come alive.</p>' +
      '<input id="enword" maxlength="24" placeholder="Stand, point, pause, build..." style="width:100%;border:1px solid #d7dde3;border-radius:12px;padding:14px;font-size:16px;font-family:inherit;margin:4px 0 12px" />' +
      '<button class="btn gold" onclick="sendEnergizer()">Add it to the wall</button>';
  });
}

function sendEnergizer(){
  var w = (el("enword").value || "").trim();
  if (!w){ el("sub").textContent = "Add one word"; return; }
  api("/spot/energizer/submit", {word: w}).then(function(res){
    if (res.ok){ energizerSent(); }
    else if (res.locked){ el("sub").textContent = "Closed now"; }
  });
}

function energizerSent(){
  setBar(100);
  el("sub").textContent = "On the wall";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">ENERGIZED</span>' +
    '<p class="big">Your word is in.</p>' +
    '<p class="small">Watch the screen light up with the whole room.</p></div>';
}

function energizerUp(){
  setBar(100);
  el("sub").textContent = "On the screen";
  el("body").innerHTML =
    '<div class="hold"><span class="tag">ENERGIZER</span>' +
    '<p class="big">Look up at the screen.</p>' +
    '<p class="small">Bring one of these into your next report.</p></div>';
}

// ----- Principle Draw, deal a principle to each person -----
function startPrincipleDraw(){
  setTitle("Principle Draw");
  setBar(0);
  el("sub").textContent = "Your assignment";
  el("body").innerHTML = '<div id="pdbody"></div>';
  pdLastSig = "";
  pdPoll();
  if (pdTimer){ clearInterval(pdTimer); }
  pdTimer = setInterval(pdPoll, 1400);
}

function pdPoll(){
  fetch("/spot/principledraw/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ return; }
    var b = el("pdbody");
    if (!b){ return; }
    var sig = d.text || "none";
    if (sig === pdLastSig){ return; }
    pdLastSig = sig;
    if (d.text){
      setBar(100);
      b.innerHTML = '<div class="center"><span class="tag">YOUR PRINCIPLE</span></div>' +
        '<div class="box" style="background:#e1f5ee;margin-top:10px"><p class="txt" style="color:#0f6e56;font-size:16px;font-weight:500;line-height:1.5">' + esc(d.text) + '</p></div>' +
        '<p class="note">Use this in your two minute Magic Formula. Evidence, Action, Benefit.</p>';
    } else {
      b.innerHTML = '<div class="hold"><span class="tag">PRINCIPLE DRAW</span>' +
        '<p class="big">Get ready</p>' +
        '<p class="small">Your host is about to deal everyone a principle. Watch the screen.</p></div>';
    }
  }).catch(function(){});
}

// ----- Clear or Cloudy, live LIONS feedback -----
function startClearCloudy(){
  setTitle("Clear or Cloudy");
  setBar(0);
  el("sub").textContent = "Rate the report";
  el("body").innerHTML = '<div id="ccbody"></div>';
  ccLastSig = "";
  ccBusy = false;
  ccPoll();
  if (ccTimer){ clearInterval(ccTimer); }
  ccTimer = setInterval(ccPoll, 1500);
}

function ccPoll(){
  if (ccBusy){ return; }
  fetch("/spot/clearcloudy/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ return; }
    var sig = d.status + "|" + (d.verdict || "none");
    if (sig === ccLastSig){ return; }
    ccLastSig = sig;
    drawClearCloudy(d);
  }).catch(function(){});
}

function drawClearCloudy(d){
  var b = el("ccbody");
  if (!b){ return; }
  if (d.status === "locked"){
    b.innerHTML = '<div class="hold"><span class="tag">CLEAR OR CLOUDY</span>' +
      '<p class="big">Voting closed</p><p class="small">Look at the screen for the room read.</p></div>';
    return;
  }
  if (d.verdict){
    b.innerHTML = '<div class="center" style="margin-bottom:8px"><span class="tag">COUNTED</span></div>' +
      '<p class="stem" style="text-align:center">You said ' + (d.verdict === "clear" ? "Clear" : "Cloudy") + '. Change it?</p>' +
      '<button class="btn" onclick="ccVote()">Clear</button>' +
      '<button class="btn gold" style="margin-top:10px" onclick="ccCloudy()">Cloudy</button>';
    return;
  }
  b.innerHTML = '<p class="stem">Was that report clear or cloudy?</p>' +
    '<button class="btn" onclick="ccVote()">Clear</button>' +
    '<button class="btn gold" style="margin-top:10px" onclick="ccCloudy()">Cloudy</button>';
}

function ccVote(){
  api("/spot/clearcloudy/submit", {verdict: "clear"}).then(function(){ ccLastSig = ""; ccPoll(); })
    .catch(function(){ ccLastSig = ""; ccPoll(); });
}

function ccCloudy(){
  ccBusy = true;
  var h = '<p class="stem">Cloudy. Which LIONS piece was missing most?</p>';
  CCLIONS.forEach(function(x){
    h += '<div class="opt" onclick="ccSubmitCloudy(\\'' + x.key + '\\')">' + esc(x.label) + '</div>';
  });
  h += '<button class="btn ghost" onclick="ccBack()">Back</button>';
  el("ccbody").innerHTML = h;
}

function ccBack(){ ccBusy = false; ccLastSig = ""; ccPoll(); }

function ccSubmitCloudy(k){
  ccBusy = false;
  api("/spot/clearcloudy/submit", {verdict: "cloudy", lions: k}).then(function(){ ccLastSig = ""; ccPoll(); })
    .catch(function(){ ccLastSig = ""; ccPoll(); });
}

// ----- Principle Bingo, always on self marked card -----
function showBingoBtn(){ var b = el("bingobtn"); if (b){ b.style.display = joined ? "block" : "none"; } }

function openBingo(){
  el("bingoover").style.display = "block";
  loadBingoCard();
}

function closeBingo(){ el("bingoover").style.display = "none"; }

function loadBingoCard(){
  fetch("/bingo/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ return; }
    renderBingoCard(d);
  }).catch(function(){});
}

function renderBingoCard(d){
  var cells = d.cells || [];
  var marked = d.marked || [];
  var note = el("bingonote");
  if (d.full){
    note.innerHTML = '<div class="bnote win"><div class="n1">You filled your whole card</div><div class="n2">Watch the big screen for your shout out</div></div>';
  } else if (d.has_line){
    note.innerHTML = '<div class="bnote"><div class="n1">Nice, you have a line</div><div class="n2">Keep going, fill every square for the celebration</div></div>';
  } else {
    note.innerHTML = '';
  }
  var h = '';
  for (var i = 0; i < 25; i++){
    var free = (i === 12);
    var cls = 'bcell' + (marked[i] ? ' on' : '') + (free ? ' free' : ' tap');
    var label = free ? 'FREE' : esc(cells[i] || '');
    if (free){
      h += '<div class="' + cls + '">' + label + '</div>';
    } else {
      h += '<div class="' + cls + '" onclick="markBingo(' + i + ')">' + label + '</div>';
    }
  }
  el("bingogrid").innerHTML = h;
}

function markBingo(pos){
  api("/bingo/mark", {pos: pos}).then(function(d){
    if (!d || d.ok === false){ return; }
    renderBingoCard(d);
  }).catch(function(){});
}

// ----- Your Recap -----
function startReview(){
  setTitle("Your Recap");
  setBar(100);
  el("sub").textContent = "Your three days";
  el("body").innerHTML = '<div class="hold"><p class="small">Loading your recap...</p></div>';
  fetch("/spot/review/me").then(function(r){ return r.json(); }).then(function(d){
    if (!d || d.ok === false){ el("body").innerHTML = '<div class="hold"><p class="small">Could not load your recap.</p></div>'; return; }
    drawReview(d);
  }).catch(function(){ el("body").innerHTML = '<div class="hold"><p class="small">Could not load your recap.</p></div>'; });
}

function reviewSection(label, inner, bg){
  return '<div class="box" style="background:' + (bg || "#f4f6f8") + '"><p class="lbl">' + esc(label) + '</p>' + inner + '</div>';
}

function drawReview(d){
  var h = '<div class="center"><span class="tag">YOUR RECAP</span>' +
    '<p style="font-size:20px;font-weight:600;margin:6px 0 2px">' + esc(d.name) + '</p>' +
    '<p style="font-size:13px;color:#5f6b76;margin:0 0 14px">Your three days, in one place</p></div>';
  if (d.note){
    h += reviewSection("A note from your instructor", '<p class="txt">' + esc(d.note) + '</p>', "#faeeda");
  }
  if (d.disc){
    var lean = d.disc.blend_name ? (d.disc.primary_name + " and " + d.disc.blend_name) : d.disc.primary_name;
    h += reviewSection("Your DISC lean",
      '<p class="txt"><strong>' + esc(lean) + '</strong></p>' +
      '<p class="txt" style="margin-top:6px">You lead with ' + esc(d.disc.lead) + '. Your stretch is ' + esc(d.disc.stretch) + '</p>', "#e1f5ee");
  }
  if (d.driver){
    h += reviewSection("The driver you chose to grow", '<p class="txt">' + esc(d.driver) + '</p>');
  }
  if (d.breakthrough){
    h += reviewSection("Your relationship breakthrough",
      '<p class="txt"><strong>' + esc(d.breakthrough.person) + '</strong></p>' +
      '<p class="txt" style="margin-top:4px">' + esc(d.breakthrough.breakthrough) + '</p>' +
      '<p class="txt" style="margin-top:4px">You will: ' + esc(d.breakthrough.action) + '</p>');
  }
  if (d.principle){
    h += reviewSection("Your assigned principle", '<p class="txt">' + esc(d.principle) + '</p>');
  }
  if (d.quizzes && d.quizzes.length){
    var qi = "";
    d.quizzes.forEach(function(q){ qi += '<p class="txt">' + esc(q.title) + ': ' + q.score + ' of ' + q.total + '</p>'; });
    h += reviewSection("Your quiz scores", qi);
  }
  if (d.recognition_given){
    h += reviewSection("Recognition you gave", '<p class="txt">To ' + esc(d.recognition_given.to) + ': ' + esc(d.recognition_given.note) + '</p>');
  }
  if (d.recognition_received && d.recognition_received.length){
    var ri = "";
    d.recognition_received.forEach(function(r){ ri += '<p class="txt">' + esc(r.note) + ' <em style="color:#8a97a3">from ' + esc(r.from) + '</em></p>'; });
    h += reviewSection("Recognition you received", ri, "#e1f5ee");
  }
  if (d.worry){
    h += reviewSection("The worry you named, and can now let go", '<p class="txt">' + esc(d.worry) + '</p>');
  }
  h += '<button class="btn gold" id="recapbtn" onclick="emailRecap()">Email my recap to me</button>';
  el("body").innerHTML = h;
}

function emailRecap(){
  var b = el("recapbtn");
  b.textContent = "Sending...";
  api("/spot/review/email", {}).then(function(res){
    if (res.ok){ b.textContent = "Sent to your inbox"; b.style.background = "#0d9488"; b.style.color = "#fff"; }
    else { b.textContent = "Could not send, try again"; }
  }).catch(function(){ b.textContent = "Could not send, try again"; });
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

var discBusy = false;
function answer(letter){
  if (discBusy){ return; }
  discBusy = true;
  api("/answer", {qnum: qi, letter: letter}).then(function(res){
    discBusy = false;
    if (res && res.ok === false && res.locked){ el("sub").textContent = "Closed for now"; return; }
    qi += 1;
    if (qi >= QUESTIONS.length){ loadResult(); }
    else { renderQuestion(); }
  }).catch(function(){ discBusy = false; });
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
showBingoBtn();
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
<link rel="icon" href="/brand/icon.png">
<link rel="apple-touch-icon" href="/brand/icon.png">
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
  .welcome { background: #0f2942; color: #fff; padding: 26px 26px 22px; }
  .weltop { display: grid; grid-template-columns: 232px 1fr; gap: 26px; align-items: center; }
  .welcome.full .weltop { grid-template-columns: 108px 1fr; }
  .weljoin { background: #fff; border-radius: 12px; padding: 18px; text-align: center; }
  .weljlab { font-size: 12px; font-weight: 600; letter-spacing: 2px; color: #0d6e63; text-transform: uppercase; margin-bottom: 12px; }
  .welqr { width: 152px; height: 152px; display: block; margin: 0 auto; border-radius: 8px; }
  .welcome.full .welqr { width: 76px; height: 76px; }
  .weljtype { font-size: 12px; color: #5f6b76; margin: 14px 0 6px; }
  .wellink { font-size: 13px; font-weight: 600; color: #0f2942; background: #eef2f5; border-radius: 8px; padding: 8px 8px; word-break: break-all; }
  .welcome.full .weljlab, .welcome.full .weljtype, .welcome.full .wellink { display: none; }
  .welright { text-align: left; }
  .weleyebrow { font-size: 13px; font-weight: 600; letter-spacing: 3px; color: #d4a017; text-transform: uppercase; margin-bottom: 14px; }
  .welline { font-size: 30px; font-weight: 600; line-height: 1.28; color: #fff; transition: opacity 0.6s ease; min-height: 80px; }
  .welrule { width: 56px; height: 3px; background: #d4a017; border-radius: 2px; margin: 20px 0 0; }
  .weldate { font-size: 14px; letter-spacing: 1px; color: #9fb3c8; margin-top: 14px; }
  .weltray { border-top: 1px solid #17324c; margin-top: 22px; padding-top: 16px; }
  .weltraylab { font-size: 12px; font-weight: 600; letter-spacing: 2px; color: #7fa0bd; text-transform: uppercase; margin-bottom: 12px; }
  .welchips { display: flex; flex-wrap: wrap; gap: 10px; }
  .welchip { display: inline-flex; align-items: center; gap: 8px; background: #14324e; border-radius: 20px; padding: 8px 16px; font-size: 16px; color: #fff; }
  .welchip .cd { width: 8px; height: 8px; border-radius: 50%; background: #2dd4bf; }
  .welchip.pop { animation: wnpop 0.5s cubic-bezier(0.2, 1.4, 0.4, 1); }
  .welghost { display: inline-flex; align-items: center; background: transparent; border: 1px dashed #2c4864; border-radius: 20px; padding: 8px 16px; font-size: 15px; color: #3f5f7d; }
  .holdhero { background: #0f2942; padding: 74px 44px; text-align: center; display: flex; align-items: center; justify-content: center; min-height: 320px; }
  .hhwrap { max-width: 860px; }
  .hheyebrow { font-size: 14px; font-weight: 600; letter-spacing: 3px; color: #d4a017; text-transform: uppercase; margin-bottom: 26px; }
  .hhquote { font-size: 34px; line-height: 1.32; font-weight: 600; color: #fff; transition: opacity 0.6s ease; min-height: 90px; }
  .hhrule { width: 64px; height: 3px; background: #d4a017; border-radius: 2px; margin: 30px auto 0; }
  .hhfoot { font-size: 14px; letter-spacing: 1px; color: #9fb3c8; margin-top: 22px; }
  .hhdot { display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: #d4a017; margin: 0 12px; vertical-align: middle; }
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
  .qlist { padding: 8px 22px 24px; max-width: 560px; margin: 0 auto; }
  .qrow { display: flex; justify-content: space-between; align-items: center; padding: 11px 14px; border-bottom: 1px solid #e6ebef; }
  .qrow .qn { font-size: 16px; font-weight: 500; color: #0f2942; }
  .qrow .qs { font-size: 16px; font-weight: 700; color: #0d6e63; }
  .pdlist { padding: 14px 20px 22px; }
  .pdrow { display: flex; align-items: baseline; gap: 12px; padding: 10px 0; border-bottom: 1px solid #e6ebef; }
  .pdrow .pdn { flex: 0 0 150px; font-size: 15px; font-weight: 600; color: #0f2942; }
  .pdrow .pdp { font-size: 15px; color: #274766; line-height: 1.4; }
  .cc { padding: 20px 22px 26px; }
  .ccrow { margin-bottom: 14px; }
  .ccrow .cctl { font-size: 15px; font-weight: 500; margin-bottom: 5px; display: flex; justify-content: space-between; }
  .cctrack { height: 20px; background: #e6ebef; border-radius: 6px; overflow: hidden; }
  .ccfill { height: 20px; border-radius: 6px; width: 0%; transition: width 0.4s; }
  .cclab { font-size: 13px; font-weight: 600; color: #5f6b76; text-transform: uppercase; letter-spacing: 0.5px; margin: 16px 0 10px; }
  .bgstage { padding: 22px 22px 28px; }
  .bgstage .lab { font-size: 13px; font-weight: 600; letter-spacing: 2px; color: #0d6e63; text-transform: uppercase; text-align: center; }
  .bglast { text-align: center; background: #0f2942; border-radius: 12px; padding: 22px; margin: 12px 0 16px; }
  .bglast .ls { font-size: 13px; color: #d4a017; font-weight: 600; letter-spacing: 1px; }
  .bglast .lt { font-size: 26px; color: #fff; font-weight: 600; margin-top: 6px; line-height: 1.3; }
  .bgcalled { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
  .bgchip { background: #e1f5ee; color: #0d6e63; border-radius: 999px; padding: 7px 14px; font-size: 14px; font-weight: 500; }
  .bgwin { text-align: center; padding: 42px 24px; }
  .bgwin .wl { font-size: 14px; font-weight: 600; letter-spacing: 2px; color: #d4a017; text-transform: uppercase; }
  .bgwin .wn { font-size: 42px; font-weight: 700; color: #0f2942; margin-top: 12px; }
  .enwall { padding: 22px 22px 28px; display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; align-items: center; }
  .enchip { background: #0d9488; color: #fff; border-radius: 14px; padding: 14px 20px; font-size: 22px; font-weight: 700; display: flex; flex-direction: column; align-items: center; line-height: 1.1; }
  .enchip:nth-child(even) { background: #d4a017; color: #3d2c00; }
  .enchip:nth-child(3n) { background: #3aa9c9; color: #fff; }
  .enchip .enname { font-size: 12px; font-weight: 500; opacity: 0.85; margin-top: 4px; }
  .wnstage { padding: 46px 24px; text-align: center; }
  .wnstage .lab { font-size: 13px; font-weight: 600; letter-spacing: 2px; color: #0d6e63; text-transform: uppercase; }
  .wnstage .name { font-size: 46px; font-weight: 700; color: #0f2942; margin: 14px 0 8px; line-height: 1.1; }
  .wnstage .rem { font-size: 14px; color: #5f6b76; }
  .wnstage .waiting { font-size: 30px; font-weight: 600; color: #5f6b76; margin: 14px 0; }
  .wnname { font-size: 54px; font-weight: 700; color: #0f2942; margin: 20px 0 10px; line-height: 1.06; min-height: 62px; }
  .wnname.pop { color: #0d9488; animation: wnpop 0.5s cubic-bezier(0.2, 1.4, 0.4, 1); }
  .wnsub { font-size: 15px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #d4a017; min-height: 20px; }
  @keyframes wnpop { 0% { transform: scale(0.7); opacity: 0.35; } 60% { transform: scale(1.12); } 100% { transform: scale(1); opacity: 1; } }
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
  #celebrate { position: fixed; inset: 0; z-index: 90; background: #0f2942; display: none; align-items: center; justify-content: center; }
  #celebrate.on { display: flex; }
  #celebrate .cbox { text-align: center; padding: 40px; animation: cpop 0.5s ease; }
  #celebrate .cband { font-size: 34px; font-weight: 700; letter-spacing: 3px; color: #d4a017; text-transform: uppercase; margin-bottom: 18px; }
  #celebrate .cname { font-size: 84px; font-weight: 700; color: #fff; line-height: 1.05; margin-bottom: 18px; }
  #celebrate .csub { font-size: 30px; color: #9fe1cb; }
  @keyframes cpop { 0% { transform: scale(0.7); opacity: 0; } 60% { transform: scale(1.06); } 100% { transform: scale(1); opacity: 1; } }
</style>
</head>
<body>
<div class="wrap">
  <div class="stage">
    <div class="head"><span style="display:flex;align-items:center;gap:12px"><img src="/brand/logo.png" alt="Dale Carnegie Nevada" style="height:24px"><span class="ttl" id="stitle">CourseLive</span></span><span class="cnt" id="cnt"></span></div>
    <div id="stagebody"></div>
  </div>
</div>
<div id="celebrate"><div class="cbox"><div class="cband">Bingo</div><div class="cname" id="celname"></div><div class="csub">filled the whole card, congratulations</div></div></div>
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
var welLineTimer = null;
var welLineOrder = [];
var welLineIdx = 0;
var welJoinedSig = "";
var welShown = {};
var welFull = false;

function mountWelcome(){
  byid("stagebody").innerHTML =
    '<div class="welcome" id="welroot">' +
    '<div class="weltop">' +
    '<div class="weljoin">' +
    '<div class="weljlab">Scan to join</div>' +
    '<img class="welqr" src="/brand/joinqr.svg" alt="Scan to join CourseLive">' +
    '<div class="weljtype">Or type it in</div>' +
    '<div class="wellink">courselive-production.up.railway.app</div>' +
    '</div>' +
    '<div class="welright">' +
    '<div class="weleyebrow">The Dale Carnegie Course</div>' +
    '<div class="welline" id="welline"></div>' +
    '<div class="welrule"></div>' +
    '<div class="weldate">Reno, Nevada<span class="hhdot"></span>July 14 to 16, 2026</div>' +
    '</div>' +
    '</div>' +
    '<div class="weltray">' +
    '<div class="weltraylab">In the room</div>' +
    '<div class="welchips" id="welchips"></div>' +
    '</div>' +
    '</div>';
  welcomeMounted = true;
  welShown = {};
  welJoinedSig = "";
  welFull = false;
  welLineOrder = shuffleArr(HOLD_LINES);
  welLineIdx = 0;
  var ln = byid("welline");
  if (ln){ ln.textContent = welLineOrder[0]; ln.style.opacity = 1; }
  if (welLineTimer){ clearInterval(welLineTimer); }
  welLineTimer = setInterval(rotateWelLine, 8000);
}

function rotateWelLine(){
  var ln = byid("welline");
  if (!ln){ return; }
  ln.style.opacity = 0;
  setTimeout(function(){
    welLineIdx = welLineIdx + 1;
    if (welLineIdx >= welLineOrder.length){ welLineOrder = shuffleArr(HOLD_LINES); welLineIdx = 0; }
    ln.textContent = welLineOrder[welLineIdx];
    ln.style.opacity = 1;
  }, 600);
}

var HOLD_LINES = [
  "Do not criticize, condemn, or complain.",
  "Give honest, sincere appreciation.",
  "Arouse in the other person an eager want.",
  "Become genuinely interested in other people.",
  "Smile.",
  "Remember that a person's name is, to them, the sweetest sound in any language.",
  "Be a good listener. Encourage others to talk about themselves.",
  "Talk in terms of the other person's interests.",
  "Make the other person feel important, and do it sincerely.",
  "The only way to get the best of an argument is to avoid it.",
  "Show respect for the other person's opinions.",
  "If you are wrong, admit it quickly and emphatically.",
  "Begin in a friendly way.",
  "Get the other person saying yes, yes, right away.",
  "Let the other person do a great deal of the talking.",
  "Let the other person feel the idea is theirs.",
  "Try honestly to see things from the other person's point of view.",
  "Be sympathetic with the other person's ideas and desires.",
  "Appeal to the nobler motives.",
  "Dramatize your ideas.",
  "Throw down a challenge.",
  "Begin with praise and honest appreciation.",
  "Call attention to mistakes indirectly.",
  "Talk about your own mistakes before criticizing the other person.",
  "Ask questions instead of giving direct orders.",
  "Let the other person save face.",
  "Praise the slightest improvement and praise every improvement.",
  "Give the other person a fine reputation to live up to.",
  "Use encouragement. Make the fault seem easy to correct.",
  "Make the other person happy about doing what you suggest.",
  "Act enthusiastic and you will be enthusiastic.",
  "Discouragement and failure are two of the surest stepping stones to success."
];
var holdMounted = false;
var holdTimer = null;
var holdIdx = 0;
var holdOrder = [];
var wnMounted = false;
var wnSeq = -1;
var wnAnimating = false;
var wnReelTimer = null;

function mountHolding(){
  byid("stagebody").innerHTML =
    '<div class="holdhero"><div class="hhwrap">' +
    '<div class="hheyebrow">The Dale Carnegie Course</div>' +
    '<div class="hhquote" id="hhquote"></div>' +
    '<div class="hhrule"></div>' +
    '<div class="hhfoot">Reno, Nevada<span class="hhdot"></span>July 14 to 16, 2026</div>' +
    '</div></div>';
  holdMounted = true;
  holdOrder = shuffleArr(HOLD_LINES);
  holdIdx = 0;
  var q = byid("hhquote");
  q.textContent = holdOrder[0];
  q.style.opacity = 1;
  if (holdTimer){ clearInterval(holdTimer); }
  holdTimer = setInterval(rotateHold, 8000);
}

function rotateHold(){
  var q = byid("hhquote");
  if (!q){ return; }
  q.style.opacity = 0;
  setTimeout(function(){
    holdIdx = holdIdx + 1;
    if (holdIdx >= holdOrder.length){ holdOrder = shuffleArr(HOLD_LINES); holdIdx = 0; }
    q.textContent = holdOrder[holdIdx];
    q.style.opacity = 1;
  }, 600);
}

function drawHolding(data){
  byid("cnt").textContent = "";
  if (holdMounted){ return; }
  mountHolding();
}

function drawWelcome(data){
  if (!welcomeMounted){ mountWelcome(); }
  var joined = data.joined || [];
  var n = joined.length;
  byid("cnt").textContent = n === 0 ? "Waiting for the room" : (n + " of 7 here");
  var full = (n >= 7);
  if (full !== welFull){
    welFull = full;
    var root = byid("welroot");
    if (root){ if (full){ root.classList.add("full"); } else { root.classList.remove("full"); } }
  }
  var sig = joined.map(function(p){ return p.id; }).join(",");
  if (sig === welJoinedSig){ return; }
  welJoinedSig = sig;
  var wrap = byid("welchips");
  if (!wrap){ return; }
  var h = "";
  joined.forEach(function(p){
    var isNew = !welShown[p.id];
    welShown[p.id] = true;
    h += '<span class="welchip' + (isNew ? " pop" : "") + '"><span class="cd"></span>' + esc(p.first) + '</span>';
  });
  var slots = 7 - n;
  for (var i = 0; i < slots; i++){
    h += '<span class="welghost">waiting</span>';
  }
  wrap.innerHTML = h;
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

function drawReviewStage(data){
  byid("cnt").textContent = "";
  byid("stagebody").innerHTML =
    '<div class="recintro"><div class="lab">YOUR RECAP</div>' +
    '<div class="big">Your three days are on your phone</div>' +
    '<div class="an">Scroll through everything you did, then tap Email my recap to keep it.</div></div>';
}

function drawEnergizer(data){
  if (data.status !== "locked"){
    var n = (data.energizer || []).length;
    byid("cnt").textContent = n + " of 7 in";
    byid("stagebody").innerHTML =
      '<div class="recintro"><div class="lab">ENERGIZER</div>' +
      '<div class="big">Energy is building</div>' +
      '<div class="an">When the room is ready, lock input to light up the wall.</div></div>';
    return;
  }
  byid("cnt").textContent = (data.energizer || []).length + " energizers";
  var h = '<div class="enwall">';
  (data.energizer || []).forEach(function(r){
    h += '<span class="enchip">' + esc(r.word) + '<span class="enname">' + esc(r.name) + '</span></span>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function drawBingo(data){
  var g = data.bingo || {};
  if (g.winner){
    byid("cnt").textContent = "";
    byid("stagebody").innerHTML = '<div class="bgwin"><div class="wl">Bingo</div><div class="wn">' + esc(g.winner) + '</div></div>';
    return;
  }
  byid("cnt").textContent = (g.count || 0) + " called";
  var h = '<div class="bgstage"><div class="lab">Principle Bingo</div>';
  if (g.last_text){
    h += '<div class="bglast"><div class="ls">Just called</div><div class="lt">' + esc(g.last_text) + '</div></div>';
  } else {
    h += '<div class="bglast"><div class="lt" style="color:#9fe1cb;font-size:20px">Call the first principle to begin</div></div>';
  }
  var chips = g.called_short || [];
  if (chips.length){
    h += '<div class="bgcalled">';
    chips.forEach(function(s){ h += '<span class="bgchip">' + esc(s) + '</span>'; });
    h += '</div>';
  }
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function drawPrincipleDraw(data){
  var p = data.principledraw || {};
  var rows = p.rows || [];
  byid("cnt").textContent = p.dealt ? (p.dealt + " dealt") : "";
  if (!rows.length){
    byid("stagebody").innerHTML =
      '<div class="recintro"><div class="lab">PRINCIPLE DRAW</div>' +
      '<div class="big">Ready to deal</div>' +
      '<div class="an">Deal the principles from the console. Each person gets one.</div></div>';
    return;
  }
  var h = '<div class="pdlist">';
  rows.forEach(function(r){
    h += '<div class="pdrow"><div class="pdn">' + esc(r.name) + '</div><div class="pdp">' + esc(r.text) + '</div></div>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function ccBarStage(label, count, max, color){
  var pct = Math.round(count / max * 100);
  return '<div class="ccrow"><div class="cctl"><span>' + esc(label) + '</span><span>' + count + '</span></div>' +
    '<div class="cctrack"><div class="ccfill" style="width:' + pct + '%;background:' + color + '"></div></div></div>';
}

function drawCloud(data){
  var t = data.clearcloudy || {clear: 0, cloudy: 0, total: 0, lions: []};
  byid("cnt").textContent = t.total + " of 7 in";
  var max = Math.max(t.clear, t.cloudy, 1);
  var h = '<div class="cc">';
  h += ccBarStage("Clear", t.clear, max, "#0d9488");
  h += ccBarStage("Cloudy", t.cloudy, max, "#d4a017");
  if (t.cloudy > 0){
    h += '<div class="cclab">Where it got cloudy</div>';
    var lmax = 1;
    (t.lions || []).forEach(function(x){ if (x.count > lmax){ lmax = x.count; } });
    (t.lions || []).forEach(function(x){ h += ccBarStage(x.label, x.count, lmax, "#3aa9c9"); });
  }
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function drawQuiz(data){
  var q = data.quiz || {};
  var rows = q.done || [];
  byid("cnt").textContent = rows.length + " of 7 done";
  var h = '<div class="recintro"><div class="lab">' + esc((q.title || "Quiz").toUpperCase()) + '</div>' +
    '<div class="big">' + (rows.length ? "Scores are coming in" : "Take the quiz on your phone") + '</div></div>';
  if (rows.length){
    var sorted = rows.slice().sort(function(a, b){ return b.score - a.score; });
    h += '<div class="qlist">';
    sorted.forEach(function(r){
      h += '<div class="qrow"><span class="qn">' + esc(r.name) + '</span><span class="qs">' + r.score + ' of ' + r.total + '</span></div>';
    });
    h += '</div>';
  }
  byid("stagebody").innerHTML = h;
}

function drawWorry(data){
  if (data.status !== "locked"){
    var n = (data.worry || []).length;
    byid("cnt").textContent = n + " of 7 in";
    byid("stagebody").innerHTML =
      '<div class="recintro"><div class="lab">WORRY VAULT</div>' +
      '<div class="big">The vault is filling</div>' +
      '<div class="an">When the room is ready, lock input on your phone to open the vault.</div></div>';
    return;
  }
  byid("cnt").textContent = (data.worry || []).length + " worries, no names";
  var h = '<div class="wall">';
  (data.worry || []).forEach(function(r){
    h += '<div class="rcard"><p class="rnote">' + esc(r.note) + '</p></div>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function mountWnStage(){
  byid("stagebody").innerHTML =
    '<div class="wnstage">' +
    '<div class="lab">Who is next</div>' +
    '<div class="wnname" id="wnname"></div>' +
    '<div class="wnsub" id="wnsub"></div>' +
    '</div>';
}

function showWnIdle(){
  var nm = byid("wnname");
  if (nm){ nm.classList.remove("pop"); nm.textContent = "Ready when you are"; }
  var sb = byid("wnsub");
  if (sb){ sb.textContent = ""; }
}

function showWnWinner(name){
  var nm = byid("wnname");
  if (nm){ nm.classList.remove("pop"); nm.textContent = name; }
  var sb = byid("wnsub");
  if (sb){ sb.textContent = "Take the floor"; }
}

function shuffleArr(a){
  var arr = a.slice();
  for (var i = arr.length - 1; i > 0; i--){
    var j = Math.floor(Math.random() * (i + 1));
    var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
  }
  return arr;
}

function runWnReel(w){
  wnAnimating = true;
  var reel = shuffleArr((w.names || []).map(function(n){ return n.first; }));
  if (!reel.length){ reel = [w.current_name]; }
  var winner = w.current_name;
  var nm = byid("wnname");
  var sb = byid("wnsub");
  if (sb){ sb.textContent = ""; }
  if (nm){ nm.classList.remove("pop"); }
  var i = 0;
  var delay = 55;
  var elapsed = 0;
  function tick(){
    if (nm){ nm.textContent = reel[i % reel.length]; }
    i++;
    elapsed += delay;
    if (elapsed > 1500){ delay += 36; }
    if (delay < 330){
      wnReelTimer = setTimeout(tick, delay);
    } else {
      wnReelTimer = null;
      if (nm){
        nm.textContent = winner;
        void nm.offsetWidth;
        nm.classList.add("pop");
      }
      if (sb){ sb.textContent = "Take the floor"; }
      wnAnimating = false;
    }
  }
  tick();
}

function drawWhoNext(data){
  var w = data.whonext || {};
  byid("cnt").textContent = w.total ? (w.remaining + " of " + w.total + " left this round") : "";
  if (!wnMounted){
    mountWnStage();
    wnMounted = true;
    wnSeq = (typeof w.seq === "number") ? w.seq : 0;
    if (w.current_name){ showWnWinner(w.current_name); } else { showWnIdle(); }
    return;
  }
  if (wnAnimating){ return; }
  var seq = (typeof w.seq === "number") ? w.seq : 0;
  if (w.current_name && seq !== wnSeq){
    wnSeq = seq;
    runWnReel(w);
    return;
  }
  wnSeq = seq;
  if (w.current_name){ showWnWinner(w.current_name); } else { showWnIdle(); }
}

function drawBreakthrough(data){
  if (data.status !== "locked"){
    var n = (data.breakthrough || []).length;
    byid("cnt").textContent = n + " of 7 committed";
    byid("stagebody").innerHTML =
      '<div class="recintro"><div class="lab">BREAKTHROUGH BOARD</div>' +
      '<div class="big">Commitments are coming in</div>' +
      '<div class="an">When the room is ready, lock input on your phone to reveal the board.</div></div>';
    return;
  }
  byid("cnt").textContent = (data.breakthrough || []).length + " commitments";
  var h = '<div class="wall">';
  (data.breakthrough || []).forEach(function(r){
    h += '<div class="rcard"><div class="rto">' + esc(r.name) + '</div>' +
      '<p class="rnote"><strong>' + esc(r.person) + '</strong></p>' +
      '<p class="rnote">' + esc(r.breakthrough) + '</p>' +
      '<p class="rnote">' + esc(r.action) + '<span class="rfrom">what I will do differently</span></p>' +
      '</div>';
  });
  h += '</div>';
  byid("stagebody").innerHTML = h;
}

function draw(data){
  var cel = byid("celebrate");
  if (data.bingo_celebrate){
    byid("celname").textContent = data.bingo_celebrate;
    cel.classList.add("on");
  } else {
    cel.classList.remove("on");
  }
  byid("stitle").textContent = (data.active === "holding") ? "" : data.title;
  if (data.active !== "welcome"){ welcomeMounted = false; if (welLineTimer){ clearInterval(welLineTimer); welLineTimer = null; } }
  if (data.active !== "holding"){ holdMounted = false; if (holdTimer){ clearInterval(holdTimer); holdTimer = null; } }
  if (data.active !== "who_next"){ wnMounted = false; wnAnimating = false; if (wnReelTimer){ clearTimeout(wnReelTimer); wnReelTimer = null; } }
  if (data.active === "holding"){ drawHolding(data); }
  else if (data.active === "welcome"){ drawWelcome(data); }
  else if (data.active === "disc"){ drawPlot(data); }
  else if (data.active === "rollcall"){ drawTally(data); }
  else if (data.active === "jeopardy"){ drawJeopardy(data); }
  else if (data.active === "who_next"){ drawWhoNext(data); }
  else if (data.active === "review"){ drawReviewStage(data); }
  else if (data.active === "pegquiz" || data.active === "taketheturn" || data.active === "namegame"){ drawQuiz(data); }
  else if (data.active === "principledraw"){ drawPrincipleDraw(data); }
  else if (data.active === "clearcloudy"){ drawCloud(data); }
  else if (data.active === "worryvault"){ drawWorry(data); }
  else if (data.active === "energizer"){ drawEnergizer(data); }
  else if (data.active === "breakthrough"){ drawBreakthrough(data); }
  else if (data.active === "recognition"){ drawRecognition(data); }
  else { drawNext(data); }
}

function poll(){
  fetch("/host/" + SECRET + "/data").then(function(r){ return r.json(); }).then(draw).catch(function(){});
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
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>CourseLive admin</title>
<link rel="icon" href="/brand/icon.png">
<link rel="apple-touch-icon" href="/brand/icon.png">
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
  .spot { border: 1px solid #d7dde3; border-radius: 10px; padding: 9px 11px; cursor: pointer; touch-action: manipulation; -webkit-tap-highlight-color: rgba(13,148,136,0.25); }
  .spot:active { transform: scale(0.97); }
  button, .toggle, .mini, .btn-wn { touch-action: manipulation; -webkit-tap-highlight-color: rgba(13,148,136,0.25); }
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
  .bgcall { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 6px; margin-top: 8px; }
  .bgc { border: 1px solid #d7dde3; background: #fff; border-radius: 8px; padding: 8px 10px; font-size: 12px; font-family: inherit; cursor: pointer; text-align: left; line-height: 1.2; }
  .bgc.called { background: #0d9488; color: #fff; border-color: #0d9488; }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div style="display:flex;align-items:center;gap:12px"><img src="/brand/logo.png" alt="Dale Carnegie Nevada" style="height:24px"><div><div class="t1">CourseLive admin</div><div class="t2" id="activeline">loading</div></div></div>
    <div class="row2">
      <button class="mini" onclick="clearPreview()">Clear preview</button>
    </div>
  </div>

  <h2>Active spot, tap one to put it on every phone</h2>
  <div class="panel">
    <div class="spotgrid" id="spotgrid"></div>
    <div class="statusline" id="statusline"></div>
    <div class="drill" style="margin-top:10px">Lock input closes the phones for the spot showing now. On Recognition, Breakthrough, Worry Vault, and Energizer that same button instead reveals the wall on the screen. Clear this spot wipes only the responses for the spot showing now and leaves every other spot and the recap untouched. Tap Holding between exercises to drop a quiet logo on the room screen and hold every phone.</div>
  </div>

  <div id="jsection" style="display:none">
    <h2>Quizo, the review board</h2>
    <div class="panel">
      <div id="jadmin"></div>
    </div>
  </div>

  <div id="wnsection" style="display:none">
    <h2>Who's Next</h2>
    <div class="panel">
      <div id="wnadmin"></div>
    </div>
  </div>

  <div id="pdsection" style="display:none">
    <h2>Principle Draw</h2>
    <div class="panel">
      <div id="pdadmin"></div>
    </div>
  </div>

  <div id="bgsection">
    <h2>Principle Bingo, running all three days</h2>
    <div class="panel">
      <div id="bgadmin"></div>
    </div>
  </div>

  <h2>The room</h2>
  <div class="panel">
    <table>
      <thead><tr><th>Name</th><th>In</th><th>DISC</th><th>Lean</th><th>Roll Call</th><th></th></tr></thead>
      <tbody id="rosterbody"></tbody>
    </table>
  </div>

  <h2>Notes for each person, for the recap</h2>
  <div class="panel">
    <div class="drill" style="margin-bottom:10px">Write a short personal note for each person. It shows on their phone in Your Recap at the end of the course. Do this the night before.</div>
    <div id="notesbody"></div>
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

var spotsSig = "";
var rosterSig = "";
var suppressSpotsUntil = 0;

function setActive(key){
  suppressSpotsUntil = Date.now() + 4000;
  var tiles = document.querySelectorAll("#spotgrid .spot");
  for (var i = 0; i < tiles.length; i++){
    if (tiles[i].getAttribute("data-key") === key){
      tiles[i].classList.add("active");
      var sk = tiles[i].querySelector(".sk");
      if (sk){ byid("activeline").textContent = "Active now, " + sk.textContent; }
    } else {
      tiles[i].classList.remove("active");
    }
  }
  post("/active", {key: key}).then(function(){ suppressSpotsUntil = 0; spotsSig = ""; load(); });
}
function toggleStatus(key, cur){ spotsSig = ""; post("/status", {key: key, status: (cur === "open" ? "locked" : "open")}).then(load); }
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

function drawSpots(d){
  if (Date.now() < suppressSpotsUntil){ return; }
  var sig = JSON.stringify(d.spots.map(function(s){ return [s.key, s.is_active, s.live, s.status]; })) + "|" + d.active_title;
  if (sig === spotsSig){ return; }
  spotsSig = sig;
  byid("activeline").textContent = "Active now, " + d.active_title;
  var h = "";
  d.spots.forEach(function(s){
    var cls = "spot" + (s.is_active ? " active" : "") + (s.live ? "" : " coming");
    var coming = s.live ? "" : '<div class="sc">COMING</div>';
    h += '<div class="' + cls + '" data-key="' + s.key + '" onclick="setActive(\\'' + s.key + '\\')">' +
         '<div class="sk">' + esc(s.title) + '</div>' +
         '<div class="sd">Day ' + (s.day === 0 ? "any" : s.day) + '</div>' + coming + '</div>';
  });
  byid("spotgrid").innerHTML = h;
  var st = d.spots.filter(function(s){ return s.is_active; })[0];
  var sl = "";
  if (st && st.key === "jeopardy"){
    sl = 'Quizo runs from the panel below. ' +
      '<button class="toggle" onclick="clearSpot(\\'jeopardy\\')">Reset Quizo</button>';
  } else if (st && st.key === "who_next"){
    sl = 'Who is Next runs from the panel below. ' +
      '<button class="toggle" onclick="clearSpot(\\'who_next\\')">Reset round</button>';
  } else if (st && st.key === "principledraw"){
    sl = 'Principle Draw runs from the panel below. ' +
      '<button class="toggle" onclick="clearSpot(\\'principledraw\\')">Clear the draw</button>';
  } else if (st && st.key === "bingo"){
    sl = 'Principle Bingo runs from the panel below. ' +
      '<button class="toggle" onclick="clearSpot(\\'bingo\\')">New game</button>';
  } else if (st && st.key === "clearcloudy"){
    var votingOpen = st.status === "open";
    sl = 'Voting is <strong>' + (votingOpen ? "open" : "closed") + '</strong> for Clear or Cloudy. ' +
      '<button class="toggle" onclick="toggleStatus(\\'clearcloudy\\',\\'' + st.status + '\\')">' +
      (votingOpen ? "Close voting" : "Open voting") + '</button> ' +
      '<button class="toggle" onclick="clearSpot(\\'clearcloudy\\')">New speaker</button>';
  } else if (st){
    var isReveal = (st.key === "recognition" || st.key === "breakthrough" || st.key === "worryvault" || st.key === "energizer");
    var noun = st.key === "breakthrough" ? "the board" : (st.key === "worryvault" ? "the vault" : "the wall");
    var openLbl = isReveal ? ("Reveal " + noun) : "Lock input";
    var lockLbl = isReveal ? ("Hide " + noun) : "Open input";
    var collecting = st.key === "breakthrough" ? "collecting commitments" : (st.key === "worryvault" ? "collecting worries" : (st.key === "energizer" ? "collecting energy" : "collecting notes"));
    var showing = st.key === "breakthrough" ? "board is showing" : (st.key === "worryvault" ? "vault is open" : (st.key === "energizer" ? "wall is up" : "wall is showing"));
    var stateLbl = isReveal
      ? (st.status === "open" ? collecting : showing)
      : (st.status === "open" ? "open" : "closed");
    sl = 'Status, <strong>' + stateLbl + '</strong> for ' + esc(d.active_title) + '. ' +
      '<button class="toggle" onclick="toggleStatus(\\'' + st.key + '\\',\\'' + st.status + '\\')">' +
      (st.status === "open" ? openLbl : lockLbl) + '</button> ' +
      '<button class="toggle" onclick="clearSpot(\\'' + st.key + '\\')">Clear this spot</button>';
  }
  byid("statusline").innerHTML = sl;
}

function drawRoster(d){
  var rsig = JSON.stringify(d.roster);
  if (rsig === rosterSig){ return; }
  rosterSig = rsig;
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

var wnAdminSig = "";
var pdAdminSig = "";
var bgAdminSig = "";
var notesBuilt = false;

function saveNote(pid){
  var t = byid("note_" + pid).value || "";
  var btn = byid("noteb_" + pid);
  if (btn){ btn.textContent = "Saving..."; }
  post("/note", {pid: pid, note: t}).then(function(){ if (btn){ btn.textContent = "Saved"; } });
}

function drawNotes(d){
  if (notesBuilt){ return; }
  notesBuilt = true;
  var notes = d.notes || {};
  var h = "";
  d.roster.forEach(function(p){
    var v = notes[p.id] || "";
    h += '<div style="margin-bottom:12px"><div style="font-size:13px;font-weight:500;margin-bottom:4px">' + esc(p.name) + '</div>' +
      '<textarea id="note_' + p.id + '" style="width:100%;border:1px solid #d7dde3;border-radius:8px;padding:8px 10px;font-size:13px;font-family:inherit;min-height:56px;resize:vertical">' + esc(v) + '</textarea>' +
      '<button class="mini" id="noteb_' + p.id + '" style="margin-top:4px" onclick="saveNote(' + p.id + ')">Save note</button></div>';
  });
  byid("notesbody").innerHTML = h;
}

function pickNext(){ post("/whonext/pick", {}).then(function(){ wnAdminSig = ""; load(); }); }
function resetWhoNext(){ if (!confirm("Reset the round so everyone is eligible again?")) return; post("/whonext/reset", {}).then(function(){ wnAdminSig = ""; load(); }); }
function dealPrinciples(){ post("/principledraw/deal", {}).then(function(){ pdAdminSig = ""; load(); }); }
function resetPrincipleDraw(){ if (!confirm("Clear the current draw?")) return; post("/principledraw/reset", {}).then(function(){ pdAdminSig = ""; load(); }); }
function announceBingo(){ post("/bingo/announce", {}).then(function(){ bgAdminSig = ""; load(); }); }
function newBingo(){ if (!confirm("Start a new Bingo game? Everyone gets a fresh card and all marks are wiped.")) return; post("/bingo/new", {}).then(function(){ bgAdminSig = ""; load(); }); }

function drawBingoPanel(d){
  var g = d.bingo || {};
  var sig = JSON.stringify(g);
  if (sig === bgAdminSig){ return; }
  bgAdminSig = sig;
  var h = '';
  if (g.celebrate){
    h += '<div style="background:#fbf1d6;border:1px solid #d4a017;border-radius:10px;padding:14px;margin-bottom:12px">' +
         '<div style="font-size:16px;font-weight:700;margin-bottom:2px">' + esc(g.celebrate) + ' filled their card</div>' +
         '<div style="font-size:12px;color:#5f6b76;margin-bottom:10px">The room screen is showing the congratulations now. Celebrate them, then tap continue to clear it.</div>' +
         '<button onclick="announceBingo()" style="width:100%;background:#d4a017;color:#3d2c00;border:none;border-radius:10px;padding:14px;font-size:15px;font-weight:700;font-family:inherit;cursor:pointer">Congratulate and continue</button>' +
         '</div>';
  } else {
    h += '<div style="font-size:12px;color:#5f6b76;margin-bottom:10px">Players open My Bingo on their own phone and mark squares as the principles and skills come up across the three days. When someone fills their whole card, the room screen throws a congratulations and it shows up here. Everyone keeps their own card going.</div>';
  }
  var done = g.done || [];
  if (done.length){
    h += '<div style="font-size:12px;color:#5f6b76;margin-bottom:4px">Filled a full card so far</div>';
    h += '<div style="margin-bottom:10px">' + done.map(function(n){ return '<span style="display:inline-block;background:#e1f5ee;border-radius:999px;padding:4px 10px;font-size:12px;margin:0 6px 6px 0">' + esc(n) + '</span>'; }).join('') + '</div>';
  }
  h += '<div class="row2"><button class="mini warn" onclick="newBingo()">New game, fresh cards</button></div>';
  byid("bgadmin").innerHTML = h;
}

function drawPrincipleDrawAdmin(d){
  var p = d.principledraw || {};
  var sig = JSON.stringify(p);
  if (sig === pdAdminSig){ return; }
  pdAdminSig = sig;
  var h = '<button onclick="dealPrinciples()" style="width:100%;background:#0d9488;color:#fff;border:none;border-radius:12px;padding:16px;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer">Deal principles to the room</button>';
  h += '<div style="font-size:12px;color:#5f6b76;margin:10px 0 6px">' + (p.dealt || 0) + ' dealt. Dealing again reshuffles everyone.</div>';
  var rows = p.rows || [];
  if (rows.length){
    h += '<table><thead><tr><th>Name</th><th>Principle</th></tr></thead><tbody>';
    rows.forEach(function(r){ h += '<tr><td>' + esc(r.name) + '</td><td>' + esc(r.text) + '</td></tr>'; });
    h += '</tbody></table>';
  }
  h += '<div class="row2"><button class="mini" onclick="resetPrincipleDraw()">Clear the draw</button></div>';
  byid("pdadmin").innerHTML = h;
}

function drawWhoNextAdmin(d){
  var w = d.whonext || {};
  var sig = JSON.stringify(w);
  if (sig === wnAdminSig){ return; }
  wnAdminSig = sig;
  var doneNames = {};
  d.roster.forEach(function(p){ doneNames[p.id] = p.name; });
  var h = '';
  if (w.current_name){
    h += '<div style="text-align:center;margin-bottom:10px"><div style="font-size:12px;color:#5f6b76">On the floor now</div>' +
      '<div style="font-size:22px;font-weight:700">' + esc(w.current_name) + '</div></div>';
  } else {
    h += '<div style="text-align:center;margin-bottom:10px;color:#5f6b76">No one picked yet</div>';
  }
  h += '<button class="btn-wn" onclick="pickNext()" style="width:100%;background:#0d9488;color:#fff;border:none;border-radius:12px;padding:16px;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer">Generate</button>';
  h += '<div style="font-size:12px;color:#5f6b76;margin:10px 0 4px">' + (w.remaining || 0) + ' of ' + (w.total || 0) + ' left this round. The room screen runs the draw. Names do not repeat until all seven have had a turn.</div>';
  var done = w.done || [];
  if (done.length){
    h += '<div style="font-size:12px;color:#5f6b76;margin-bottom:6px">Already up: ';
    h += done.map(function(pid){ return esc(doneNames[pid] || ("id " + pid)); }).join(", ");
    h += '</div>';
  }
  h += '<button class="mini" onclick="resetWhoNext()">Reset round</button>';
  byid("wnadmin").innerHTML = h;
}

function load(){
  fetch("/host/" + SECRET + "/admin/data").then(function(r){ return r.json(); }).then(function(d){
    drawSpots(d);
    drawRoster(d);
    drawNotes(d);
    var js = byid("jsection");
    if (d.active === "jeopardy"){ js.style.display = "block"; drawJeopardyAdmin(d); }
    else { js.style.display = "none"; jAdminSig = ""; }
    var wns = byid("wnsection");
    if (d.active === "who_next"){ wns.style.display = "block"; drawWhoNextAdmin(d); }
    else { wns.style.display = "none"; wnAdminSig = ""; }
    var pds = byid("pdsection");
    if (d.active === "principledraw"){ pds.style.display = "block"; drawPrincipleDrawAdmin(d); }
    else { pds.style.display = "none"; pdAdminSig = ""; }
    drawBingoPanel(d);
  }).catch(function(){});
}

load();
setInterval(load, 2500);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Participant routes
# ---------------------------------------------------------------------------
def render_participant(is_preview):
    if is_preview:
        bootpid = PREVIEW_PID
    else:
        sp = session.get("pid")
        bootpid = sp if sp in ROSTER_IDS else None
    html = PAGE.replace("__QUESTIONS__", json.dumps(QUESTIONS))
    html = html.replace("__LEAN__", json.dumps(LEAN))
    html = html.replace("__UPSELL__", json.dumps(UPSELL))
    html = html.replace("__DRIVERS__", json.dumps(DRIVERS))
    html = html.replace("__SPOT_TITLES__", json.dumps({s["key"]: s["title"] for s in SPOTS}))
    html = html.replace("__QUIZBANKS__", json.dumps(QUIZ_BANKS))
    html = html.replace("__CCLIONS__", json.dumps(CC_LIONS))
    html = html.replace("__PREVIEW__", "true" if is_preview else "false")
    html = html.replace("__BOOTPID__", json.dumps(bootpid))
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
    if key == "breakthrough":
        person = (data.get("person") or "").strip()
        breakthrough = (data.get("breakthrough") or "").strip()
        action = (data.get("action") or "").strip()
        if not person or not breakthrough or not action:
            return jsonify({"ok": False})
        save_response(pid, "breakthrough", {
            "person": person[:160],
            "breakthrough": breakthrough[:240],
            "action": action[:240],
        })
        return jsonify({"ok": True})
    if key in QUIZ_BANKS:
        try:
            score = int(data.get("score"))
            total = int(data.get("total"))
        except (TypeError, ValueError):
            return jsonify({"ok": False})
        qn = len(QUIZ_BANKS[key]["questions"])
        if total != qn or score < 0 or score > qn:
            return jsonify({"ok": False})
        save_response(pid, key, {"score": score, "total": total})
        return jsonify({"ok": True})
    if key == "worryvault":
        note = (data.get("note") or "").strip()
        if not note:
            return jsonify({"ok": False})
        save_response(pid, "worryvault", {"note": note[:240]})
        return jsonify({"ok": True})
    if key == "clearcloudy":
        verdict = data.get("verdict")
        if verdict not in ("clear", "cloudy"):
            return jsonify({"ok": False})
        payload = {"verdict": verdict}
        if verdict == "cloudy":
            lions = data.get("lions")
            if lions in CC_LIONS_KEYS:
                payload["lions"] = lions
        save_response(pid, "clearcloudy", payload)
        return jsonify({"ok": True})
    if key == "energizer":
        word = (data.get("word") or "").strip()
        if not word:
            return jsonify({"ok": False})
        save_response(pid, "energizer", {"word": word[:40]})
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


@app.route("/spot/whonext/me")
def whonext_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    cur = whonext_current()
    name = None
    if cur is not None:
        for rid, first, last, company, email in ROSTER:
            if rid == cur:
                name = first + " " + last
                break
    return jsonify({
        "ok": True,
        "current_pid": cur,
        "current_name": name,
        "you": (cur is not None and cur == pid),
    })


@app.route("/spot/principledraw/me")
def principledraw_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    mine = principledraw_for(pid)
    return jsonify({"ok": True, "text": mine["text"] if mine else None})


@app.route("/spot/clearcloudy/me")
def clearcloudy_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    r = get_response(pid, "clearcloudy")
    return jsonify({
        "ok": True,
        "status": get_spot_status("clearcloudy"),
        "verdict": r.get("verdict") if r else None,
    })


def _bingo_me_payload(pid):
    st = bingo_get_state()
    positions = bingo_card_positions(pid, st["nonce"])
    marked = bingo_marked(positions, bingo_marks_for(pid))
    cells = []
    for pos in range(25):
        idx = positions[pos]
        if pos == 12 or idx is None:
            cells.append("")
        else:
            cells.append(BINGO_ITEMS[idx]["short"] if 0 <= idx < BINGO_N else "")
    return {
        "ok": True,
        "cells": cells,
        "marked": marked,
        "has_line": bingo_has_line(marked),
        "full": bingo_is_full(marked),
    }


@app.route("/bingo/me")
def bingo_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    return jsonify(_bingo_me_payload(pid))


@app.route("/bingo/mark", methods=["POST"])
def bingo_mark():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    data = request.get_json(silent=True) or {}
    pos = data.get("pos")
    if not isinstance(pos, int) or pos < 0 or pos > 24 or pos == 12:
        return jsonify({"ok": False})
    st = bingo_get_state()
    positions = bingo_card_positions(pid, st["nonce"])
    item_idx = positions[pos]
    bingo_toggle_mark(pid, item_idx)
    bingo_record_done_if_full(pid)
    return jsonify(_bingo_me_payload(pid))


@app.route("/spot/review/me")
def review_me():
    pid = joined_pid()
    if pid is None:
        return jsonify({"ok": False})
    bundle = review_bundle(pid)
    if not bundle:
        return jsonify({"ok": False})
    out = dict(bundle)
    out.pop("email", None)
    out["ok"] = True
    return jsonify(out)


@app.route("/spot/review/email", methods=["POST"])
def review_email():
    pid = joined_pid()
    if pid is None or pid == PREVIEW_PID:
        return jsonify({"ok": False})
    bundle = review_bundle(pid)
    if not bundle:
        return jsonify({"ok": False})
    res = send_recap_email(bundle["email"], bundle["name"], bundle)
    return jsonify({"ok": bool(res.get("ok"))})


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


def esc_html(s):
    s = str(s if s is not None else "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def send_recap_email(to_email, to_name, b):
    if not SENDGRID_API_KEY:
        return {"ok": False, "status": "skipped"}

    def sec(label, inner, bg="#f4f6f8", lab="#0d9488"):
        return ('<div style="background:' + bg + ';border-radius:10px;padding:12px 14px;margin-bottom:10px">'
                '<div style="font-size:12px;font-weight:bold;color:' + lab + '">' + label + '</div>'
                '<div style="font-size:14px;color:#0f2942;margin-top:3px;line-height:1.5">' + inner + '</div></div>')

    body = ""
    if b.get("note"):
        body += sec("A note from your instructor", esc_html(b["note"]), "#faeeda", "#854f0b")
    if b.get("disc"):
        d = b["disc"]
        lean = (d["primary_name"] + " and " + d["blend_name"]) if d.get("blend_name") else d["primary_name"]
        body += sec("Your DISC lean", "<strong>" + esc_html(lean) + "</strong><br>You lead with "
                    + esc_html(d["lead"]) + ". Your stretch is " + esc_html(d["stretch"]), "#e1f5ee")
    if b.get("driver"):
        body += sec("The driver you chose to grow", esc_html(b["driver"]))
    if b.get("breakthrough"):
        bt = b["breakthrough"]
        body += sec("Your relationship breakthrough", "<strong>" + esc_html(bt["person"]) + "</strong><br>"
                    + esc_html(bt["breakthrough"]) + "<br>You will: " + esc_html(bt["action"]))
    if b.get("principle"):
        body += sec("Your assigned principle", esc_html(b["principle"]))
    if b.get("quizzes"):
        qi = "<br>".join(esc_html(q["title"]) + ": " + str(q["score"]) + " of " + str(q["total"]) for q in b["quizzes"])
        body += sec("Your quiz scores", qi)
    if b.get("recognition_given"):
        rg = b["recognition_given"]
        body += sec("Recognition you gave", "To " + esc_html(rg["to"]) + ": " + esc_html(rg["note"]))
    if b.get("recognition_received"):
        ri = "<br>".join(esc_html(r["note"]) + " (from " + esc_html(r["from"]) + ")" for r in b["recognition_received"])
        body += sec("Recognition you received", ri, "#e1f5ee")
    if b.get("worry"):
        body += sec("The worry you named, and can now let go", esc_html(b["worry"]))

    html = (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#0f2942">'
        '<div style="background:#0f2942;padding:20px;border-radius:12px 12px 0 0">'
        '<div style="color:#ffffff;font-size:18px;font-weight:bold">Your Recap</div>'
        '<div style="color:#9fe1cb;font-size:13px">Dale Carnegie Course, Reno</div></div>'
        '<div style="border:1px solid #e6ebef;border-top:none;border-radius:0 0 12px 12px;padding:20px">'
        '<p style="font-size:15px;margin:0 0 14px">' + esc_html(to_name) + ", here is everything you did across the three days.</p>"
        + body +
        '<p style="font-size:12px;color:#5f6b76;border-top:1px solid #e6ebef;padding-top:12px;margin-top:6px">'
        'Keep applying these. Small steps, every day.</p></div></div>'
    )
    payload = {
        "personalizations": [{"to": [{"email": to_email, "name": to_name}]}],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": "Your recap from the Dale Carnegie Course",
        "content": [{"type": "text/html", "value": html}],
    }
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": "Bearer " + SENDGRID_API_KEY, "Content-Type": "application/json"},
            json=payload, timeout=15,
        )
        return {"ok": 200 <= resp.status_code < 300, "status": resp.status_code}
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
    if active == "who_next":
        payload["whonext"] = whonext_public()
    if active == "breakthrough":
        payload["breakthrough"] = breakthrough_list()
    if active in QUIZ_BANKS:
        payload["quiz"] = {"title": QUIZ_BANKS[active]["title"], "done": quiz_list(active)}
    if active == "worryvault":
        payload["worry"] = worry_list()
    if active == "energizer":
        payload["energizer"] = energizer_list()
    if active == "principledraw":
        payload["principledraw"] = principledraw_public()
    if active == "clearcloudy":
        payload["clearcloudy"] = clearcloudy_tally()
    payload["bingo_celebrate"] = bingo_pending_celebration()
    return jsonify(payload)


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
        "whonext": whonext_public(),
        "principledraw": principledraw_public(),
        "bingo": bingo_host_public(),
        "notes": notes_map(),
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
    if key == "who_next":
        whonext_reset()
        return jsonify({"ok": True})
    if key == "principledraw":
        principledraw_reset()
        return jsonify({"ok": True})
    if key == "bingo":
        bingo_new_game()
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


# ---------------------------------------------------------------------------
# Who's Next host controls
# ---------------------------------------------------------------------------
@app.route("/host/<secret>/whonext/pick", methods=["POST"])
def whonext_pick_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    pid = whonext_pick()
    return jsonify({"ok": pid is not None, "pid": pid})


@app.route("/host/<secret>/whonext/reset", methods=["POST"])
def whonext_reset_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    whonext_reset()
    return jsonify({"ok": True})


@app.route("/host/<secret>/principledraw/deal", methods=["POST"])
def principledraw_deal_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    n = principledraw_deal()
    return jsonify({"ok": n > 0, "dealt": n})


@app.route("/host/<secret>/principledraw/reset", methods=["POST"])
def principledraw_reset_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    principledraw_reset()
    return jsonify({"ok": True})


@app.route("/host/<secret>/bingo/announce", methods=["POST"])
def bingo_announce_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    bingo_announce_next()
    return jsonify({"ok": True})


@app.route("/host/<secret>/bingo/new", methods=["POST"])
def bingo_new_route(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    bingo_new_game()
    return jsonify({"ok": True})


@app.route("/host/<secret>/note", methods=["POST"])
def host_note(secret):
    if secret != HOST_SECRET:
        return jsonify({"ok": False}), 404
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    if pid not in ROSTER_IDS:
        return jsonify({"ok": False})
    note = (data.get("note") or "").strip()
    set_note(pid, note[:600])
    return jsonify({"ok": True})


BRAND_LOGO_B64 = "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"
BRAND_ICON_B64 = "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vjaWR5pXlkYu7sWZickk9TVwWtyZMZRRRWpIUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFAHqHwS8XHQ/FX9j3EmLLUyEGTwkw+4fx+7+I9K+mq+GIpHhlSWNijowZWBwQR0NfZPgzxAvifwjp2rAjzJogJQO0g+Vx+YNZzXUqLN6iiisygooooA8Q/aF1sx2elaHG3+tZrqUA9h8qfqW/KvBK7/4zamdR+JV+gOUtEjtk/Bcn/x5mrgK2irIh7hRRRVCCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAK97/Z61syWeq6HI3+qZbqIE9j8r/qF/OvBK7/AODOpnTviVYIThLtJLZ/xXI/8eVaUldAtz6rooorA0CiiigD4s8VXh1DxbrF4TnzryVx9C5x+lZFPlcyyvIerMT+dMroRmFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFa/hW8On+LdHvAceTeROfoHGf0rIp8TmKVJB1VgfyoA+56KKK5zQKKKKAPhWiiiugzCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigD7qooornNAooooA+FaKKK6DMKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACi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2H9tarDjVrpMJGw5t4z29mPf0HHrSbsgSudt4P8ADFr4R8NWuk22GMY3TS4x5sh+83+HsAK3aKKwbuaBRRRQAUUUUAFFFFABXinxY+E7XzTeIvDsGbk5e7s0H+s9XQf3vUd+o56+10U07CaufCxBUkEEEdQaSvpf4jfCC08TNLqui+XaasctIh4juD7/AN1vfoe/rXznqel32jX8ljqNrLbXMZw0ci4I9/ce44rZNMhqxUooopgFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABSgFiAAST0Aq1pml32s38djp1rLc3Mhwsca5J9/Ye54r6M+HPwgtPDLRarrXl3erDDRoOY7c+395vfoO3rSbSBK5j/Cf4TtYtD4i8RQYuRh7Szcf6v0dx/e9B26nnp7XRRWLdy0rBRRRSGFFFFABRRRQAUUUUAFFFFABWF4n8H6J4usvs2rWayFR+7mX5ZI/91v6dPat2igD5l8XfBLXtDZ7jR86rZDnEa4mQe6fxf8AAfyFeZSxSQyNHKjJIpwysMEH3Ffc9YPiDwZ4e8ToRq2lwTyYwJgNsg+jjBrRT7kuJ8Z0V75rf7PVvIWk0PWHi9IbxNw/77XB/Q1wWp/BnxrpxJTTkvEH8drMrfocN+lWpJk2ZwFFa954V8QaexF5omowY6l7ZwPzxWW8UkRxIjIfRhimAyiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKekUkpxGjOfRRmtSz8K+INQYCz0TUZ89Cls5H54oAyKK7/TPgz411EgvpyWaH+O6mVf0GW/Su90T9nq3jKya5rDy+sNmm0f99tk/oKTkkFmeDRRSTSLHEjPIxwqqMkn2Fem+Efglr2uMlxrGdKsjziRczOPZP4f+Bfka988P+DPD3hhANJ0uCCTGDMRukP1c5Nb1Q59ilEwvDHg/RPCNl9m0mzWMsP3kzfNJJ/vN/Tp7Vu0UVm3coKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA//2Q=="


@app.route("/brand/logo.png")
def brand_logo():
    return Response(base64.b64decode(BRAND_LOGO_B64), mimetype="image/png")


@app.route("/brand/icon.png")
def brand_icon():
    return Response(base64.b64decode(BRAND_ICON_B64), mimetype="image/png")


@app.route("/brand/joinqr.svg")
def brand_joinqr():
    return Response(base64.b64decode(JOIN_QR_SVG_B64), mimetype="image/svg+xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
