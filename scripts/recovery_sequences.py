"""Exact bounded public-sequence state for owned recovery comparisons."""
import re
import json


def sequence_state(query):
    # pg_sequences.last_value is NULL before first nextval, hiding the seed.
    # Read each actual sequence relation, including the is_called bit instead.
    names=query("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename;").splitlines()
    if len(names)>1024 or len(set(names))!=len(names):
        raise ValueError('Unexpected recovery sequence inventory')
    if any(re.fullmatch('[a-z_][a-z0-9_]{0,62}',name) is None for name in names):
        raise ValueError('Unexpected recovery sequence identifier')
    result={}
    for name in names:
        result[name]=json.loads(query(
            "SELECT json_build_object('last_value',s.last_value,'is_called',s.is_called,"
            "'data_type',format_type(p.seqtypid,NULL),'start',p.seqstart,'increment',p.seqincrement,"
            "'minimum',p.seqmin,'maximum',p.seqmax,'cache',p.seqcache,'cycle',p.seqcycle) "
            'FROM public.'+name+" s CROSS JOIN pg_sequence p WHERE p.seqrelid='public."+name+"'::regclass;"))
    return result
