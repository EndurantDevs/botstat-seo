from datetime import date
import re
from io import BytesIO
from botstat.botstat import seek_to_date


DATE = date(year=2018, month=9, day=3)
RE_PARSER = re.compile(r'.*\[(?P<time_local>.*)\].*')


def test_in_the_middle():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:10]\n"
        "3 [2018/09/03 12:09:11]\n"
        "4 [2018/09/03 12:09:19]\n"
        "5 [2018/09/03 12:09:29]\n"
        "6 [2018/09/04 12:09:09]\n"
        "7 [2018/09/04 12:19:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "3 [2018/09/03 12:09:11]\n"


def test_first_line():
    stream = BytesIO(
        "3 [2018/09/03 12:09:09]\n"
        "4 [2018/09/03 12:09:19]\n"
        "5 [2018/09/03 12:09:29]\n"
        "6 [2018/09/04 12:09:09]\n"
        "7 [2018/09/04 12:19:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "3 [2018/09/03 12:09:09]\n"


def test_last_line():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "3 [2018/09/03 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "3 [2018/09/03 12:09:09]\n"


def test_at_the_end():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "3 [2018/09/03 12:09:09]\n"
        "4 [2018/09/03 12:09:19]\n"
        "5 [2018/09/03 12:09:29]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "3 [2018/09/03 12:09:09]\n"


def test_in_the_middle_not_exact():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "6 [2018/09/04 12:09:09]\n"
        "7 [2018/09/04 12:09:19]\n"
        "8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "6 [2018/09/04 12:09:09]\n"


def test_first_line_not_exact():
    stream = BytesIO(
        "6 [2018/09/04 12:09:09]\n"
        "7 [2018/09/04 12:19:09]\n"
        "8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "6 [2018/09/04 12:09:09]\n"


def test_last_line_not_exact():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "6 [2018/09/04 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "6 [2018/09/04 12:09:09]\n"


def test_at_the_end_not_exact():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "6 [2018/09/04 12:09:09]\n"
        "7 [2018/09/04 12:19:09]\n"
        "8 [2018/09/05 12:09:09]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "6 [2018/09/04 12:09:09]\n"


def test_all_are_less():
    stream = BytesIO(
        "1 [2018/09/01 12:09:09]\n"
        "2 [2018/09/02 12:09:09]\n"
        "3 [2018/09/02 12:19:09]\n"
        "4 [2018/09/02 12:29:19]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == ""
    position = stream.tell()
    assert position == stream.seek(0, 2) # check is eof


def test_all_are_larger():
    stream = BytesIO(
        "1 [2018/09/05 12:09:09]\n"
        "2 [2018/09/06 12:09:09]\n"
        "3 [2018/09/07 12:19:09]\n"
        "4 [2018/09/08 12:29:19]\n"
    )
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == "1 [2018/09/05 12:09:09]\n"


def test_empty():
    stream = BytesIO("")
    seek_to_date(stream, DATE, RE_PARSER)
    assert stream.readline() == ""
