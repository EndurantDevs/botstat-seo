import sys
import logging
import argparse
from config import detect_log_config, detect_config_path, extract_variables, build_pattern


def main():
    parser = argparse.ArgumentParser(prog="botstat",
                                     description="Parse web server logs and make bots statistic")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--log_format", help="Web server log format like 'log_format' in nginx.conf. "
                                             "Accept 'combined', 'common' or format string field "
                                             "names with $")
    parser.add_argument("--nginx_config", help="Nginx config file name with path")
    parser.add_argument("--access_log", help="Access log file name. If not specify used stdin.")
    args = parser.parse_args()
    access_log = args.access_log
    log_format = args.log_format
    if access_log is None and not sys.stdin.isatty():
        access_log = sys.stdin
    if access_log is None:
        access_log, log_format = detect_log_config(args)


if __name__ == '__main__':
    main()
