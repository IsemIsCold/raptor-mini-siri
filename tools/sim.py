"""Tiny simulator for the RAPTOR JSON specs (console subset) to check program logic."""
import ast, datetime, json, math, random, re, sys

sys.setrecursionlimit(10000)


class RStr(str):
    def __getitem__(self, i):  # RAPTOR strings are 1-based
        return RStr(str.__getitem__(self, int(i) - 1))


def radd(a, b):
    if isinstance(a, str) or isinstance(b, str):
        f = lambda v: v if isinstance(v, str) else (str(int(v)) if float(v).is_integer() else repr(round(v, 4)))
        return RStr(f(a) + f(b))
    return a + b


class AddT(ast.NodeTransformer):
    def visit_BinOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Add):
            return ast.Call(ast.Name('radd', ast.Load()), [n.left, n.right], [])
        return n


def py(expr):
    e = expr
    e = re.sub(r'\bmod\b', '%', e)
    e = re.sub(r'\brem\b', '%', e)
    e = e.replace('^', '**').replace('!=', '<>').replace('<>', '!=')
    # RAPTOR '=' means '==', but leave text inside "quotes" alone
    parts = re.split(r'("(?:[^"]|"")*")', e)
    e = ''.join(p if p.startswith('"') else re.sub(r'(?<![<>!=])=(?!=)', '==', p) for p in parts)
    return e


def ev(expr, env):
    tree = ast.parse(py(expr), mode='eval')
    tree = ast.fix_missing_locations(AddT().visit(tree))
    g = dict(radd=radd, floor=math.floor, sqrt=math.sqrt, pi=math.pi, abs=abs,
             to_ascii=ord, to_character=lambda c: RStr(chr(int(c))), length_of=len, min=min, max=max)
    now = datetime.datetime.now()
    g.update(random=random.random(), Current_Hour=now.hour, Current_Minute=now.minute,
             Current_Day=now.day, Current_Month=now.month, Current_Year=now.year)
    return eval(compile(tree, '<e>', 'eval'), g, env)


class Prog:
    def __init__(self, spec, inputs):
        self.subs = {s['name']: s for s in spec['subcharts']}
        self.inputs = list(inputs)
        self.out = ''
        self.steps = 0

    def run(self):
        self.block(self.subs['main']['body'], {})
        return self.out

    def block(self, body, env):
        for st in body:
            self.stmt(st, env)

    def stmt(self, st, env):
        self.steps += 1
        if self.steps > 5_000_000:
            raise RuntimeError('too many steps')
        if 'assign' in st:
            m = re.match(r'(\w+)\[(.+)\]$', st['assign'].strip())
            if m:
                env.setdefault(m.group(1), {})[ev(m.group(2), env)] = ev(st['value'], env)
            else:
                env[st['assign']] = ev(st['value'], env)
        elif 'call' in st and st['call'].split('(')[0].strip() not in self.subs:
            pass  # RAPTOR built-in (graphics, sound, Clear_Console): nothing to simulate
        elif 'call' in st and '(' not in st['call']:
            self.block(self.subs[st['call'].strip()]['body'], env)
        elif 'input' in st:
            v = self.inputs.pop(0)
            if isinstance(v, str) and re.fullmatch(r'-?\d+(\.\d+)?', v):
                v = float(v) if '.' in v else int(v)  # RAPTOR reads a typed number as a number
            env[st['input']] = v if not isinstance(v, str) else RStr(v)
        elif 'output' in st:
            v = ev(st['output'], env)
            self.out += radd('', v) + ('\n' if st.get('newline', True) else '')
        elif 'if' in st:
            self.block(st['then'] if ev(st['if'], env) else st.get('else', []), env)
        elif 'while' in st:
            while ev(st['while'], env):
                self.block(st['body'], env)
        elif 'repeat' in st:
            while True:
                self.block(st['repeat'], env)
                if ev(st['until'], env):
                    break
        elif 'for' in st:
            v = st['for']
            env[v] = ev(st['from'], env)
            while not env[v] > ev(st['to'], env):
                self.block(st['body'], env)
                env[v] = env[v] + ev(st.get('step', '1'), env)
        elif 'call' in st:
            m = re.match(r'(\w+)\s*\((.*)\)', st['call'])
            name, args = m.group(1), [a.strip() for a in m.group(2).split(',')]
            sub = self.subs[name]
            local = {}
            params = [p.split()[-1] for p in sub['params']]
            modes = [p for p in sub['params']]
            for p, md, a in zip(params, modes, args):
                if md.startswith('in'):
                    local[p] = ev(a, env)
            self.block(sub['body'], local)
            for p, md, a in zip(params, modes, args):
                if 'out' in md:
                    env[a] = local[p]
        else:
            raise ValueError(st)


def run(name, inputs):
    spec = json.load(open(f'specs/{name}.json', encoding='utf-8'))
    p = Prog(spec, inputs)
    return p.run().rstrip('\n')


if __name__ == '__main__':
    # Usage: python sim.py MiniSiri "hello" "what is 12 times 7" "tell me a joke" "bye"
    # Runs the JSON spec in specs/<name>.json with the given typed inputs and prints the console.
    # Graphics and sound calls are skipped, so this checks the logic only.
    name = sys.argv[1] if len(sys.argv) > 1 else 'MiniSiri'
    inputs = sys.argv[2:] or ['hello', 'what is 12 times 7', 'tell me a joke', 'flip a coin', 'bye']
    print(run(name, inputs))
