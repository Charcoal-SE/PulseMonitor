from re import compile, search, match, sub, I, error
from html import unescape


_re_compile = compile

def _normalize(regex):
    if regex.startswith('<code>') and regex.endswith('</code>'):
        regex = regex[6:-7]
    return unescape(regex)

def compile(regex, flags=0):
    return _re_compile(_normalize(regex), flags)
