from django.db.models import F, Q
from icecream import ic
import dill
from io import StringIO
import traceback
from contextlib import redirect_stdout


def plus(a, b):
    c = a + b
    return c

def run(request_dict):
    code_object = compile(request_dict['query']['code'], '<string>', 'exec')
    
    error = None
    f = StringIO()
    with redirect_stdout(f):
        try:
            exec(code_object)
        except:
            error = str(traceback.format_exc())

    if error == None:
        s = f.getvalue()
    else:
        s = error

    return True, s, None, None
