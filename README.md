# Mini Siri & a Perceptron Classifier, built in RAPTOR

Two small machine-learning programs written entirely as **RAPTOR flowcharts**. RAPTOR is the visual
programming tool used in intro computer courses.

| Program | What it does | ML idea |
|---|---|---|
| **Mini Siri** (`MiniSiri/MiniSiri.rap`) | A typed voice assistant. Ask it the time, the date, a joke, some math, or to flip a coin or roll a dice. It answers out loud. If it doesn't understand you, **you teach it** and it remembers. | Bag-of-words **intent classifier** with online learning |
| **Classifier** (`Classifier/Classifier.rap`) | Click to place red and blue points, then press TRAIN and watch a line learn to separate them. Then click TEST points and it predicts their colour. | **Perceptron** (the simplest neural network) |

```
You: what is 12 times 7
      [classifier: intent = math, 1 matching word(s)]
Siri: 12 x 7 = 84
You: blorp
Siri: Sorry, I do not know that one yet. Teach me!   -> you type 7 (about me)
Siri: Got it! I learned 1 new word(s) for: about me
You: blorp
      [classifier: intent = about me, 1 matching word(s)]
Siri: I am Mini Siri, an assistant built entirely as a RAPTOR flowchart.
```

---

## 1. Run it

1. Install RAPTOR from <https://raptor.martincarlisle.com> (the current Avalonia version, Windows).
2. Download this repo. On GitHub, click **Code → Download ZIP** and unzip it.
3. Open `MiniSiri/MiniSiri.rap` in RAPTOR. Keep the `siri_*.wav` files **in the same folder** as the `.rap`, or there will be no voice.
4. **Wait about 20 seconds** after the file opens. Clicking Run while RAPTOR is still loading a big file can crash it.
5. Use **Run → Run Compiled**. Normal Run animates every symbol and takes about 40 seconds per answer. Compiled mode answers instantly. RAPTOR asks you to *Save As* first; save into the same folder.
6. Type in the input box and click **Done**. The chat appears in the graphics window. Type `bye` to stop.

For the Classifier, open `Classifier/Classifier.rap`, set the speed slider to about 70 and press Run (or use Run Compiled):

1. Pick **RED** or **BLUE**, then click in the white area to add points of that colour.
2. Press **TRAIN**. The black line moves after every epoch until all points are on the correct side.
3. Press **TEST** and click anywhere. A ringed dot shows the predicted colour.
4. **RESET** starts over and **QUIT** closes the program.

---

## 2. How Mini Siri works

```
 typed sentence ──► Tokenize ──► Classify ──► best intent ──► Respond ──► text + voice clip
                                    │                              ▲
                                    └── no match? ──► Teach ───────┘ (learn the new words)
```

### 2.1 Training data
`SetupKnowledge` fills two parallel arrays:

* `tw[j]`: a training word, for example `"joke"`
* `tint[j]`: the intent number it belongs to, for example `5`

There are 10 intents, starting with goodbye, math, time, date and joke, and 70 training words in total.

**Speed trick:** the words are sorted by first letter, and `bstart[b]..bend[b]` holds the block of words
that start with letter `b` (a=1 … z=26, symbols=27). Each word of the sentence is compared only with the
few training words that share its first letter, not with all 70. This took an answer from about 40 seconds down to about 1 second in normal Run.

### 2.2 Tokenize
`Tokenize` walks the sentence character by character with `to_ascii`:

* It converts upper case to lower case (`code + 32`).
* Letters and digits are added to the current word, and anything else ends the word (`PushWord`).
* `+ - * /` become words of their own, so `12*7` works.
* `PushWord` also checks whether the word is a whole number and stores its value in `numval[]`, for the math intent.

### 2.3 Classify (the ML part)
This is a **bag-of-words classifier**:

```
score[intent] = 0 for every intent
for every word in the sentence:
    for every training word with the same first letter:
        if they match: score[that word's intent] += 1
    for every word the user taught: same thing
best = intent with the highest score (ties -> lower number)
```

If `bestscore = 0`, Siri doesn't know the sentence and calls `Teach`.

### 2.4 Learning
`Teach` shows the list of categories, and the user types a number. Every word of the sentence that is not a
number and not a **stop word** (`the, a, is, what, you, …`, stored in `sw[]`) is added to `lw[]` / `lint[]`.
From then on, `Classify` counts those learned words too. The program learns while it runs.

### 2.5 Respond, math, time and voice
* `Respond` is an if/else-if chain on `best`.
* `DoMath` finds the first two numbers and an operation word (`plus`, `times`, `divided`, `/` …) and checks for division by zero.
* Time and date come from `Current_Hour`, `Current_Day` and so on. **Read them into variables first.** RAPTOR crashes ("Object reference not set") if you use them directly inside an Output.
* Every answer calls `Play_Sound("siri_xxx.wav")`. The clips were recorded with Windows' built-in text-to-speech (see `tools/make_voice.ps1`). RAPTOR has one sound player, so a new clip cuts off the previous one.

### 2.6 The chat window
RAPTOR's console and input dialogs hide answers behind each other. Instead, every message goes through
the `Say` subchart, which:

* keeps the last 14 lines in `line[]` / `who[]`, scrolling up when the window is full,
* redraws them in a graphics window: blue for you, black for Siri, and grey for the classifier's explanation.

---

## 3. How the Classifier (perceptron) works

* Each point is scaled to `u = x / 600` and `v = (y - 100) / 370`, so both fall between 0 and 1.
* The model is three numbers, `w0, w1, w2`. Its prediction is **RED if `w0 + w1·u + w2·v ≥ 0`, otherwise BLUE**.
* Training follows the **perceptron rule**: for every point it gets wrong,
  ```
  w0 += lr * label
  w1 += lr * label * u
  w2 += lr * label * v      (label = +1 red, -1 blue, lr = 0.2)
  ```
  It repeats epochs until there are 0 mistakes, or stops after 100 epochs (then no straight line can separate the points).
* The decision line `w0 + w1·u + w2·v = 0` is drawn by solving for `v` at `u = 0` and at `u = 1` (`DrawLine`).
* Buttons are plain rectangles. A click with `y < 90` is a button: `btn = floor(x / 100) + 1`.

---

## 4. Make your own

### Option A: build it by hand in RAPTOR
Recommended if this is your own class project. Building the flowchart yourself is how you learn it.

1. **Make the subcharts first.** Right-click the `main` tab → *Add subchart*. For Mini Siri you need
   `SetupKnowledge, Tokenize, PushWord, Classify, Respond, DoMath, HasWord, Teach, Say`.
   Subcharts in RAPTOR share main's variables, so no parameters are needed.
2. **Create every variable at the top of `main`** (`x ← 0`, `name ← ""`, …). RAPTOR throws
   *"Variable … not found"* if a subchart or `Get_Mouse_Button` reads a variable before it has been assigned.
3. **Arrays start at 1** (`tw[1]`). Give each array a first element before using it (`lw[1] ← ""`).
4. **Start with the classifier.** Put 3 intents with about 5 words each into `SetupKnowledge`, write `Tokenize` and
   `Classify`, and print `best`. When that works, add `Respond`, then `Teach`, then the chat window, then voice.
5. **Text vs numbers:** an Input of `12` comes back as a number. Use `txt ← "" + said` to force it to text.
6. **Strings:** `length_of(s)`, `s[i]` (1-based), `to_ascii`, `to_character`, and `+` to join.
7. **Graphics:** `Open_Graph_Window(w, h)`, `Clear_Window(White)`, `Draw_Box`, `Display_Text`,
   `Draw_Circle`, `Get_Mouse_Button(Left_Button, x, y)`. y counts from the **bottom** of the window.
   Avoid `Freeze_Graph_Window`, which left the window blank in our tests.
8. **Voice:** record your own clips. Run `tools/make_voice.ps1` in PowerShell, or use any recorder, save
   `.wav` files next to the `.rap`, and call `Play_Sound("name.wav")`.

### Option B: generate the flowchart from Python
Both programs here were *generated*: a Python script describes the flowchart as JSON, and a builder turns
the JSON into a `.rap` file. This is faster to change. For example, adding 20 training words by hand means
40 assignment boxes.

```
tools/
  make_siri.py        describes Mini Siri    -> specs/MiniSiri.json
  make_classifier.py  describes Classifier   -> specs/Classifier.json
  make_voice.ps1      records the siri_*.wav clips with Windows text-to-speech
  sim.py              runs a spec in Python to test the logic before opening RAPTOR
  specs/*.json        the generated flowchart descriptions
```

The spec format is simple: each statement is one flowchart symbol.

```json
{"subcharts": [{"name": "main", "body": [
  {"assign": "x", "value": "0"},
  {"input": "said", "prompt": "You:"},
  {"if": "x > 0", "then": [{"output": "\"positive\""}], "else": []},
  {"for": "i", "from": "1", "to": "10", "body": [ ... ]},
  {"repeat": [ ... ], "until": "done = 1"},
  {"call": "Classify"}
]}]}
```

Steps:

```bash
cd tools
python make_siri.py                 # 1. edit INTENTS / JOKES at the top, then regenerate the spec
python sim.py MiniSiri "hi" "what is 3 plus 4" "bye"   # 2. test the logic in Python
powershell -File make_voice.ps1 -OutDir ..\MiniSiri    # 3. re-record the voice if you changed any lines
```

4. Build the `.rap` from the spec. The builder (`make_rap.py`) is **not included** in this repo. It comes from the
   *RAPTOR flowchart* skill for Claude, which writes RAPTOR's XML format and checks every symbol with a port of RAPTOR's
   parser (RAPTOR silently blanks any symbol it can't parse). Without it, use the specs as a blueprint for Option A.

Ideas to extend it: more intents (weather by city, unit conversion, a quiz), saving learned words to a file with
`Redirect_Output` so the program remembers them between runs, or a kNN classifier instead of a perceptron.

---

## 5. Known RAPTOR quirks (learned the hard way)

| Symptom | Fix |
|---|---|
| `Variable x not found` | Assign every variable at the top of `main` |
| Crash right after opening a big file | Wait about 20 seconds before pressing Run |
| Each answer takes about 40 seconds | Use **Run → Run Compiled** |
| `Object reference not set` with dates | Read `Current_Day` and the others into variables first |
| Old text in the console | Call `Clear_Console` at the start |
| Graphics window blank | Don't use `Freeze_Graph_Window` |
| Clicks missed in mouse programs | Set the speed slider to about 70 |
| `Get_Mouse_Y` returns the X position | Use `Get_Mouse_Button(Left_Button, x, y)` instead |
