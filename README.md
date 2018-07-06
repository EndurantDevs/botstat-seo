# BotStat

BotStat is a small utility to monitor the crawl rate of your website by search engine bots. Once you run it, it sends bots crawl rate statistics in CSV format to your email.

Also, it helps to detect the source of possible problems. Crawl rate is dependent on many parameters. We try to give a picture of your site productivity for different search engines: Google, Bing, Yahoo, Baidu, Yandex, Sogou, and others.

For example, according to Google's Webmaster Blog, if your website responds quickly for a while, the crawl limit goes up, meaning more connections can be used to crawl. If the site slows down or responds with server errors, the limit goes down, and Googlebot crawls less. Other search engines have similar logic in most cases.

### Installing

It is easy to do from `pip`

```
pip install botstat-seo
```

or from sources

```
git clone git@github.com:EndurantDevs/botstat-seo.git
cd botstat-seo
python setup.py install
```

If you want to confirm that install was successful, please check for the `botstat` command line utility.

Usually this tool is used with `cron`. To go the same way, please add your configuration and configure your `crontab`.

## Running the tests

To be sure everything is fine before installation from sources, just run:
```
python setup.py test
```
Or
```
pytest tests/
```

## Usage

If you have config at ~/.botstat or /etc/botstat.conf you can just do
```
botstat
```
or if you have config on custom path
```
botstat -c /path/to/your/config 
```
or if you like to provide all params from command line
```
botstat --access-log access.log --debug --log-format '$remote_addr $host $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_time -$http_x_forwarded_for-' --smtp-port 10025 --mail-to "you@gmail.com" --mail-from "root@localhost"
```

## Help

```
$ botstat --help
usage: botstat [-h] [-c MY_CONFIG] [--verbose] [--debug]
               [--log-format LOG_FORMAT] [--nginx-config NGINX_CONFIG]
               [--access-log ACCESS_LOG] [--day-start DAY_START]
               [--date-start DATE_START] [--mail-to MAIL_TO]
               [--mail-from MAIL_FROM] [--mail-subject MAIL_SUBJECT]
               [--smtp-host SMTP_HOST] [--smtp-port SMTP_PORT]
               [--server-type {nginx,apache}]

Parse web server logs and make bots statistic Args that start with '--' (eg.
--verbose) can also be set in a config file (/etc/botstat.conf or ~/.botstat
or specified via -c). Config file syntax allows: key=value, flag=true,
stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is
specified in more than one place, then commandline values override config file
values which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c MY_CONFIG, --my-config MY_CONFIG
                        config file path
  --verbose             Verbose output
  --debug               Enable debug mode
  --log-format LOG_FORMAT
                        Web server log format like 'log_format' in nginx.conf.
                        Accept 'combined', 'common' or format string field
                        names with $
  --nginx-config NGINX_CONFIG
                        Nginx config file name with path
  --access-log ACCESS_LOG
                        Access log file name. If not specify used stdin.
  --day-start DAY_START
                        Days from the beginning of today, all older records
                        skipped
  --date-start DATE_START
                        Start date for parsing log, all older records skipped
  --mail-to MAIL_TO     Email address to send report
  --mail-from MAIL_FROM
                        'Email FROM' address
  --mail-subject MAIL_SUBJECT
                        Report email subject
  --smtp-host SMTP_HOST
                        SMTP server host name or ip adddress
  --smtp-port SMTP_PORT
                        SMTP server port
  --server-type {nginx,apache}
                        Web server type, support nginx and apache (default:
                        nginx)
```

## Built With

* [ConfigArgParse](https://github.com/bw2/ConfigArgParse) - A drop-in replacement for argparse that allows options to also be set via config files and/or environment variables
* [pytest](https://docs.pytest.org/en/latest/) - Framework makes it easy to write small tests, yet scales to support complex functional testing for applications and libraries
* [apache-log-parser](https://github.com/rory/apache-log-parser) - Parses log lines from an apache log

## Authors

 [Endurant Devs Team](https://github.com/EndurantDevs)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details