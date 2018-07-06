from collections import namedtuple
from datetime import date, timedelta
from botstat.botstat import generate_start_date
from botstat.botstat import make_stats


Args = namedtuple("Args", ["date_start", "day_start"])
# Make all fields are optional with default value None
Args.__new__.__defaults__ = (None,) * len(Args._fields)


def test_generate_start_date_by_days():
    args = Args(day_start=2)
    start_date = generate_start_date(args)
    assert start_date == date.today() - timedelta(days=args.day_start)


def test_generate_start_date_by_date():
    args = Args(date_start='2018/03/21')
    start_date = generate_start_date(args)
    assert start_date == date(year=2018, month=3, day=21)


def test_generate_start_date_blank():
    args = Args()
    start_date = generate_start_date(args)
    assert start_date is None


def test_make_stats():
    header = ('time_local', 'host', 'status', 'body_bytes_sent', 'request_time', 'http_user_agent')
    rows = [('25/Jun/2018:14:06:24', 'localhost', '200', '100', '1', 'Googlebot'),
            ('25/Jun/2018:14:06:25', 'localhost', '200', '200', '2', 'Googlebot'),
            ('25/Jun/2018:14:06:26', 'localhost', '201', '300', '3', 'Googlebot'),
            ('25/Jun/2018:14:06:27', 'localhost', '301', '400', '4', 'Bingbot'),
            ('25/Jun/2018:14:06:28', 'localhost', '500', '500', '5', 'Googlebot'),
            ('26/Jun/2018:14:06:29', 'localhost', '500', '200', '6', 'Googlebot'),
            ('26/Jun/2018:14:06:29', 'localhost', '500', '200', '6', 'Some user'),
            ('26/Jun/2018:14:06:34', 'localhost', '500', '400', '7', 'Googlebot'),
            ('26/Jun/2018:14:06:35', 'localhost', '200', '500', '8', 'Googlebot'),
            ('27/Jun/2018:14:06:36', 'localhost', '300', '100', '9', 'Googlebot'),
            ('27/Jun/2018:14:06:37', 'localhost', '300', '300', '10', 'Googlebot'),
            ('27/Jun/2018:14:06:38', 'localhost', '300', '500', '11', 'Googlebot'),
            ('28/Jun/2018:14:06:34', 'vhost', '200', '100', '12', 'Googlebot')]
    records = (dict(zip(header, row)) for row in rows)
    stats = make_stats(records, Args())
    assert len(stats) == 4
    dates = [date(2018, 6, 25), date(2018, 6, 26), date(2018, 6, 27), date(2018, 6, 28)]
    assert sorted(stats.keys()) == sorted(dates)
    assert stats[date(2018, 6, 25)]['Google']['localhost'][200] == {'count': 3, 'bytes': 600, 'time': 6}
    assert stats[date(2018, 6, 25)]['Google']['localhost'][500] == {'count': 1, 'bytes': 500, 'time': 5}
    assert stats[date(2018, 6, 25)]['Bing']['localhost'][300] == {'count': 1, 'bytes': 400, 'time': 4}
    assert stats[date(2018, 6, 26)]['Google']['localhost'][500] == {'count': 2, 'bytes': 600, 'time': 13}
    assert stats[date(2018, 6, 26)]['Google']['localhost'][200] == {'count': 1, 'bytes': 500, 'time': 8}
    assert stats[date(2018, 6, 27)]['Google']['localhost'][300] == {'count': 3, 'bytes': 900, 'time': 30}
    assert stats[date(2018, 6, 28)]['Google']['vhost'][200] == {'count': 1, 'bytes': 100, 'time': 12}


def test_make_stats_empty_bytes():
    header = ('time_local', 'host', 'status', 'body_bytes_sent', 'request_time', 'http_user_agent')
    rows = [('25/Jun/2018:14:06:24', 'localhost', '200', '-', '1', 'Googlebot')]
    records = (dict(zip(header, row)) for row in rows)
    stats = make_stats(records, Args())
    assert len(stats) == 1
    assert stats[date(2018, 6, 25)]['Google']['localhost'][200] == {'count': 1, 'bytes': 0, 'time': 1}


def test_make_stats_no_request_time():
    header = ('time_local', 'host', 'status', 'http_user_agent', 'body_bytes_sent')
    rows = [('25/Jun/2018:14:06:24', 'localhost', '200', 'Googlebot', '1')]
    records = (dict(zip(header, row)) for row in rows)
    stats = make_stats(records, Args())
    assert len(stats) == 1
    assert stats[date(2018, 6, 25)]['Google']['localhost'][200] == {'count': 1, 'bytes': 1}


def test_make_stats_no_bytes():
    header = ('time_local', 'host', 'status', 'http_user_agent', 'request_time')
    rows = [('25/Jun/2018:14:06:24', 'localhost', '200', 'Googlebot', '1')]
    records = (dict(zip(header, row)) for row in rows)
    stats = make_stats(records, Args())
    assert len(stats) == 1
    assert stats[date(2018, 6, 25)]['Google']['localhost'][200] == {'count': 1, 'time': 1}


def test_make_stats_no_bytes_no_times():
    header = ('time_local', 'host', 'status', 'http_user_agent')
    rows = [('25/Jun/2018:14:06:24', 'localhost', '200', 'Googlebot')]
    records = (dict(zip(header, row)) for row in rows)
    stats = make_stats(records, Args())
    assert len(stats) == 1
    assert stats[date(2018, 6, 25)]['Google']['localhost'][200] == {'count': 1}
