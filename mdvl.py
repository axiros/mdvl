#!/usr/bin/env python -Ss
# coding: utf-8

'''
# Lightweight Simple Markdown Renderer for the Terminal

## Usage

    mdvl <markdown source | markdown file>
    cat <markdown file> | mdvl

## Config

```
%s
```

### Colors

```
%%s
```

See also https://github.com/axiros/mdvl

'''
__version__ = "2017.07.16.7" # count up for new pip versions
__author__ = "Gunther Klessinger"

from textwrap import fill
from operator import setitem as set
import re, os

# check environ for value and cast into bools if necessary:
_b = {'True': True, 'False': False}
env = lambda k, d=None: _b.get(k, os.environ.get(k, d))

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
    '''
    Color namespae with efault color scheme (greenish).
    The 'C' in the main method.
    x_ -> x with ansi escapes in __init__, with env precedence
    '''
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
        # see Cfg for expl.
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
    ''' features config '''
    term_width       = 80
    no_print         = False
    bq_mark          = '┃'
    code_mark        = '│'
    light_bg         = False
    no_smart_indent  = False
    horiz_rule       = '─'
    single_line_mode = False
    # left and right global indents:
    indent           = 1
    rindent          = 0
    width            = 0 # if set > 0 we set rindent accordingly
    header_numbering = 50 # -1: off, min number of lines to do autonumbering
    header_underlining = '*' # e.g. '*-' to underline H1 with *** and H2 with ---


    def __init__(f, md, **kw):
        # first check if the config contains color codes and set to C:
        # now overriding our defaults with kw then with env
        if md.split('\n', 1)[0] == md:
            f.single_line_mode = True
            f.indent = 0
        f.setup(kw)
        f.colr = Colors(); f.colr.setup(kw)

# ------------------------------------------------ end config - begin rendering
# helper funcs:
def get_subseq_light_table_indent(l0):
    p = '**' if l0.startswith('**') else '*'
    keywrd, l1 = l0[2:].split(p, 1)
    keywrd = l0[:2] + keywrd + p
    l1 = l1
    offs = 1 if l1 and l1[0] == ' ' else 2
    return len(l0) - len(l1[offs:].lstrip()) - (2 * len(p))


def block_quote_status(l, g):
    'blockquote'
    if not l.startswith('>'):
        return 0, l, ''
    _ = l.split(' ', 1)
    lev = len(_[0])
    g['max_bq_depth'] = max(lev, g['max_bq_depth'])
    return lev, _[1], _[0]



h_rules_col = {'-': 'L', '_': 'H3', '*': 'H1'} # different colors
h_rules = '---', '___', '***'
def _main(md, f):
    C, cur_colr = f.colr, 'cur_colr'
    cols = int(f.term_width)
    if f.width:
        f.rindent = cols - f.indent - f.width + f.rindent
    cols = cols - f.indent - f.rindent

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
    is_md_link = lambda l: l[0] == '[' and 'http' in l and ']' in l
    def is_rule(l):
        if l[:3] in h_rules:
            ll = len(l)
            return True if l in (ll * '-', ll * '*', ll * '_') else False


    # LINESPROCESSOR:
    lines, out = md.splitlines(), []

    g['header_numbering'] = False
    if f.header_numbering > -1 and len(lines) > f.header_numbering:
        g['header_numbering'] = True
        g['header_level'] = {} # storing the current header numberings

    # remove boundary effects:
    lines.insert(0, '')
    lines.append('')

    while lines:

        line = lines.pop(0)
        if is_empty(line):
            out.append('')
            continue

        if is_rule(line):
            out.append(getattr(C, h_rules_col[line[0]])+ (cols * f.horiz_rule))
            continue

        cb = None # indentd code blocks:
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

        # TEXTBLOCKS: Concat lines which must be wrapped:
        bqm = '' # blockquote mark. e.g. '>>'.
        bq_lev, line, bqm = block_quote_status(line, g)

        src_line_nr = 0
        while ( lines and not line.endswith('  ')
                      and not is_header(line) ):

            src_line_nr += 1
            nl, l0 = lines[0], line.lstrip() # next line, this line
            bqnl = block_quote_status(nl, g)
            if bqnl[0] == bq_lev:
                lines[0] = nl = bqnl[1] # remove redundant '>'
            elif bqnl[0] != bq_lev and bqnl[0] > 0:
                break # next line different blockquote level -> new text block

            # finding subseq. indent for textwrap.fill:

            # Little md violation: If first word is starred, we set a ssi to
            # position: first line second word start.
            # Gives easy 2 col wrappable tables when first col is hilited.

            #if 'xyz' in line:
            #    import pdb; pdb.set_trace()
            if ssi == None:
                if is_list(l0):
                    ssi = 2
                elif ( l0.startswith('*') and
                       not f.no_smart_indent and
                       src_line_nr == 1 ):
                    ssi = get_subseq_light_table_indent(l0)

            if ( not is_header(nl)       and
                 not is_list(nl)         and
                 not is_empty(nl)        and
                 not is_md_link(nl)      and
                 not nl[0] in ('\x02', ) and
                 not is_rule(nl)
                 ):
                line = line.rstrip() + ' ' + lines.pop(0).lstrip()
            else:
                # line is now one wrapable textblock
                if bqnl[0]: # block quote new line
                    # adapt next line to parse:
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
            level = len(h)

            u = getattr(f, 'header_underlining', '')
            if len(u) >= level:
                lines.insert(0, 3 * u[level-1])

            if g['header_numbering']:
                hl = g['header_level']
                hl[level] = hl.get(level, 0) + 1
                [set(hl, i, 0) for i in hl if i > level]
                nr = '.'.join([str(hl[ll]) for ll in range(1, level + 1)])
                line = nr + ' ' + line
            g[cur_colr] = C.H(level)

        # WRAP:
        if len(line) > cols:
            s = (bqm + ' ' *  (ind + ssi))
            line = fill(line, subsequent_indent=s, width=cols)
        if is_md_link(line):
            g[cur_colr] = C.GRAY
        out.append(g[cur_colr] + line)


    # --------------- Leaving line/block scanning, reWork complete document now
    g[cur_colr] = C.O
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

    # rearrange resets, to be *before* the line breaks, not after...
    out = out.replace('\n' + C.O, C.O + '\n')
    # ... so that we can look for blockquotes:
    for i in range(g['max_bq_depth'], 0, -1):
        # coloring, take header levels. bq_mark is "|":
        m = ''
        for j in range(1, i + 1):
            m += C.H(j) + f.bq_mark
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
    out = strip_it(out, C.O)
    if not f.single_line_mode:
        out = '\n' + out + '\n'
    li, ri = f.indent * ' ', f.rindent * ' '
    if li or ri:
        out = li + out.replace('\n', '%s\n%s' % (ri, li))
    out += C.O # reset
    if not f.no_print:
        print (out)
    return out

def strip_it(out, rst):
    'clumsy way to strip at start at end, including color resets'
    sc = {' ': 1, rst: len(rst), '\n': 1}
    while 1:
        m = False
        for k in sc:
            if out.startswith(k):
                out = out[sc[k]:]
                m = True
            if out.endswith(k):
                out = out[:-sc[k]]
                m = True
            if m:
                break
        if not m:
            break
    return out


def main(md, **kw):
    f = Facts(md, **kw)
    #return _main(md, f), f  # we also return to the client the config
    try:
        return _main(md, f), f  # we also return to the client the config
    except Exception as ex:
        print (md) # clear text
        print ('md error: %s %s ' % (f.colr.CODE, ex))

def render(md, cols, **kw):
    kw['term_width'] = cols
    return main(md, **kw)[0]

def get_help(cols, PY2):
    ff = Facts('\n', term_width=cols)
    md, C = __doc__, ff.colr
    for o in ff, C:
        mmd = ()
        for k, d in sorted(o._parms):
            v = getattr(o, k)
            if o == ff: # need the perceived len here:
                v = C.H2 + (str(u'%5s' % str(v)) if PY2 else '%5s' % v) + C.O
            mmd += ('%s %s [%s]' % (v, k, d),)
        md = md % ('\n'.join(mmd))
    return md

def sys_main():
    import sys
    PY2 = sys.version_info[0] == 2
    if PY2:
        reload(sys); sys.setdefaultencoding('utf-8')
    import os
    from stat import S_ISFIFO
    # allow to adapt $COLUMNS by setting $term_width:
    cols = env('term_width') or os.popen('tput cols').read().strip()
    if S_ISFIFO(os.fstat(0).st_mode): # pipe mode
        md = sys.stdin.read()
    else:
        if not len(sys.argv) > 1 or '-h' in sys.argv:
            md = get_help(cols, PY2)
        else:
            md = sys.argv[1]
        if os.path.exists(md):
            with open(md) as fd:
                md = fd.read()
    main(md, term_width=cols)

if __name__ == '__main__':
    sys_main()

