import sys
import logging
import argparse
import os
from dateutil import parser
import datetime
from collections import defaultdict
import csv
from config import detect_log_config
from config import build_log_format_regex
from tempfile import NamedTemporaryFile
from mail import send_mail


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
    parser.add_argument("--day_start", type=int, help="Days from the beginning of today, all older records skipped")
    parser.add_argument("--date_start", help="Start date for parsing log, all older records skipped")
    parser.add_argument("--mail-to", help="Email address to send report")
    parser.add_argument("--mail-from", help="'Email FROM' address")
    parser.add_argument("--mail-subject", help="Report email subject",
                        default="Search bot statistics from %s" % datetime.date.today().strftime("%Y/%m/%d"))
    parser.add_argument("--smtp_host", help="SMTP server host name or ip adddress", default="127.0.0.1")
    parser.add_argument("--smtp_port", type=int, help="SMTP server port")
    return parser.parse_args()


def generate_start_date(args):
    if args.date_start:
        return parser.parse(args.date_start).date()
    elif args.day_start:
        return datetime.date.today() - datetime.timedelta(days=args.day_start)


def make_stats(records, args):
    date_start = generate_start_date(args)
    logging.debug("Date start: %s", date_start)
    #date -> bot -> vhost -> {2xx, 3xx, 4xx, 5xx} -> { count, bytes, time }
    stats = defaultdict(            #date
        lambda:defaultdict(         #bot name
            lambda: defaultdict(    #vhost
                lambda:defaultdict( #http code
                    lambda:{'count':0, 'bytes':0, 'time':.0}
                )
            )
        )
    )
    for record in records:
        record_date = parser.parse(record['time_local'], fuzzy=True).date()
        if date_start is None or record_date >= date_start:
            for bot in ('Googlebot', 'bingbot'):
                if bot in record['http_user_agent']:
                    status = (int(record['status'])/100)*100
                    stats[record_date][bot][record['host']][status]['count'] += 1
                    stats[record_date][bot][record['host']][status]['bytes'] += int(record['body_bytes_sent'])
                    stats[record_date][bot][record['host']][status]['time'] += float(record['request_time'])
                    break
    return stats


def make_csv(stats, stream):
    writer = csv.writer(stream)
    header = ["date", "bot", "vhost", "hits_2xx", "hits_3xx", "hits_4xx",
              "hits_5xx", "hits_all", "total_time_all", "total_time_2xx",
              "total_time_5xx", "bytes_all", "avg_time_all", "avg_time_2xx",
              "avg_bytes_all", "avg_bytes_2xx"]
    writer.writerow(header)
    for date, bot_data in stats.iteritems():
        for bot, host_data in bot_data.iteritems():
            for host, data in host_data.iteritems():
                writer.writerow([date.strftime('%Y/%m/%d'), bot, host, # date, bot, vhost
                                 data[200]['count'], # hits_2xx
                                 data[300]['count'], # hits_3xx
                                 data[400]['count'], # hits_4xx
                                 data[500]['count'], # hits_5xx
                                 sum(x['count'] for x in data.itervalues()), # hits_all
                                 sum(x['time'] for x in data.itervalues()),  # total_time_all
                                 data[200]['time'], # total_time_2xx
                                 data[500]['time'], # total_time_5xx
                                 sum(x['bytes'] for x in data.itervalues()), # bytes_all
                                 sum(x['time'] for x in data.itervalues())/(len(data.keys()) or 1), # avg_time_all
                                 data[200]['time'] / (data[200]['count'] or 1), # avg_time_2xx
                                 sum(x['bytes'] for x in data.itervalues())/(len(data.keys()) or 1), # avg_bytes_all
                                 data[200]['bytes'] / (data[200]['count'] or 1) # avg_bytes_2xx
                                 ])


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
    stats = make_stats(records, args)
    with NamedTemporaryFile(mode="w+") as csv_stream:
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


if __name__ == '__main__':
    main()
