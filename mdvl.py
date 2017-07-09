#!/usr/bin/env python -Ss
# coding: utf-8
from textwrap import fill
from operator import setitem as set
import re, os

env = os.environ.get
# ----------------------------------------------------------------- Config Mgmt
class Cfg:
    '''
    Base class for osenv and kw configurable instances.
    - We have defaults, overridable by environ keys, overridable by **kws
    - problem is that color codes should be givabable as ints - but on the
      terminal we usually have them as full ansi escape str.
      Thats why `get_val` is present and adapts for that in the Colors cls.
    '''
    _parms = None # our (relevant) keys and values

    def setup(self, kw):
        ''' find all our key value defaults and override with env and **kw'''
        self._parms = []
        kv = [(k, getattr(self, k))
              for k in dir(self) if not k.startswith('_')]
        self._parms = [(k, v) for k, v in kv if not hasattr(v, '__code__')]
        [setattr(self, k, self.get_val(k, v, kw)) for k, v in self._parms]

    def get_val(self, k, dflt, kw):
        return type(dflt)(kw.get(k, env(k, dflt)))


class Colors(Cfg):
    # just a color namespace, built from facts which are from env
    O = '\x1B[0m'
    GRAY = 240
    CODE = 245
    L    = env('L', 66)
    H1   = env('I', 158)
    H2   = env('G', 115)
    H3   = env('M', 72)
    H4   = env('L', 66)
    emph = env('I', 158)
    ital = env('M', 72)

    def get_val(self, k, dflt, kw):
        v = kw.get(k, env(k, dflt))
        v = str(v)
        if '\x1B' in v:
            pass
        elif '[' in v:
            v = '\x1B' + v[2:]
        else:
            v = '\x1B[1;38;5;%sm' % v
        return v

    def H(s, lev):
        return getattr(s, 'H%s' % lev, s.L)


class Facts(Cfg):
    '''default scheme. The 'C' in the main method.
    x_ -> x with ansi escapes in __init__, with env precedence'''
    term_width       = 80
    no_print         = False
    bq_mark          = '┃'
    code_mark        = '│'
    light_bg         = False
    no_smart_indent  = False

    def __init__(f, **kw):
        # first check if the config contains color codes and set to C:
        # now overriding our defaults with kw then with env
        f.setup(kw)
        f.colr = Colors(); f.colr.setup(kw)

# ------------------------------------------------ end config - begin rendering
def _main(md, f):
    C, cur_colr = f.colr, 'cur_colr'
    cols = int(f.term_width)
    g = {} # glob parsing state (current color, code blocks)

    md = md.strip()

    # FENCED CODE BLOCKS:
    # we take them out before all parsing,see http://stackoverflow.com/a/587518
    apo, apos = chr(96), chr(96) * 3 # chr 96 is backtick.
    _ = r'^({apos})\n((?:[^{apo}]+\n{apo}{apo})+)'.format(apos=apos, apo=apo)
    fncd = re.compile(_, re.MULTILINE) # finds fenced code
    md = md.replace('\n~~~', apos) # alternative markup for fenced
    # remembering the blocks by their occurance number (len(g))
    [set(g, len(g), '\n'.join(m.groups()) + apo ) for m in fncd.finditer(md)]
    blocks = len(g)
    for i in range(blocks):
        md = md.replace(g[i], '\x02%s' % i)
    g['max_bq_depth'] = 0

    # Tools:
    is_header  = lambda l: l.startswith('#')
    is_list    = lambda l: l.lstrip().startswith('- ')
    is_empty   = lambda l: l.strip() == ''

    def bq(l):
        'blockquote'
        if not l.startswith('>'):
            return 0, l, ''
        _ = l.split(' ', 1)
        lev = len(_[0])
        g['max_bq_depth'] = max(lev, g['max_bq_depth'])
        return lev, _[1], _[0]

    # LINESPROCESSOR:
    lines, out = md.splitlines(), []
    lines.append('')
    while lines:

        line = lines.pop(0)
        if is_empty(line):
            out.append('')
            continue

        # indentd code blocks:
        cb = None
        while line.startswith('    '):
            cb = cb or []
            cb.append(line[4:])
            line = lines.pop(0)
        if cb:
            if out[-1] == '':
                out.pop()
            g[blocks] = '\n%s\n' % '\n'.join(cb)
            out.append('\x02%s' % blocks)
            blocks += 1
            lines.insert(0, line)
            continue

        ssi = None # subseq indent for textwrap
        bqm = '' # blockquote mark. e.g. '>>'.
        # TEXTBLOCKS: Concat lines which must be wrapped:
        bq_lev, line, bqm = bq(line) # blockquote status of that line

        while lines and not line.endswith('  ') and not is_header(line):

            nl, l0 = lines[0], line.lstrip() # next line, this line
            bqnl = bq(nl) # bq status of next line
            if bqnl[0] == bq_lev:
                lines[0] = nl = bqnl[1] # remove redundant '>'
            elif bqnl[0] != bq_lev and bqnl[0] > 0:
                break # next line different blockquote level -> new text block

            # finding subseq. indent for textwrap.fill:

            # Little md violation: If first word is starred, we set a ssi to
            # position: first line second word start.
            # Gives easy 2 col wrappable tables when first col is hilited.

            if ssi == None:
                if is_list(l0):
                    ssi = 2
                elif l0.startswith('*') and not f.no_smart_indent:
                    keywrd, l1 = (l0 + ' ').split(' ', 1)
                    l1 = l1.rstrip()
                    ssi = len(l0) - len(l1.lstrip()) - 2
                if l0.startswith('**') and not f.no_smart_indent:
                    ssi -= 2
            if ( not is_header(nl) and not is_list(nl) and
                not is_empty(nl) and not nl[0] in ('*', '\x02') ):
                line = line.rstrip() + ' ' + lines.pop(0).lstrip()
            else:
                # line is now one wrapable textblock
                if bqnl[0]:
                    lines[0] = (bqnl[2] + ' ') + lines[0]
                break

        ssi = 0 if ssi is None else ssi
        # lines are now blocks

        g[cur_colr] = C.O # reset color
        ind = len(line) - len(line.lstrip())
        if bqm:
            bqm += ' '
        line = bqm + line


        if is_header(line):
            h, line = line.split(' ', 1)
            g[cur_colr] = C.H(len(h))

        # WRAP:
        if len(line) > cols:
            s = (bqm + ' ' *  (ind + ssi))
            line = fill(line, subsequent_indent=s, width=cols)

        out.append(g[cur_colr] + line)


    # --------------- Leaving line/block scanning, reWork complete document now
    out = '\n'.join(out)

    # INLINE MARKUP, *, **, backticks
    # Alternating replacements, e.g. code, emph. requires a first space char:
    altern = lambda s, c, r: re.sub(
            r'([^{c}]+){c}([^{c}]+){c}?'.format(c=c),
            r'\1%s\2%s' % (r, g[cur_colr]), ' ' + s)[1:] # removing space again

    # Star must be replaced, else the re would not work :((
    # currently no way to find single stars and not process them..
    out = out.replace('*', '\x01')
    out = altern(out, apo       , C.L) # code
    out = altern(out, '\x01\x01', C.emph) # **
    out = altern(out, '\x01'    , C.ital) # *

    # rearrange resets, to be before the line breaks, not after...
    out = out.replace('\n' + C.O, C.O + '\n')
    # ... so that we can look for blockquotes:
    for i in range(g['max_bq_depth'], 0, -1):
        # coloring, take header levels. bq_mark is "|":
        m = ''
        for j in range(1, i + 1): m += C.H(j) + f.bq_mark
        m += C.O
        out = out.replace('\n' + '>' * i, '\n' + m)

    # Insert back the stored code blocks:
    code_fmt = lambda c: c.replace('\n', '\n%s%s %s' % (C.L, f.code_mark, C.CODE)
                         ).rsplit('\n', 1)[0]
    for i in range(blocks):
        out = out.replace('\x02%s' % i,
                          '%s%s%s' % (C.CODE, code_fmt(g[i]), C.O))
    out = out.replace(apos + '\n', '') # before
    out = out.replace(apos, '')        # after
    out += C.O # reset
    if f.no_print:
        return out
    else:
        print (out)


def main(md, **kw):
    f = Facts(**kw)
    #return _main(md, f), f  # we also return to the client the config
    try:
        return _main(md, f), f  # we also return to the client the config
    except Exception as ex:
        print (md) # clear text
        print ('md error: %s %s ' % (f.colr.CODE, ex))

if __name__ == '__main__':
    import sys
    import os
    from stat import S_ISFIFO
    # allow to adapt $COLUMNS by setting $term_width:
    cols = env('term_width') or os.popen('tput cols').read()
    if S_ISFIFO(os.fstat(0).st_mode): # pipe mode
        md = sys.stdin.read()
    else:
        md = sys.argv[1]
        if os.path.exists(md):
            with open(md) as fd:
                md = fd.read()
    main(md, term_width=cols)

