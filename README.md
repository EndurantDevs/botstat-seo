# BotStat

BotStat is a small utility to monitor the crawl rate of your website by search engine bots. Also, it helps to detect the source of possible problems. Crawl rate is dependent on many parameters. We try to give a picture of your site productivity for different search engines: Google, Bing, Yahoo, Baidu, Yandex, Sogou, and others.

For example, according to Google's Webmaster Blog, if your website responds quickly for a while, the crawl limit goes up, meaning more connections can be used to crawl. If the site slows down or responds with server errors, the limit goes down, and Googlebot crawls less. Other search engines have similar logic in most cases.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

## Running the tests

Just run:
```bash
python setup.py test
```
Or
```bash
pytest tests/
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [ConfigArgParse](https://github.com/bw2/ConfigArgParse) - A drop-in replacement for argparse that allows options to also be set via config files and/or environment variables
* [pytest](https://docs.pytest.org/en/latest/) - Framework makes it easy to write small tests, yet scales to support complex functional testing for applications and libraries
* [apache-log-parser](https://github.com/rory/apache-log-parser) - Parses log lines from an apache log

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
