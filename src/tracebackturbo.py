"""Extract, format and print information about Python stack traces."""
# 2010-01-27, benjamin:
# this is a patched traceback.py module (hg id 1728133edce0)
# in addition to the original traceback module, this moduls dumps
# the scope (local and global variables) of all traced functions.
# note: this module holds lots of legacy code and duplicates,
#   we could clean-up things a bit for ease of maintenance.

import linecache
import sys
import types

__all__ = ['extract_stack', 'extract_tb', 'format_exception',
           'format_exception_only', 'format_list', 'format_stack',
           'format_tb', 'print_exc', 'format_exc', 'print_exception',
           'print_last', 'print_stack', 'print_tb', 'tb_lineno',
           'print_vars', 'format_vars']

def _print(afile, astr='', terminator='\n'):
    """write a line to a file"""
    afile.write(astr + terminator)

def print_vars(vars, width=72, afile=None):
    """Print a list of variables as given by globals.items()"""

    if afile is None:
        afile = sys.stderr
    for key, value in vars:
        var = '      '
        if isinstance(value, str):
            value = '"' + value.encode("string_escape") + '"'
        if isinstance(value, unicode):
            value = 'u"' + value.encode(
                                    sys.getdefaultencoding(),
                                    'replace').encode("string_escape") + '"'
        try:
            var += "%s = %s" % (key, value)
        except Exception as _exc:
            var += "%s = %s" % (key, type(value))
        if len(var) > width:
            var = var[:width - 3] + '...'
        _print(afile, var)

def format_vars(vars, width=72):
    """Format a list of variables, arguments are like print_vars"""

    result = ""
    for key, value in vars:
        var = '      '  # fixed indentation
        if isinstance(value, str):
            value = '"' + value.encode("string_escape") + '"'
        if isinstance(value, unicode):
            value = 'u"' + value.encode(
                                    sys.getdefaultencoding(),
                                    'replace').encode("string_escape") + '"'
        try:
            var += "%s = %s" % (key, value)
        except:
            var += "%s = %s" % (key, type(value))
        if len(var) > width:
            var = var[:width - 3] + '...'
        result += var + "\n"
    return result

def print_list(extracted_list, afile=None, with_vars=True):
    """Print the list of tuples as returned by extract_tb() or
    extract_stack() as a formatted stack trace to the given file."""
    if afile is None:
        afile = sys.stderr
    for filename, lineno, name, line, alocals in extracted_list:
        _print(afile,
               '  File "%s", line %d, in %s' % (filename, lineno, name))
        if with_vars:
            _print(afile, '    Local variables:')
            print_vars(sorted(alocals), afile=afile)
        if line:
            _print(afile, '    %s' % line.strip())

def format_list(extracted_list, with_vars=True):
    """Format a list of traceback entry tuples for printing.

    Given a list of tuples as returned by extract_tb() or
    extract_stack(), return a list of strings ready for printing.
    Each string in the resulting list corresponds to the item with the
    same index in the argument list.  Each string ends in a newline;
    the strings may contain internal newlines as well, for those items
    whose source text line is not None.
    """
    alist = []
    for filename, lineno, name, line, alocals in extracted_list:
        item = '  File "%s", line %d, in %s\n' % (filename, lineno, name)
        if with_vars:
            item += '    Local variables:\n'
            item += format_vars(sorted(alocals))
        if line:
            item = item + '    %s\n' % line.strip()
        alist.append(item)
    return alist


def print_tb(traceb, limit=None, afile=None, with_vars=True):
    """Print up to 'limit' stack trace entries from the traceback 'traceb'.

    If 'limit' is omitted or None, all entries are printed.  If 'afile'
    is omitted or None, the output goes to sys.stderr; otherwise
    'afile' should be an open file or file-like object with a write()
    method.
    """
    if afile is None:
        afile = sys.stderr
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    n = 0
    while traceb is not None and (limit is None or n < limit):
        frame = traceb.tb_frame
        lineno = traceb.tb_lineno
        co = frame.f_code
        filename = co.co_filename
        name = co.co_name
        _print(afile,
               '  File "%s", line %d, in %s' % (filename, lineno, name))
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, frame.f_globals)
        alocals = frame.f_locals.items()
        if with_vars:
            _print(afile, '    Local variables:')
            print_vars(sorted(alocals))
        if line:
            _print(afile, '    ' + line.strip())
        traceb = traceb.tb_next
        n = n + 1

def format_tb(traceb, limit=None, with_vars=False):
    """A shorthand for 'format_list(extract_stack(frame, limit))."""
    return format_list(extract_tb(traceb, limit), with_vars)

def extract_tb(traceb, limit=None):
    """Return list of up to limit pre-processed entries from traceback.

    This is useful for alternate formatting of stack traces.  If
    'limit' is omitted or None, all entries are extracted.  A
    pre-processed stack trace entry is a quadruple (filename, line
    number, function name, text) representing the information that is
    usually printed for a stack trace.  The text is a string with
    leading and trailing whitespace stripped; if the source is not
    available it is None.
    """
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    alist = []
    n = 0
    while traceb is not None and (limit is None or n < limit):
        frame = traceb.tb_frame
        lineno = traceb.tb_lineno
        co = frame.f_code
        filename = co.co_filename
        name = co.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, frame.f_globals)
        if line: line = line.strip()
        else: line = None
        alocals = frame.f_locals.items()
        alist.append((filename, lineno, name, line, alocals))
        traceb = traceb.tb_next
        n = n + 1
    return alist


def print_exception(etype, value, traceb, limit=None, afile=None, with_vars=False):
    """Print exception up to 'limit' stack trace entries from 'traceb' to 'afile'.

    This differs from print_tb() in the following ways: (1) if
    traceback is not None, it prints a header "Traceback (most recent
    call last):"; (2) it prints the exception type and value after the
    stack trace; (3) if type is SyntaxError and value has the
    appropriate format, it prints the line where the syntax error
    occurred with a caret on the next line indicating the approximate
    position of the error.
    """
    if afile is None:
        afile = sys.stderr
    if traceb:
        _print(afile, 'Traceback (most recent call last):')
        print_tb(traceb, limit, afile, with_vars)
    lines = format_exception_only(etype, value)
    for line in lines:
        _print(afile, line, '')

def format_exception(etype, value, traceb, limit=None, with_vars=False):
    """Format a stack trace and the exception information.

    The arguments have the same meaning as the corresponding arguments
    to print_exception().  The return value is a list of strings, each
    ending in a newline and some containing internal newlines.  When
    these lines are concatenated and printed, exactly the same text is
    printed as does print_exception().
    """
    if traceb:
        alist = ['Traceback (most recent call last):\n']
        alist = alist + format_tb(traceb, limit, with_vars)
    else:
        alist = []
    alist = alist + format_exception_only(etype, value)
    return alist

def format_exception_only(etype, value):
    """Format the exception part of a traceback.

    The arguments are the exception type and value such as given by
    sys.last_type and sys.last_value. The return value is a list of
    strings, each ending in a newline.

    Normally, the list contains a single string; however, for
    SyntaxError exceptions, it contains several lines that (when
    printed) display detailed information about where the syntax
    error occurred.

    The message indicating which exception occurred is always the last
    string in the list.

    """

    # An instance should not have a meaningful value parameter, but
    # sometimes does, particularly for string exceptions, such as
    # >>> raise string1, string2  # deprecated
    #
    # Clear these out first because issubtype(string1, SyntaxError)
    # would throw another exception and mask the original problem.
    if (isinstance(etype, BaseException) or
        isinstance(etype, types.InstanceType) or
        etype is None or type(etype) is str):
        return [_format_final_exc_line(etype, value)]

    stype = etype.__name__

    if not issubclass(etype, SyntaxError):
        return [_format_final_exc_line(stype, value)]

    # It was a syntax error; show exactly where the problem was found.
    lines = []
    try:
        msg, (filename, lineno, offset, badline) = value.args
    except Exception:
        pass
    else:
        filename = filename or "<string>"
        lines.append('  File "%s", line %d\n' % (filename, lineno))
        if badline is not None:
            lines.append('    %s\n' % badline.strip())
            if offset is not None:
                caretspace = badline.rstrip('\n')[:offset].lstrip()
                # non-space whitespace (likes tabs) must be kept for alignment
                caretspace = ((c.isspace() and c or ' ') for c in caretspace)
                # only three spaces to account for offset1 == pos 0
                lines.append('   %s^\n' % ''.join(caretspace))
            value = msg

    lines.append(_format_final_exc_line(stype, value))
    return lines

def _format_final_exc_line(etype, value):
    """Return a list of a single line 
    
       -- normal case for format_exception_only
    """
    valuestr = _some_str(value)
    if value is None or not valuestr:
        line = "%s\n" % etype
    else:
        line = "%s: %s\n" % (etype, valuestr)
    return line

def _some_str(value):
    try:
        return str(value)
    except Exception:
        pass
    try:
        value = unicode(value)
        return value.encode("ascii", "backslashreplace")
    except Exception:
        pass
    return '<unprintable %s object>' % type(value).__name__


def print_exc(limit=None, afile=None):
    """Shorthand for 'print_exception(
                            sys.exc_type, 
                            sys.exc_value, 
                            sys.exc_traceback, 
                            limit, 
                            afile)'.
    (In fact, it uses sys.exc_info() to retrieve the same information
    in a thread-safe way.)"""
    if afile is None:
        afile = sys.stderr
    try:
        etype, value, traceb = sys.exc_info()
        print_exception(etype, value, traceb, limit, afile)
    finally:
        etype = value = traceb = None


def format_exc(limit=None, with_vars=False):
    """Like print_exc() but return a string."""
    try:
        etype, value, traceb = sys.exc_info()
        return ''.join(format_exception(etype, value, traceb, limit, with_vars))
    finally:
        etype = value = traceb = None


def print_last(limit=None, afile=None):
    """This is a shorthand for 'print_exception(sys.last_type,
    sys.last_value, sys.last_traceback, limit, afile)'."""
    if not hasattr(sys, "last_type"):
        raise ValueError("no last exception")
    if afile is None:
        afile = sys.stderr
    print_exception(sys.last_type,
                    sys.last_value, #@UndefinedVariable
                    sys.last_traceback, #@UndefinedVariable
                    limit, afile)


def print_stack(frame=None, limit=None, afile=None, with_vars=False):
    """Print a stack trace from its invocation point.

    The optional 'frame' argument can be used to specify an alternate
    stack frame at which to start. The optional 'limit' and 'afile'
    arguments have the same meaning as for print_exception().
    """
    if frame is None:
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            frame = sys.exc_info()[2].tb_frame.f_back
    if afile is None:
        afile = sys.stderr
    print_list(extract_stack(frame, limit), afile, with_vars)

def format_stack(frame=None, limit=None, with_vars=False):
    """Shorthand for 'format_list(extract_stack(frame, limit))'."""
    if frame is None:
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            frame = sys.exc_info()[2].tb_frame.f_back
    return format_list(extract_stack(frame, limit), with_vars)

def extract_stack(frame=None, limit=None):
    """Extract the raw traceback from the current stack frame.

    The return value has the same format as for extract_tb().  The
    optional 'frame' and 'limit' arguments have the same meaning as for
    print_stack().  Each item in the list is a quadruple (filename,
    line number, function name, text), and the entries are in order
    from oldest to newest stack frame.
    """
    if frame is None:
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            frame = sys.exc_info()[2].tb_frame.f_back
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    alist = []
    n = 0
    while frame is not None and (limit is None or n < limit):
        lineno = frame.f_lineno
        co = frame.f_code
        filename = co.co_filename
        name = co.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, frame.f_globals)
        if line: line = line.strip()
        else: line = None
        alocals = frame.f_locals.items()
        alist.append((filename, lineno, name, line, alocals))
        frame = frame.f_back
        n = n + 1
    alist.reverse()
    return alist

def tb_lineno(traceb):
    """Calculate correct line number of traceback given in traceb.

    Obsolete in 2.3.
    """
    return traceb.tb_lineno
