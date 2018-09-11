from io import BytesIO
from botstat.botstat import get_nearest_line


def test_first():
    stream = BytesIO("123\n"
                     "456\n"
                     "789\n")
    assert get_nearest_line(stream, 0) == "123\n"


def test_first_in_the_middle():
    stream = BytesIO("123\n"
                     "456\n"
                     "789\n")
    stream.seek(2)
    assert get_nearest_line(stream, 0) == "123\n"


def test_second_in_the_middle():
    stream = BytesIO("123\n"
                     "456\n"
                     "789\n")
    stream.seek(5)
    assert get_nearest_line(stream, 0) == "456\n"


def test_second_in_the_less_start():
    stream = BytesIO("123\n"
                     "456\n"
                     "789\n")
    stream.seek(5)
    assert get_nearest_line(stream, 6) is None


def test_last_in_the_middle():
    stream = BytesIO("123\n"
                     "456\n"
                     "789\n")
    stream.seek(10)
    assert get_nearest_line(stream, 0) == "789\n"