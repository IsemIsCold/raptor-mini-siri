"""Mini Siri for RAPTOR: a typed assistant whose intent is picked by a bag-of-words classifier
that can learn new words from the user."""
import json


def A(v, e, c=None):
    d = {"assign": v, "value": e}
    if c:
        d["comment"] = c
    return d


def C(t, c=None):
    d = {"call": t}
    if c:
        d["comment"] = c
    return d


def O(e, c=None):
    d = {"output": e}
    if c:
        d["comment"] = c
    return d


def IF(cond, then, els=None, c=None):
    d = {"if": cond, "then": then}
    if els:
        d["else"] = els
    if c:
        d["comment"] = c
    return d


def FOR(v, a, b, body, c=None):
    d = {"for": v, "from": a, "to": b, "body": body}
    if c:
        d["comment"] = c
    return d


def chain(cases, default=None):
    cond, body = cases[0]
    if len(cases) > 1:
        return IF(cond, body, [chain(cases[1:], default)])
    return IF(cond, body, default)


def q(s):
    return '"' + s.replace('"', '""') + '"'


INTENTS = [
    ("goodbye", "bye goodbye exit quit stop later"),
    ("math", "plus add sum minus subtract times multiply multiplied divided divide over calculate math + - * / x"),
    ("time", "time clock hour hours minute oclock"),
    ("date", "date day today month year"),
    ("joke", "joke jokes funny laugh"),
    ("greeting", "hello hi hey morning afternoon evening sup hiya"),
    ("about me", "who name yourself called creator made built"),
    ("how are you", "how feel feeling doing going"),
    ("thanks", "thank thanks thx appreciate"),
    ("coin / dice", "coin flip toss dice die roll random"),
]
STOP = "the a an is are what whats it me you i to of please can do does my your and in on tell be".split()
JOKES = ["Why did the flowchart go to therapy? It had too many unresolved loops.",
         "I would tell you a UDP joke, but you might not get it.",
         "Why do programmers prefer dark mode? Because light attracts bugs.",
         "There are 10 kinds of people: those who understand binary and those who don't."]
GREETS = ["Hello! How can I help you?", "Hi there! Ask me the time, a joke, or some maths.",
          "Hey! What can I do for you?"]
def bucket(w):
    c = ord(w[0])
    return c - 96 if 97 <= c <= 122 else 27


MONTHS = "January February March April May June July August September October November December".split()

# ------------------------------------------------------------------ SetupKnowledge
setup = [A("nint", str(len(INTENTS)), "THE TRAINING DATA\nEvery known word is stored with the intent it belongs to:\n"
                                      "tw[j] = word, tint[j] = intent number.\n"
                                      "Words are sorted by first letter; bstart[b]..bend[b] is the block of\n"
                                      "words starting with letter b (a=1 ... z=26, symbols=27), so a word is only\n"
                                      "compared with the few words that start with the same letter.")]
for k, (name, words) in enumerate(INTENTS, 1):
    setup.append(A("iname[%d]" % k, q(name)))
pairs = sorted(((w, k) for k, (name, words) in enumerate(INTENTS, 1) for w in words.split()),
               key=lambda p: (bucket(p[0]), p[0]))
for j, (w, k) in enumerate(pairs, 1):
    setup.append(A("tw[%d]" % j, q(w)))
    setup.append(A("tint[%d]" % j, str(k)))
setup.append(A("ntw", str(len(pairs)), "number of training words"))
for b in range(1, 28):
    idx = [j for j, (w, k) in enumerate(pairs, 1) if bucket(w) == b]
    setup.append(A("bstart[%d]" % b, str(idx[0] if idx else 1)))
    setup.append(A("bend[%d]" % b, str(idx[-1] if idx else 0)))
setup.append(A("nlw", "0", "words learned while chatting go in lw[] / lint[]"))
setup.append(A("lw[1]", '""'))
setup.append(A("lint[1]", "0"))
j = len(pairs)
for k, w in enumerate(STOP, 1):
    setup.append(A("sw[%d]" % k, q(w), "stop words: too common to learn from" if k == 1 else None))
setup.append(A("nsw", str(len(STOP))))
for k, t in enumerate(JOKES, 1):
    setup.append(A("joke[%d]" % k, q(t)))
for k, t in enumerate(GREETS, 1):
    setup.append(A("greet[%d]" % k, q(t)))
for k, t in enumerate(MONTHS, 1):
    setup.append(A("mon[%d]" % k, q(t)))

# ------------------------------------------------------------------ Tokenize (txt -> tok[1..ntok])
tokenize = [
    A("ntok", "0", "Split the sentence into lower-case words.\nLetters and digits build a word; anything else ends it.\n"
                   "+ - * / become words of their own (for maths)."),
    A("cur", '""'),
    FOR("ti", "1", "length_of(txt)", [
        A("code", "to_ascii(txt[ti])"),
        IF("code >= 65 and code <= 90", [A("code", "code + 32")], c="A..Z -> a..z"),
        IF("(code >= 97 and code <= 122) or (code >= 48 and code <= 57)",
           [A("cur", "cur + to_character(code)")],
           [C("PushWord"),
            IF("code = 43 or code = 45 or code = 42 or code = 47",
               [A("cur", '"" + to_character(code)'), C("PushWord")])]),
    ]),
    C("PushWord", "the last word"),
]

push_word = [
    IF("length_of(cur) > 0", [
        A("ntok", "ntok + 1"),
        A("tok[ntok]", "cur"),
        A("allnum", "1", "is the word a whole number? then keep its value for maths"),
        A("val", "0"),
        FOR("pc", "1", "length_of(cur)", [
            A("dg", "to_ascii(cur[pc]) - 48"),
            IF("dg < 0 or dg > 9", [A("allnum", "0")], [A("val", "val * 10 + dg")]),
        ]),
        A("isnum[ntok]", "allnum"),
        A("numval[ntok]", "val"),
        A("cur", '""'),
    ]),
]

# ------------------------------------------------------------------ Classify
classify = [
    FOR("cq", "1", "nint", [A("score[cq]", "0")],
        c="THE CLASSIFIER (bag of words)\nEach intent gets one point for every word of the\n"
          "sentence that appears in its training words.\nThe intent with the most points wins."),
    FOR("sk", "1", "ntok", [
        IF("isnum[sk] = 0", [
            A("t", "tok[sk]"),
            A("c1", "to_ascii(t[1])", "first letter -> which block of training words to search"),
            IF("c1 >= 97 and c1 <= 122", [A("b", "c1 - 96")], [A("b", "27")]),
            FOR("sj", "bstart[b]", "bend[b]", [
                IF("t = tw[sj]", [A("score[tint[sj]]", "score[tint[sj]] + 1")]),
            ]),
            FOR("sj", "1", "nlw", [
                IF("t = lw[sj]", [A("score[lint[sj]]", "score[lint[sj]] + 1")]),
            ], c="also check the words learned from the user"),
        ]),
    ]),
    A("best", "0"),
    A("bestscore", "0"),
    FOR("cq", "1", "nint", [
        IF("score[cq] > bestscore", [A("bestscore", "score[cq]"), A("best", "cq")],
           c="ties go to the lower intent number"),
    ]),
]

# ------------------------------------------------------------------ HasWord (target -> found)
has_word = [
    A("found", "0", "Is the word in 'target' one of the sentence's words?"),
    FOR("hk", "1", "ntok", [IF("tok[hk] = target", [A("found", "1")])]),
]

# ------------------------------------------------------------------ DoMath
def V(name_expr, c=None):
    """play one of Siri's recorded voice clips (siri_<name>.wav, next to the .rap file)"""
    return C('Play_Sound(%s)' % name_expr, c)


def op_test(words):
    return " or ".join('mt = "%s"' % w for w in words)


do_math = [
    A("cnt", "0", "Find the first two numbers and the operation word"),
    A("na", "0"),
    A("nb", "0"),
    A("op", "0"),
    FOR("mk", "1", "ntok", [
        IF("isnum[mk] = 1", [
            A("cnt", "cnt + 1"),
            IF("cnt = 1", [A("na", "numval[mk]")], [IF("cnt = 2", [A("nb", "numval[mk]")])]),
        ], [
            A("mt", "tok[mk]"),
            chain([
                (op_test(["plus", "add", "sum", "+"]), [A("op", "1")]),
                (op_test(["minus", "subtract", "-"]), [A("op", "2")]),
                (op_test(["times", "multiply", "multiplied", "x", "*"]), [A("op", "3")]),
                (op_test(["divided", "divide", "over", "/"]), [A("op", "4")]),
            ]),
        ]),
    ]),
    chain([
        ("cnt < 2", [V('"siri_mathneed.wav"'), O('"Siri: Give me two whole numbers, for example: what is 12 times 7"')]),
        ("op = 0", [V('"siri_mathop.wav"'), O('"Siri: Should I add, subtract, multiply or divide?"')]),
        ("op = 1", [V('"siri_math.wav"'), O('"Siri: " + na + " + " + nb + " = " + (na + nb)')]),
        ("op = 2", [V('"siri_math.wav"'), O('"Siri: " + na + " - " + nb + " = " + (na - nb)')]),
        ("op = 3", [V('"siri_math.wav"'), O('"Siri: " + na + " x " + nb + " = " + (na * nb)')]),
        ("nb = 0", [V('"siri_divzero.wav"'), O('"Siri: I cannot divide by zero!"')]),
    ], [V('"siri_math.wav"'), O('"Siri: " + na + " / " + nb + " = " + (na / nb)')]),
]

# ------------------------------------------------------------------ Respond (best -> answer)
respond = [chain([
    ("best = 1", [V('"siri_bye.wav"', "SPEAK: play the recorded voice clip for this answer"), O('"Siri: Goodbye! Thanks for chatting."'), A("done", "1")]),
    ("best = 2", [C("DoMath")]),
    ("best = 3", [A("hh", "Current_Hour", "time from the computer's clock"),
                  A("mm", "Current_Minute"),
                  IF("mm < 10", [A("mtxt", '"0" + mm')], [A("mtxt", '"" + mm')]),
                  V('"siri_time.wav"'), O('"Siri: It is " + hh + ":" + mtxt + "."')]),
    ("best = 4", [A("dd", "Current_Day", "date from the computer's clock\n(read into variables first: RAPTOR fails if\nthese functions are used inside an output)"),
                  A("mo", "Current_Month"),
                  A("yy", "Current_Year"),
                  A("mname", "mon[mo]"),
                  V('"siri_date.wav"'), O('"Siri: Today is " + dd + " " + mname + " " + yy + "."')]),
    ("best = 5", [A("r", "floor(random * 4) + 1", "pick a random joke"), V('"siri_joke" + r + ".wav"'), O('"Siri: " + joke[r]')]),
    ("best = 6", [A("r", "floor(random * 3) + 1"), V('"siri_greet" + r + ".wav"'), O('"Siri: " + greet[r]')]),
    ("best = 7", [V('"siri_about.wav"'), O('"Siri: I am Mini Siri, an assistant built entirely as a RAPTOR flowchart."')]),
    ("best = 8", [V('"siri_howareyou.wav"'), O('"Siri: I am doing great - all my loops are running smoothly!"')]),
    ("best = 9", [V('"siri_thanks.wav"'), O('"Siri: You are welcome!"')]),
], [
    A("target", '"coin"'),
    C("HasWord"),
    IF("found = 1",
       [IF("random < 0.5", [V('"siri_heads.wav"'), O('"Siri: I flipped a coin... HEADS!"')], [V('"siri_tails.wav"'), O('"Siri: I flipped a coin... TAILS!"')])],
       [A("r", "floor(random * 6) + 1"), V('"siri_dice" + r + ".wav"'), O('"Siri: I rolled a dice... " + r + "!"')]),
])]

# ------------------------------------------------------------------ Teach
teach = [
    V('"siri_teach.wav"'),
    O('"Siri: Sorry, I do not know that one yet. Teach me!"', "LEARNING: unknown sentence -> the user gives the intent,\n"
                                                            "and its words are added to the training data"),
    O('"      1 goodbye   2 math   3 time   4 date   5 joke"'),
    O('"      6 greeting   7 about me   8 how are you   9 thanks   10 coin/dice"'),
    {"input": "cat", "prompt": "Category number (0 = skip):"},
    IF("cat >= 1 and cat <= nint and cat = floor(cat)", [
        A("learned", "0"),
        FOR("lk", "1", "ntok", [
            A("target", "tok[lk]"),
            A("stop", "0"),
            FOR("lj", "1", "nsw", [IF("sw[lj] = target", [A("stop", "1")])]),
            IF("isnum[lk] = 0 and stop = 0", [
                A("nlw", "nlw + 1", "add the new word to the learned words"),
                A("lw[nlw]", "target"),
                A("lint[nlw]", "cat"),
                A("learned", "learned + 1"),
            ]),
        ]),
        O('"Siri: Got it! I learned " + learned + " new word(s) for: " + iname[cat]'),
        A("best", "cat"),
        C("Respond"),
    ], [V('"siri_never.wav"'), O('"Siri: OK, never mind."')]),
]

# ------------------------------------------------------------------ main
init = ["said", "txt", "cur", "ntok", "code", "allnum", "val", "dg", "best", "bestscore", "found", "target",
        "cnt", "na", "nb", "op", "mt", "hh", "mm", "mtxt", "mo", "r", "cat", "learned", "stop", "done",
        "nint", "ntw", "nsw", "nlw", "t", "c1", "b", "dd", "yy", "mname", "ly", "sy"]
main = [A(n, '""' if n in ("said", "txt", "cur", "target", "mt", "mtxt", "t", "mname") else "0",
          "MINI SIRI - a typed assistant with a learning classifier\n"
          "Create every variable first (avoids RAPTOR 'not found' errors)" if i == 0 else None)
        for i, n in enumerate(init)]
main += [
    C("Clear_Console", "start with an empty console (it keeps text from earlier runs)"),
    C("Open_Graph_Window(800, 520)", "the chat window: shows the last 14 lines of the conversation"),
    C('Set_Window_Title("Mini Siri")'),
    A("nl", "0"),
    A("line[1]", '""'),
    A("who[1]", "0"),
    A("newtext", '""'),
    A("newwho", "0"),
    A("sk", "0"),
    C("SetupKnowledge", "load the training words, jokes and month names"),
    V('"siri_welcome.wav"', "Mini Siri talks: each answer plays a .wav clip recorded with\nWindows text-to-speech. The siri_*.wav files must be in the same folder."),
    O('"Siri: Hi, I am Mini Siri! Ask me the time, the date, a joke,"'),
    O('"      some maths (12 times 7), to flip a coin or roll a dice."'),
    O('"      If I do not understand, you can teach me. Say bye to stop."'),
    {"repeat": [
        {"input": "said", "prompt": "You:"},
        A("txt", '"" + said', "make sure it is text (a lone number is read as a number)"),
        O('"You: " + txt'),
        C("Tokenize"),
        C("Classify"),
        IF("bestscore > 0", [
            O('"      [classifier: intent = " + iname[best] + ", " + bestscore + " matching word(s)]"'),
            C("Respond"),
        ], [
            IF("ntok = 0", [V('"siri_didnt.wav"'), O('"Siri: I did not catch that."')], [C("Teach")]),
        ]),
    ], "until": "done = 1"},
    {"output": '"(close this window or press Stop to finish)"'},
]

# ------------------------------------------------------------------ Say: add a line to the chat window
say = [
    {"output": "newtext", "comment": "also write it to the RAPTOR console"},
    IF("nl < 14", [A("nl", "nl + 1")], [
        FOR("sy", "1", "13", [A("line[sy]", "line[sy + 1]"), A("who[sy]", "who[sy + 1]")],
            c="window full: scroll every line up by one"),
    ]),
    A("line[nl]", "newtext"),
    A("who[nl]", "newwho"),
    C("Clear_Window(White)", "redraw the chat"),
    C("Draw_Box(0, 480, 800, 520, Blue, Filled)"),
    C('Display_Text(20, 508, "Mini Siri  -  type in the input box, then click Done", White)'),
    FOR("sy", "1", "nl", [
        A("ly", "470 - (sy - 1) * 32"),
        chain([("who[sy] = 1", [C("Display_Text(20, ly, line[sy], Blue)")]),
               ("who[sy] = 3", [C("Display_Text(20, ly, line[sy], Dark_Gray)")])],
              [C("Display_Text(20, ly, line[sy], Black)")]),
    ]),
]


def route(stmts):
    """turn every Output into 'newtext <- ...; newwho <- k; Call Say' so it also appears in the chat window"""
    out = []
    for st in stmts:
        for k in ("then", "else", "body", "repeat"):
            if k in st and isinstance(st[k], list):
                st[k] = route(st[k])
        if "output" in st and st["output"] not in ('"(close this window or press Stop to finish)"',):
            e = st["output"]
            who = "1" if e.startswith('"You:') else ("3" if e.startswith('"      [') else "2")
            a = A("newtext", e, st.get("comment"))
            out += [a, A("newwho", who), C("Say")]
        else:
            out.append(st)
    return out


main, respond, do_math, teach = route(main), route(respond), route(do_math), route(teach)
main = [m for m in main]

spec = {"subcharts": [
    {"name": "main", "body": main},
    {"name": "SetupKnowledge", "body": setup},
    {"name": "Tokenize", "body": tokenize},
    {"name": "PushWord", "body": push_word},
    {"name": "Classify", "body": classify},
    {"name": "Respond", "body": respond},
    {"name": "DoMath", "body": do_math},
    {"name": "HasWord", "body": has_word},
    {"name": "Teach", "body": teach},
    {"name": "Say", "body": say},
]}
json.dump(spec, open("specs/MiniSiri.json", "w", encoding="utf-8"), indent=1)
print("ok", j, "training words")
