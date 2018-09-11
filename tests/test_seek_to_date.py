from datetime import date
import re
from io import StringIO
from botstat.botstat import seek_to_date


DATE = date(year=2018, month=9, day=3)
RE_PARSER = re.compile(r'.*\[(?P<time_local>.*)\].*')


def test_in_the_middle():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:10]\n"
        u"3 [2018/09/03 12:09:11]\n"
        u"4 [2018/09/03 12:09:19]\n"
        u"5 [2018/09/03 12:09:29]\n"
        u"6 [2018/09/04 12:09:09]\n"
        u"7 [2018/09/04 12:19:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"3 [2018/09/03 12:09:11]\n"


def test_first_line():
    stream = StringIO(
        u"3 [2018/09/03 12:09:09]\n"
        u"4 [2018/09/03 12:09:19]\n"
        u"5 [2018/09/03 12:09:29]\n"
        u"6 [2018/09/04 12:09:09]\n"
        u"7 [2018/09/04 12:19:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"3 [2018/09/03 12:09:09]\n"


def test_last_line():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"3 [2018/09/03 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"3 [2018/09/03 12:09:09]\n"


def test_at_the_end():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"3 [2018/09/03 12:09:09]\n"
        u"4 [2018/09/03 12:09:19]\n"
        u"5 [2018/09/03 12:09:29]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"3 [2018/09/03 12:09:09]\n"


def test_in_the_middle_not_exact():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"6 [2018/09/04 12:09:09]\n"
        u"7 [2018/09/04 12:09:19]\n"
        u"8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"6 [2018/09/04 12:09:09]\n"


def test_first_line_not_exact():
    stream = StringIO(
        u"6 [2018/09/04 12:09:09]\n"
        u"7 [2018/09/04 12:19:09]\n"
        u"8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"6 [2018/09/04 12:09:09]\n"


def test_last_line_not_exact():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"6 [2018/09/04 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"6 [2018/09/04 12:09:09]\n"


def test_at_the_end_not_exact():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"6 [2018/09/04 12:09:09]\n"
        u"7 [2018/09/04 12:19:09]\n"
        u"8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"6 [2018/09/04 12:09:09]\n"


def test_all_are_less():
    stream = StringIO(
        u"1 [2018/09/01 12:09:09]\n"
        u"2 [2018/09/02 12:09:09]\n"
        u"3 [2018/09/02 12:19:09]\n"
        u"4 [2018/09/02 12:29:19]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u""
    position = stream.tell()
    assert position == stream.seek(0, 2) # check is eof


def test_all_are_larger():
    stream = StringIO(
        u"1 [2018/09/05 12:09:09]\n"
        u"2 [2018/09/06 12:09:09]\n"
        u"3 [2018/09/07 12:19:09]\n"
        u"4 [2018/09/08 12:29:19]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u"1 [2018/09/05 12:09:09]\n"


def test_empty():
    stream = StringIO(u"")
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == u""
