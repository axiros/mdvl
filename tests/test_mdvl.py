#!/usr/bin/env python -tt

import unittest, sys, os
import operator
import time
pth = os.path.abspath(__file__).rsplit('/', 2)[0]
sys.path.insert(0, pth)
import mdvl

# see README.md:
inspect = os.environ.get('inspect')
record = os.environ.get('record')
if record:
    print('removing old recordings')
    os.system('/bin/rm -f "%s"' % (pth + '/tests/results/'))

def dedent(s):
    md = s.splitlines()
    if len(md) < 2: return s
    ind = len(md[1]) - len(md[1].lstrip())
    return '\n'.join([m[ind:] for m in md])

class F(unittest.TestCase):
    def test_gslti(s):
        gslti = mdvl.get_subseq_light_table_indent
        assert gslti('*a* b'       ) == 2
        assert gslti('*a b* b'     ) == 4
        assert gslti('*a*: b'      ) == 3
        assert gslti('*a b*: b'    ) == 5
        assert gslti('*a* b '      ) == 2
        assert gslti('*a b* b '    ) == 4
        assert gslti('*a*: b '     ) == 3
        assert gslti('*a b*: b '   ) == 5
        assert gslti('**a** b'     ) == 2
        assert gslti('**a b** b'   ) == 4
        assert gslti('**a**: b'    ) == 3
        assert gslti('**a b**: b'  ) == 5
        assert gslti('**a** b '    ) == 2
        assert gslti('**a b** b '  ) == 4
        assert gslti('**a**: b '   ) == 3
        assert gslti('**a b**: b ' ) == 5




class M(unittest.TestCase):
    def c(s, md, testcase, **kw):
        print('\n\n%s\n' % ('=' * 40))
        print('Testcase: %s' % testcase)
        print('\n\n%s\n' % ('=' * 40))
        md = dedent(md)
        print('source (spaces as dots):')
        print(md.replace(' ', '.'))
        mdr, f = mdvl.main(md, no_print=True, **kw)
        print('result:')
        print(mdr)
        if inspect:
            return
        fn = pth + '/tests/results/' + testcase
        if record:
            print ('recording %s' % testcase)
            with open(fn, 'w') as fd:
                fd.write(mdr)
            return
        with open(fn) as fd:
            exp = fd.read()
            if exp == mdr:
                return
            import difflib
            d = difflib.Differ()
            diff = d.compare(exp.splitlines(), mdr.splitlines())
            print ('\n'.join(diff))
            raise Exception('compare failed')


    def test_1(s):
        s.c( '''
        # H1
        ## H2
        foo *it* **em** bar
        ''', 'test_1')

    def test_list_wrap(s):
        s.c('''
        # H1
        - this line  
          line**break**
        - bar
        ''', 'test_list_wrap')


    def test_light_table(s):
        s.c( '''
        # H1
        *xyz* L
        *foobar* baz

        # Fat:
        **xyz** L
        **foobar** baz

        # no spc
        *xyz*: L
        *foobar*: baz

        # Fat no spc:
        **xyz**: L
        **foobar**: baz

        '''.replace('L', 'asdf ' * 20)
        , 'test_light_table')


    def test_horiz_rules(s):
        s.c( '''
        # H1
        ----
        foo
        ****
        bar
        ___
        baz
        '''
        , 'test_horiz_rules')


    def test_indent(s):
        s.c( '''
        # H1
        ----
        a longer sentence which will be indented by 5 chars
        '''
        , 'test_indent', indent=5)


    def test_width(s):
        s.c( '''
        # H1
        ----
        a longer sentence which will be wrapped into max 8 chars
        '''
        , 'test_width', indent=10, width=10, rindent=2)

    def test_single_line_mode(s):
        s.c('> this is single line, no indent, no line sep'
            , 'test_single_line_mode')

    def test_single_line_mode_forced_indent(s):
        s.c('> this is single line, still indent can be forced'
            , 'test_single_line_mode_forced_indent', indent=10)


if __name__ == '__main__':
    # tests/test_pycond.py PyCon.test_auto_brackets
    print('NOTE: TO RECORD A NEW TEST RESULT SET: export record=1 - THEN RUN.')
    print('to inspect before recording: export inspect=1 then run.')
    unittest.main()


