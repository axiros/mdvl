#!/usr/bin/env python -tt

import unittest, sys, os
import operator
import time
pth = os.path.abspath(__file__).rsplit('/', 2)[0]
sys.path.insert(0, pth)
import mdvl


'''
We visually inspect the test results.
If all ok we export record=1 and run again, so that we have the results
as the next set of assertions for the next run

Rationale: It is very tedious to write assertions with the escape codes and
change all the time when we add a new feature, which might cause a
re-arrrangement of the coloring in the code.
'''
record = os.environ.get('record')
inspect = os.environ.get('inspect')

def dedent(s):
    md = s.splitlines()
    if len(md) < 2: return s
    ind = len(md[1]) - len(md[1].lstrip())
    return '\n'.join([m[ind:] for m in md])

class M(unittest.TestCase):
    def c(s, md, testcase):
        print('\n-----\n')
        md = dedent(md)
        print('source (spaces as dots):')
        print(md.replace(' ', '.'))
        mdr, f = mdvl.main(md, no_print=True)
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


    def test_list_table(s):
        s.c( '''
        # H1
        *foo* L
        *foobar* baz
        '''.replace('L', 'asdf ' * 20)
        , 'test_list_table')

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



if __name__ == '__main__':
    # tests/test_pycond.py PyCon.test_auto_brackets
    print('NOTE: TO RECORD A NEW TEST RESULT SET: export record=1 - THEN RUN.')
    print('to inspect before recording: export inspect=1 then run.')
    unittest.main()


