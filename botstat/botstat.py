import sys
import logging
import argparse
import os
from config import detect_log_config
from config import detect_nginx_config_path
from config import build_log_format_regex


def configure_logging(args):
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')


def parse_argumets():
    parser = argparse.ArgumentParser(prog="botstat",
                                     description="Parse web server logs and make bots statistic")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log_format", help="Web server log format like 'log_format' in nginx.conf. "
                                             "Accept 'combined', 'common' or format string field "
                                             "names with $")
    parser.add_argument("--nginx_config", help="Nginx config file name with path")
    parser.add_argument("--access_log", help="Access log file name. If not specify used stdin.")
    return parser.parse_args()


def main():
    args = parse_argumets()
    configure_logging(args)
    logging.debug("Arguments: %s", vars(args))
    access_log = args.access_log
    log_format = args.log_format
    if access_log is None and not sys.stdin.isatty():
        access_log = "stdin"
    if access_log is None:
        access_log, log_format = detect_log_config(args)
    logging.info("access_log: %s", access_log)
    logging.info("log_format: %s", log_format)

    if access_log != "stdin" and not os.path.exists(access_log):
        raise SystemExit("Access log file \"%s\" does not exist" % access_log)
    if access_log == "stdin":
        stream = sys.stdin
    else:
        stream = open(access_log)
    parser = build_log_format_regex(log_format)
    logging.debug("Log parse regexp: %s", parser.pattern)
    matches = (parser.match(l) for l in stream)
    records = (m.groupdict() for m in matches if m is not None)


if __name__ == '__main__':
    main()
