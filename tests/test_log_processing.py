import pytest
import re
from botstat.log_processing import check_regex_required_fields
from botstat.log_processing import build_log_format_regex
from botstat.log_processing import LOG_FORMATS
from botstat.log_processing import extract_access_logs
from botstat.log_processing import extract_log_format


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


def test_extract_access_logs_format_name():
    config = '''
        http {
            access_log /path/to/access.log main gzip=15 buffer=64k flush=5m;
            server {
                access_log /path/to/vhost.log 'custom format';
            }
        }
    '''
    logs = dict(extract_access_logs(config))
    assert len(logs) == 2
    assert logs['/path/to/access.log'] == 'main'
    assert logs['/path/to/vhost.log'] == 'custom format'


def test_extract_access_log_format():
    config = '''
user root;
worker_processes auto;
pid /run/nginx.pid;
events {
  worker_connections 1024;
  # multi_accept on;
}
http {
  sendfile on;
  keepalive_timeout 65;
  types_hash_max_size 2048;
  server_tokens off;
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  ssl_prefer_server_ciphers on;
  log_format main '$remote_addr $host $remote_user [$time_local] "$request" '
                  '$status $body_bytes_sent "$http_referer" '
                  '"$http_user_agent" $request_time -$http_x_forwarded_for-';
  access_log /var/log/nginx/access.log main;
  include /etc/nginx/conf.d/*.conf;
  include /etc/nginx/sites-enabled/*;
}'''
    logs = dict(extract_log_format(config))
    assert len(logs) == 1
    assert logs['main'] == '$remote_addr $host $remote_user [$time_local] ' \
                           '"$request" $status $body_bytes_sent "$http_referer" ' \
                           '"$http_user_agent" $request_time -$http_x_forwarded_for-'
