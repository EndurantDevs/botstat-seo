import os
import re
import subprocess
from pyparsing import Literal, Word, ZeroOrMore, OneOrMore, Group
from pyparsing import printables, quotedString, pythonStyleComment
from pyparsing import removeQuotes
import logging
from six.moves import input


DEFAULT_APACHE_LOG_FORMAT = r'%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-agent}i"'
REGEX_SPECIAL_CHARS = r'([\.\*\+\?\|\(\)\{\}\[\]])'
REGEX_LOG_FORMAT_VARIABLE = r'\$([a-z0-9\_]+)'
LOG_FORMATS = {"combined": '$remote_addr - $remote_user [$time_local] ' +
                           '"$request" $status $body_bytes_sent ' +
                           '"$http_referer" "$http_user_agent"',
               "common": '$remote_addr - $remote_user [$time_local] ' +
                         '"$request" $status $body_bytes_sent ' +
                         '"$http_x_forwarded_for"'}


semicolon = Literal(';').suppress()
parameter = Word(''.join(c for c in printables if c not in set('{;"\''))) \
            | quotedString.setParseAction(removeQuotes)


def detect_nginx_config_path():
    try:
        proc = subprocess.Popen(['nginx', '-V'], stderr=subprocess.PIPE)
    except OSError:
        raise SystemExit('Access log file or format was not set and nginx '
                         'config file cannot be detected. '
                         'Perhaps nginx is not in your PATH?')
    stdout, stderr = proc.communicate()
    version_output = stderr.decode('utf-8')
    conf_path_match = re.search(r'--conf-path=(\S*)', version_output)
    if conf_path_match is not None:
        return conf_path_match.group(1)
    prefix_match = re.search(r'--prefix=(\S*)', version_output)
    if prefix_match is not None:
        return prefix_match.group(1) + '/conf/nginx.conf'
    return '/etc/nginx/nginx.conf'


def extract_access_logs(config):
    access_log = Literal("access_log") + ZeroOrMore(parameter) + semicolon
    access_log.ignore(pythonStyleComment)
    for directive in access_log.searchString(config).asList():
        path = directive[1]
        if path == 'off' or path.startswith('syslog:'):
            continue
        format_name = 'combined'
        if len(directive) > 2 and '=' not in directive[2]:
            format_name = directive[2]
        yield path, format_name


def extract_log_format(config):
    log_format = Literal('log_format') + parameter \
                 + Group(OneOrMore(parameter)) + semicolon
    log_format.ignore(pythonStyleComment)
    for directive in log_format.searchString(config).asList():
        name = directive[1]
        format_string = ''.join(directive[2])
        yield name, format_string


def choose_one(choices, prompt):
    for idx, choice in enumerate(choices):
        print('%d. %s' % (idx + 1, choice))
    selected = None
    while selected is None or not 0 <= selected <= len(choices):
        selected = input(prompt)
        try:
            selected = int(selected)
        except ValueError:
            selected = None
    return choices[selected - 1]


def detect_log_config(arguments):
    config = arguments.nginx_config
    if config is None:
        config = detect_nginx_config_path()
    if not os.path.exists(config):
        raise SystemExit('Nginx config file not found: %s' % config)
    with open(config) as fobj:
        config_str = fobj.read()
    access_logs = dict(extract_access_logs(config_str))
    if not access_logs:
        raise SystemExit('Access log file is not provided and ngxtop cannot detect '
                         'it from your config file (%s).' % config)
    log_formats = dict(extract_log_format(config_str))
    if len(access_logs) == 1:
        log_path, format_name = next(iter(access_logs.items()))
        if format_name == 'combined':
            return log_path, LOG_FORMATS["combined"]
        if format_name not in log_formats:
            raise SystemExit('Incorrect format name set in config for access log file "%s"' % log_path)
        return log_path, log_formats[format_name]
    print('Multiple access logs detected in configuration:')
    log_path = choose_one(list(access_logs.keys()), 'Select access log file to process: ')
    format_name = access_logs[log_path]
    if format_name not in log_formats:
        raise SystemExit('Incorrect format name set in config for access log file "%s"' % log_path)
    return log_path, log_formats[format_name]


def build_log_format_regex(log_format):
    if log_format in LOG_FORMATS:
        log_format = LOG_FORMATS[log_format]
    pattern = re.sub(REGEX_SPECIAL_CHARS, r'\\\1', log_format)
    pattern = re.sub(REGEX_LOG_FORMAT_VARIABLE, '(?P<\\1>.*)', pattern)
    logging.debug("Log parse regexp: %s", pattern)
    return re.compile(pattern)


def check_regex_required_fields(re_expression, fields):
    for field in fields:
        if 'P<%s>' % (field,) not in re_expression.pattern:
            raise SystemExit("\"%s\" is a required field in log format, but it isn't present" % (field,))
