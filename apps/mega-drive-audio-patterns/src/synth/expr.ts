// A small, safe expression language for user-typed functions like I(t).
//
//   numbers   1  0.5  .5  2e-3
//   names     t (seconds since the key went down)  f (the note's frequency, Hz)  pi  e
//   operators + - * /  ^ or ** (power, right-associative)  unary + -  ( )
//   functions sin cos tan exp log sqrt abs floor (one argument)  min max (two or more)
//
// Precedence matches ordinary maths and Python: -t^2 is -(t^2), 2^-t is 2^(-t),
// 2^3^2 is 2^9. art/audio/fm.py accepts exactly this language and evaluates it with
// the same IEEE double arithmetic, so a patch sounds the same in the game build.
// Nothing here uses eval or Function.

export type Fn2 = (t: number, f: number) => number

export const VARIABLES = ['t', 'f'] as const
export const CONSTANTS: Record<string, number> = { pi: Math.PI, e: Math.E }
const UNARY: Record<string, (x: number) => number> = {
  sin: Math.sin,
  cos: Math.cos,
  tan: Math.tan,
  exp: Math.exp,
  log: Math.log,
  sqrt: Math.sqrt,
  abs: Math.abs,
  floor: Math.floor,
}
const VARIADIC: Record<string, (...xs: number[]) => number> = { min: Math.min, max: Math.max }
export const FUNCTIONS = [...Object.keys(UNARY), ...Object.keys(VARIADIC)]

export class ExprError extends Error {
  readonly pos: number
  constructor(message: string, pos: number) {
    super(message)
    this.pos = pos
  }
}

type Token =
  | { kind: 'num'; value: number; pos: number }
  | { kind: 'name'; value: string; pos: number }
  | { kind: 'op'; value: string; pos: number }
  | { kind: 'end'; pos: number }

function tokenize(src: string): Token[] {
  const out: Token[] = []
  let i = 0
  while (i < src.length) {
    const c = src[i]
    if (c === ' ' || c === '\t' || c === '\n') {
      i++
      continue
    }
    const num = /^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?/.exec(src.slice(i))
    if (num) {
      out.push({ kind: 'num', value: Number(num[0]), pos: i })
      i += num[0].length
      continue
    }
    const name = /^[A-Za-z_][A-Za-z_0-9]*/.exec(src.slice(i))
    if (name) {
      out.push({ kind: 'name', value: name[0], pos: i })
      i += name[0].length
      continue
    }
    if (src.startsWith('**', i)) {
      out.push({ kind: 'op', value: '^', pos: i })
      i += 2
      continue
    }
    if ('+-*/^(),'.includes(c)) {
      out.push({ kind: 'op', value: c, pos: i })
      i++
      continue
    }
    throw new ExprError(`unexpected "${c}"`, i)
  }
  out.push({ kind: 'end', pos: src.length })
  return out
}

// The parse tree compiles straight to closures.
type Node = (t: number, f: number) => number

class Parser {
  private toks: Token[]
  private i = 0

  constructor(src: string) {
    this.toks = tokenize(src)
  }

  parse(): Node {
    if (this.peek().kind === 'end') throw new ExprError('empty formula', 0)
    const node = this.sum()
    const tok = this.peek()
    if (tok.kind !== 'end') throw new ExprError(`unexpected ${describe(tok)}`, tok.pos)
    return node
  }

  private peek(): Token {
    return this.toks[this.i]
  }

  private isOp(value: string): boolean {
    const tok = this.peek()
    return tok.kind === 'op' && tok.value === value
  }

  private expect(value: string): void {
    const tok = this.peek()
    if (!this.isOp(value)) throw new ExprError(`expected "${value}" but found ${describe(tok)}`, tok.pos)
    this.i++
  }

  private sum(): Node {
    let left = this.product()
    while (this.isOp('+') || this.isOp('-')) {
      const op = (this.toks[this.i++] as { value: string }).value
      const a = left
      const b = this.product()
      left = op === '+' ? (t, f) => a(t, f) + b(t, f) : (t, f) => a(t, f) - b(t, f)
    }
    return left
  }

  private product(): Node {
    let left = this.unary()
    while (this.isOp('*') || this.isOp('/')) {
      const op = (this.toks[this.i++] as { value: string }).value
      const a = left
      const b = this.unary()
      left = op === '*' ? (t, f) => a(t, f) * b(t, f) : (t, f) => a(t, f) / b(t, f)
    }
    return left
  }

  private unary(): Node {
    if (this.isOp('-')) {
      this.i++
      const a = this.unary()
      return (t, f) => -a(t, f)
    }
    if (this.isOp('+')) {
      this.i++
      return this.unary()
    }
    return this.power()
  }

  private power(): Node {
    const base = this.atom()
    if (!this.isOp('^')) return base
    this.i++
    const exp = this.unary()
    return (t, f) => Math.pow(base(t, f), exp(t, f))
  }

  private atom(): Node {
    const tok = this.peek()
    if (tok.kind === 'num') {
      this.i++
      const v = tok.value
      return () => v
    }
    if (tok.kind === 'op' && tok.value === '(') {
      this.i++
      const inner = this.sum()
      this.expect(')')
      return inner
    }
    if (tok.kind === 'name') {
      this.i++
      if (this.isOp('(')) return this.call(tok.value, tok.pos)
      if (tok.value === 't') return (t) => t
      if (tok.value === 'f') return (_t, f) => f
      if (tok.value in CONSTANTS) {
        const v = CONSTANTS[tok.value]
        return () => v
      }
      if (tok.value in UNARY || tok.value in VARIADIC)
        throw new ExprError(`${tok.value} needs brackets: ${tok.value}(...)`, tok.pos)
      throw new ExprError(`unknown name "${tok.value}" (use t, f, pi or e)`, tok.pos)
    }
    throw new ExprError(`unexpected ${describe(tok)}`, tok.pos)
  }

  private call(name: string, pos: number): Node {
    this.expect('(')
    const args: Node[] = [this.sum()]
    while (this.isOp(',')) {
      this.i++
      args.push(this.sum())
    }
    this.expect(')')
    if (name in UNARY) {
      if (args.length !== 1) throw new ExprError(`${name} takes one argument`, pos)
      const fn = UNARY[name]
      const a = args[0]
      return (t, f) => fn(a(t, f))
    }
    if (name in VARIADIC) {
      if (args.length < 2) throw new ExprError(`${name} takes two or more arguments`, pos)
      const fn = VARIADIC[name]
      return (t, f) => fn(...args.map((a) => a(t, f)))
    }
    throw new ExprError(`unknown function "${name}"`, pos)
  }
}

function describe(tok: Token): string {
  if (tok.kind === 'end') return 'the end of the formula'
  if (tok.kind === 'num') return `the number ${tok.value}`
  return `"${tok.value}"`
}

/** Compile a formula, or throw an ExprError saying where it went wrong. */
export function compile(src: string): Fn2 {
  return new Parser(src).parse()
}

/** Compile without throwing: the function, or the error to show. */
export function tryCompile(src: string): { fn: Fn2; error: null } | { fn: null; error: ExprError } {
  try {
    return { fn: compile(src), error: null }
  } catch (e) {
    if (e instanceof ExprError) return { fn: null, error: e }
    throw e
  }
}
