import sys
import logging
import argparse
import os
from config import detect_log_config
from config import build_log_format_regex
from dateutil import parser
import datetime
from collections import defaultdict
import csv
from tempfile import NamedTemporaryFile


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
    return parser.parse_args()


def make_stats(records, args):
    if args.date_start:
        date_start = parser.parse(args.date_start).date()
    elif args.day_start:
        date_start = datetime.date.today() - datetime.timedelta(days=args.day_start)
    else:
        date_start = None
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
        if date_start is not None:
            record_date = parser.parse(record['time_local'], fuzzy=True).date()
            if record_date >= date_start:
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
                writer.writerow([date.strftime('%Y/%m/%d'), bot, host,
                                 data[200]['count'], data[300]['count'], data[400]['count'], data[500]['count'],  #hits
                                 sum(x['count'] for x in data.itervalues()), # hits_all
                                 sum(x['time'] for x in data.itervalues()),  # total_time_all
                                 data[200]['time'], data[300]['time'], data[400]['time'], data[500]['time'],
                                 sum(x['bytes'] for x in data.itervalues()), # bytes_all
                                 sum(x['time'] for x in data.itervalues())/len(data.keys()), # avg_time_all
                                 data[200]['time'],# avg_time_2xx
                                 sum(x['bytes'] for x in data.itervalues())/len(data.keys()), # avg_bytes_all
                                 data[200]['bytes']# avg_bytes_2xx
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
    with NamedTemporaryFile(delete=False) as output_file:
        make_csv(stats, output_file)
        print "Result file (only for debug):", output_file.name

if __name__ == '__main__':
    main()
