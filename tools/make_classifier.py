"""Final project: click-and-train perceptron classifier for RAPTOR."""
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


def IF(cond, then, els=None, c=None):
    d = {"if": cond, "then": then}
    if els:
        d["else"] = els
    if c:
        d["comment"] = c
    return d


def chain(cases, default=None):
    """if/else-if chain from [(cond, body), ...]"""
    cond, body = cases[0]
    rest = cases[1:]
    if rest:
        return IF(cond, body, [chain(rest, default)])
    return IF(cond, body, default)


PLOT_TOP, PLOT_BOT, WIDTH = 470, 100, 600
H = PLOT_TOP - PLOT_BOT  # 370

# ------------------------------------------------------------------ main
init_vars = ["mx", "my", "btn", "pen", "done", "npts", "ntest", "w0", "w1", "w2", "lr", "trained",
             "epoch", "errors", "i", "u", "v", "s", "pred", "selx", "ya", "yb", "xa", "correct"]
main = [
    C("Open_Graph_Window(600, 500)",
      "FINAL PROJECT - Click-and-train classifier (a perceptron)\n"
      "1) choose RED or BLUE and click to add training points\n"
      "2) press TRAIN: the perceptron learns a line that separates the colours\n"
      "3) choose TEST and click anywhere: the model predicts the colour"),
    C("Set_Window_Title(\"Perceptron classifier - click to teach, TRAIN to learn\")"),
]
main += [A(n, "0", "Create every variable first (avoids RAPTOR 'not found' errors)" if n == "mx" else None)
         for n in init_vars]
main += [
    A("px[1]", "0", "Training data: px[i], py[i] = position, lab[i] = +1 (RED) or -1 (BLUE)"),
    A("py[1]", "0"),
    A("lab[1]", "0"),
    A("tx[1]", "0", "Test points: tx[j], ty[j] = position, tl[j] = predicted class"),
    A("ty[1]", "0"),
    A("tl[1]", "0"),
    A("pen", "1", "pen = what a click adds: 1 = RED point, -1 = BLUE point, 0 = TEST"),
    A("lr", "0.2", "learning rate: how far the line moves after each mistake"),
    A("msg", '"Choose RED or BLUE, then click in the white area to add points"'),
    C("Redraw"),
    {"repeat": [
        C("Get_Mouse_Button(Left_Button, mx, my)", "wait for a left click"),
        IF("my < 90", [
            A("btn", "floor(mx / 100) + 1", "6 buttons, each 100 pixels wide"),
            chain([
                ("btn = 1", [A("pen", "1"), A("msg", '"RED: click to add red points"')]),
                ("btn = 2", [A("pen", "-1"), A("msg", '"BLUE: click to add blue points"')]),
                ("btn = 3", [A("pen", "0"),
                             IF("trained = 1", [A("msg", '"TEST: click anywhere, the model predicts the colour"')],
                                [A("msg", '"Press TRAIN first, then TEST"')])]),
                ("btn = 4", [C("Train")]),
                ("btn = 5", [A("npts", "0"), A("ntest", "0"), A("w0", "0"), A("w1", "0"), A("w2", "0"),
                             A("trained", "0"), A("epoch", "0"), A("pen", "1"),
                             A("msg", '"Cleared. Choose RED or BLUE and add new points"')]),
            ], [A("done", "1")]),
        ], [
            IF("my > 100 and my < 470", [
                IF("pen != 0", [
                    A("npts", "npts + 1", "add a training point"),
                    A("px[npts]", "mx"),
                    A("py[npts]", "my"),
                    A("lab[npts]", "pen"),
                    A("msg", '"Training points: " + npts + "   (press TRAIN when ready)"'),
                ], [
                    IF("trained = 1", [
                        A("u", "mx / 600", "same feature scaling as in training"),
                        A("v", "(my - 100) / 370"),
                        A("s", "w0 + w1 * u + w2 * v", "score > = 0 means RED, < 0 means BLUE"),
                        IF("s >= 0", [A("pred", "1"), A("msg", '"Prediction: RED"')],
                           [A("pred", "-1"), A("msg", '"Prediction: BLUE"')]),
                        A("ntest", "ntest + 1"),
                        A("tx[ntest]", "mx"),
                        A("ty[ntest]", "my"),
                        A("tl[ntest]", "pred"),
                    ], [A("msg", '"Press TRAIN first, then TEST"')]),
                ]),
            ]),
        ]),
        IF("done = 0", [C("Redraw")]),
    ], "until": "done = 1"},
    C("Close_Graph_Window"),
]

# ------------------------------------------------------------------ Train
train = [
    IF("npts < 2", [A("msg", '"Add at least 2 points (both colours) before training"'), C("Redraw")], [
        A("epoch", "0", "Perceptron learning rule:\nfor every point the model gets wrong,\n"
                        "move the weights toward the right answer"),
        A("errors", "1"),
        {"while": "errors > 0 and epoch < 100", "body": [
            A("epoch", "epoch + 1", "one epoch = one pass over all training points"),
            A("errors", "0"),
            {"for": "i", "from": "1", "to": "npts", "body": [
                A("u", "px[i] / 600", "scale x to 0..1"),
                A("v", "(py[i] - 100) / 370", "scale y to 0..1"),
                A("s", "w0 + w1 * u + w2 * v", "score = bias + w1*u + w2*v"),
                IF("s >= 0", [A("pred", "1")], [A("pred", "-1")]),
                IF("pred != lab[i]", [
                    A("errors", "errors + 1", "wrong: nudge the weights toward the correct class"),
                    A("w0", "w0 + lr * lab[i]"),
                    A("w1", "w1 + lr * lab[i] * u"),
                    A("w2", "w2 + lr * lab[i] * v"),
                ]),
            ]},
            A("msg", '"Training...  epoch " + epoch + "   mistakes: " + errors'),
            C("Redraw", "show the line moving after every epoch"),
        ]},
        A("trained", "1"),
        A("correct", "npts - errors"),
        IF("errors = 0",
           [A("msg", '"Learned! All " + npts + " points correct after " + epoch + " epochs. Try TEST"')],
           [A("msg", '"Stopped after 100 epochs: " + correct + "/" + npts + " correct (no straight line fits)"')]),
        C("Redraw"),
    ]),
]

# ------------------------------------------------------------------ Redraw
labels = [("RED", "Red"), ("BLUE", "Blue"), ("TEST", "Dark_Gray"), ("TRAIN", "Green"),
          ("RESET", "Brown"), ("QUIT", "Black")]
redraw = [C("Clear_Window(White)", "Redraw the whole screen")]
redraw += [
    {"for": "i", "from": "1", "to": "ntest", "body": [
        IF("tl[i] = 1", [C("Draw_Circle(tx[i], ty[i], 9, Light_Red, Filled)")],
           [C("Draw_Circle(tx[i], ty[i], 9, Light_Blue, Filled)")]),
        C("Draw_Circle(tx[i], ty[i], 9, Black, Unfilled)", "test point: ringed, coloured by the prediction"),
    ]},
    {"for": "i", "from": "1", "to": "npts", "body": [
        IF("lab[i] = 1", [C("Draw_Circle(px[i], py[i], 6, Red, Filled)")],
           [C("Draw_Circle(px[i], py[i], 6, Blue, Filled)")]),
    ]},
    IF("epoch > 0", [C("DrawLine")]),
    C("Draw_Box(0, 0, 600, 95, White, Filled)", "cover the line outside the plot area"),
    C("Draw_Box(0, 472, 600, 500, White, Filled)"),
    C("Draw_Line(0, 97, 600, 97, Black)"),
    C("Display_Text(10, 492, msg, Black)"),
]
for k, (text, colour) in enumerate(labels):
    x = 100 * k
    redraw.append(C("Draw_Box(%d, 15, %d, 80, %s, Filled)" % (x + 8, x + 92, colour)))
    redraw.append(C('Display_Text(%d, 55, "%s", White)' % (x + 50 - 4 * len(text), text)))
redraw += [
    chain([("pen = 1", [A("selx", "0")]), ("pen = -1", [A("selx", "100")])], [A("selx", "200")]),
    C("Draw_Box(selx + 3, 10, selx + 97, 85, Black, Unfilled)", "frame around the selected pen"),
]

# ------------------------------------------------------------------ DrawLine
draw_line = [
    IF("abs(w2) > 0.0001", [
        A("ya", "100 + 370 * (0 - w0) / w2", "decision line: w0 + w1*u + w2*v = 0\nsolve for v at u = 0 and u = 1"),
        A("yb", "100 + 370 * (0 - w0 - w1) / w2"),
        A("ya", "max(-3000, min(3000, ya))", "keep the numbers drawable"),
        A("yb", "max(-3000, min(3000, yb))"),
        C("Draw_Line(0, ya, 600, yb, Black)"),
    ], [
        IF("abs(w1) > 0.0001", [
            A("xa", "600 * (0 - w0) / w1", "vertical line"),
            A("xa", "max(-3000, min(3000, xa))"),
            C("Draw_Line(xa, 100, xa, 470, Black)"),
        ]),
    ]),
]

spec = {"subcharts": [
    {"name": "main", "body": main},
    {"name": "Train", "body": train},
    {"name": "Redraw", "body": redraw},
    {"name": "DrawLine", "body": draw_line},
]}
json.dump(spec, open("specs/Classifier.json", "w", encoding="utf-8"), indent=1)
print("ok")
