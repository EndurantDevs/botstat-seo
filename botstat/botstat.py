from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import logging
import configargparse
import os
import socket
from dateutil import parser
import datetime
from collections import defaultdict
from collections import Counter
import csv
import apache_log_parser
from tempfile import TemporaryFile
from .mail import send_mail
from six import iteritems
from six import itervalues
from six.moves import input
from .log_processing import detect_log_config
from .log_processing import build_log_format_regex
from .log_processing import check_regex_required_fields
from .log_processing import DEFAULT_APACHE_LOG_FORMAT

# Bots list in format:
# "bot name in user agent": "pretty name for report"
# if some bot has several identify string in user agent field
# than need to specify all them as key with one value, statistic
# will aggregate by pretty bot name
BOT_LIST = {'Googlebot': 'Google',
            'Bingbot': 'Bing',
            'Slurp': 'Yahoo',
            'DuckDuckBot': 'DuckDuckGo',
            'Baiduspider': 'Baidu',
            'YandexBot': 'Yandex',
            'Sogou': 'Sogou',
            'ia_archiver': 'Alexa'}


def configure_logging(args):
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')


def parse_argumets():
    arg_parser = configargparse.ArgParser(
        default_config_files=['/etc/botstat.conf', '~/.botstat'],
        prog="botstat",
        description="Parse web server logs and make bots statistic",
    )
    arg_parser.add(
        '-c', '--my-config',
        required=False,
        is_config_file=True,
        help='config file path'
    )
    arg_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    arg_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    arg_parser.add_argument(
        "--log-format",
        help="Web server log format like 'log_format' in nginx.conf. "
             "Accept 'combined', 'common' or format string field names with $"
    )
    arg_parser.add_argument(
        "--nginx-config",
        help="Nginx config file name with path"
    )
    arg_parser.add_argument(
        "--access-log",
        help="Access log file name. If not specify used stdin."
    )
    arg_parser.add_argument(
        "--day-start",
        type=int,
        help="Days from the beginning of today, all older records skipped"
    )
    arg_parser.add_argument(
        "--date-start",
        help="Start date for parsing log, all older records skipped"
    )
    arg_parser.add_argument(
        "--mail-to",
        help="Email address to send report"
    )
    arg_parser.add_argument(
        "--mail-from", help="'Email FROM' address"
    )
    arg_parser.add_argument(
        "--mail-subject",
        help="Report email subject",
        default="Search bot statistics from %s" % datetime.date.today().strftime("%Y/%m/%d")
    )
    arg_parser.add_argument(
        "--smtp-host",
        help="SMTP server host name or ip adddress",
        default="127.0.0.1"
    )
    arg_parser.add_argument(
        "--smtp-port",
        type=int,
        help="SMTP server port"
    )
    arg_parser.add_argument(
        "--server-type",
        choices=["nginx", "apache"],
        default="nginx",
        help="Web server type, support nginx and apache (default: %(default)s)"
    )
    return arg_parser.parse_args()


def generate_start_date(args):
    if args.date_start:
        return parser.parse(args.date_start).date()
    elif args.day_start:
        return datetime.date.today() - datetime.timedelta(days=args.day_start)


def make_stats(records, args):
    date_start = generate_start_date(args)
    logging.debug("Date start: %s", date_start)
    # date -> bot -> vhost -> {2xx, 3xx, 4xx, 5xx} -> { count, bytes, time }
    stats = defaultdict(              # date
        lambda: defaultdict(          # bot name
            lambda: defaultdict(      # vhost
                lambda: defaultdict(  # http code
                    Counter
                )
            )
        )
    )
    system_hostname = socket.gethostname()
    for record in records:
        record_date = parser.parse(record['time_local'], fuzzy=True).date()
        if date_start is None or record_date >= date_start:
            for bot, bot_name in iteritems(BOT_LIST):
                if bot.lower() in record['http_user_agent'].lower():
                    status = (int(int(record['status'])/100))*100
                    hostname = record.get('host', system_hostname)
                    status_record = stats[record_date][bot_name][hostname][status]
                    status_record['count'] += 1
                    if 'body_bytes_sent' in record:
                        bytes_sent = 0 if record['body_bytes_sent'] == '-' else int(record['body_bytes_sent'])
                        status_record['bytes'] += bytes_sent
                    if 'request_time' in record:
                        status_record['time'] += float(record['request_time'])
                    break
    return stats


def make_csv(stats, stream):
    writer = csv.writer(stream)
    header = ["Date", "Bot", "Host", "Hits 2xx", "Hits 3xx", "Hits 4xx",
              "Hits 5xx", "All Hits", "Avg Time, ms", "Avg Time 2xx, ms",
              "Total Time, sec", "Total Time 2xx, sec",
              "Total Time 5xx, sec", "Bytes Total",
              "Avg Bytes", "Avg 2xx Bytes"]
    writer.writerow(header)
    for date, bot_data in iteritems(stats):
        for bot, host_data in iteritems(bot_data):
            for host, data in iteritems(host_data):
                writer.writerow(
                    [date.strftime('%Y/%m/%d'), bot, host,       # date, bot, vhost
                     data[200]['count'],                         # hits_2xx
                     data[300]['count'],                         # hits_3xx
                     data[400]['count'],                         # hits_4xx
                     data[500]['count'],                         # hits_5xx
                     sum(x['count'] for x in itervalues(data)),  # hits_all
                     int(1000 * sum(
                                    x['time'] for x in itervalues(data)
                                ) / (sum(x['count'] for x in itervalues(data)) or 1)),  # avg_time_all
                     int(1000 * data[200]['time'] / (data[200]['count'] or 1)),  # avg_time_2xx
                     sum(x['time'] for x in itervalues(data)),   # total_time_all
                     data[200]['time'],                          # total_time_2xx
                     data[500]['time'],                          # total_time_5xx
                     sum(x['bytes'] for x in itervalues(data)),  # bytes_all
                     sum(x['bytes'] for x in itervalues(data))/(len(data.keys()) or 1),  # avg_bytes_all
                     data[200]['bytes'] / (data[200]['count'] or 1)  # avg_bytes_2xx
                     ]
                )


def make_report(stats, access_log, args):
    with TemporaryFile(mode="w+") as csv_stream:
        make_csv(stats, csv_stream)
        csv_stream.flush()
        csv_stream.seek(0)
        if access_log == "stdin":
            filename = "stdin.csv"
        else:
            filename = "%s.csv" % (os.path.basename(access_log).rsplit('.', 1)[0])
        start_date = generate_start_date(args)
        if start_date:
            text = "Search bot statistics from %s to %s" % (start_date,  datetime.date.today())
        else:
            text = "Search bot statistics for all time"
        send_mail(text, csv_stream, filename, args)


def process_nginx(access_log, args):
    if access_log is None:
        access_log, log_format = detect_log_config(args)
    else:
        log_format = None
    if args.log_format:
        log_format = args.log_format
    logging.info("access_log: %s", access_log)
    logging.info("log_format: %s", log_format)
    if access_log != "stdin" and not os.path.exists(access_log):
        raise SystemExit("Access log file \"%s\" does not exist" % access_log)
    if log_format is None:
        raise SystemExit("Nginx log_format is not set and can't be detected automatically")
    if access_log == "stdin":
        stream = sys.stdin
    else:
        stream = open(access_log)
    regex_parser = build_log_format_regex(log_format)
    check_regex_required_fields(
        regex_parser,
        ('status', 'http_user_agent', 'time_local',)
    )
    matches = (regex_parser.match(l) for l in stream)
    return (m.groupdict() for m in matches if m is not None)


def convert_field_names(record):
    translations = (('request_header_user_agent', 'http_user_agent'),
                    ('response_bytes', 'body_bytes_sent'),
                    ('time_us', 'request_time'),
                    ('time_received', 'time_local'),
                    ('server_name', 'host'))
    if 'response_bytes' not in record and 'response_bytes_clf' in record:
        record['response_bytes'] = record['response_bytes_clf']
    for apache, nginx in translations:
        if apache in record:
            record[nginx] = record[apache]
            del record[apache]
    if 'request_time' in record:
        record['request_time'] = record['request_time']/10000000.0  # convert time from microseconds to float like nginx
    return record


def process_apache(access_log, args):
    log_format = args.log_format
    if log_format is None:
        response = None
        while not response or response not in 'yn':
            response = input(
                "No log_format for apache configured, use default? \n%s\n(Y/N) "
                % (DEFAULT_APACHE_LOG_FORMAT, )
            ).lower()
        if response == 'y':
            log_format = DEFAULT_APACHE_LOG_FORMAT
        else:
            raise SystemExit("Apache log_format is not set and can't be detected automatically.")
    if access_log is None:
        raise SystemExit("Access log file is not set for apache and cannot be detected.")
    line_parser = apache_log_parser.make_parser(log_format)
    if access_log == "stdin":
        stream = sys.stdin
    else:
        stream = open(access_log)
    return (convert_field_names(line_parser(line)) for line in stream)


def main():
    args = parse_argumets()
    configure_logging(args)
    logging.debug("Arguments: %s", vars(args))
    access_log = args.access_log
    if access_log is None and not sys.stdin.isatty():
        access_log = "stdin"
    if args.server_type == 'nginx':
        records = process_nginx(access_log, args)
    elif args.server_type == 'apache':
        records = process_apache(access_log, args)
    else:
        raise SystemExit("Unknown server type %s" % (args.server_type,))
    stats = make_stats(records, args)
    make_report(stats, access_log, args)


if __name__ == '__main__':
    main()
