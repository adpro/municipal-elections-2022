# Municipal Elections 2022 in Czech republic

The tool downloads open data from volby.cz for **municipal elections in Czech republic** and calculates the number of mandates for each political party at the time of the incomplete election results.

## Getting started

We need install `requests`, best way is via `Pipfile`:

```
$ pipenv install
```

And run shell to activate virtual environment:

```
$ pipenv shell
```

After that go to subfolder `municipal-elections-2022`. That's all. Now you can run python3 tool:

```
$ python main.py [-h] [--org ORG] [-p]
```

ORG is organization id for council code based on [code list of municipalities and polling divisions](https://www.volby.cz/pls/kv2022/kv31?xjazyk=CZ&xid=1). Default one is set, if you want to change org id to your municipality, call eg. `$ python main.py --org 562351`.

For help use: 

```
$python main.py -h
usage: main.py [-h] [--org ORG] [-p]

options:
  -h, --help      show this help message and exit
  --org ORG       set organization id
  -p, --previous  previous elections in 2018
```

## Limitations

- Code is made for one electoral district with several polling divisions.
- XML parsing is based on XSD for 2018 and 2022 elections only.
- Tested on Python 3.10.x only.