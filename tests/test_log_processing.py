import pytest
import re
from botstat.log_processing import check_regex_required_fields
from botstat.log_processing import build_log_format_regex
from botstat.log_processing import LOG_FORMATS


def test_check_regex_required_fields_raise():
    expression = re.compile(r'(?P<host>.*) (?P<name>.*)')
    with pytest.raises(SystemExit) as excinfo:
        check_regex_required_fields(expression, ('name', 'required_field', 'host'))
    assert '"required_field"' in str(excinfo.value)


def test_check_regex_required_fields_pass():
    expression = re.compile(r'(?P<host>.*) (?P<name>.*) (?P<required_field>.*)')
    try:
        check_regex_required_fields(expression, ('name', 'required_field', 'host'))
    except SystemExit:
        raise pytest.fail("Did raise {0}".format(SystemExit))


def test_build_log_format_regex_combined():
    expression = build_log_format_regex(LOG_FORMATS['combined'])
    pattern = re.compile(r'(?P<remote_addr>.*) - (?P<remote_user>.*) \[(?P<time_local>.*)\] '
                         r'"(?P<request>.*)" (?P<status>.*) (?P<body_bytes_sent>.*) '
                         r'"(?P<http_referer>.*)" "(?P<http_user_agent>.*)"')
    assert expression == pattern


def test_build_log_format_regex_common():
    expression = build_log_format_regex(LOG_FORMATS['common'])
    pattern = re.compile(r'(?P<remote_addr>.*) - (?P<remote_user>.*) \[(?P<time_local>.*)\] '
                         r'"(?P<request>.*)" (?P<status>.*) (?P<body_bytes_sent>.*) '
                         r'"(?P<http_x_forwarded_for>.*)"')
    assert expression == pattern
