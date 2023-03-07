![Github](https://img.shields.io/github/tag/essembeh/essembeh-tools.svg)
![PyPi](https://img.shields.io/pypi/v/essembeh-tools.svg)
![Python](https://img.shields.io/pypi/pyversions/essembeh-tools.svg)
![CI](https://github.com/essembeh/essembeh-tools/actions/workflows/poetry.yml/badge.svg)

# essembeh-tools

Collection of useful CLI tools.

## batxaran

`batxaran` is a _batch_ tool, to run a command _N_ times with different arguments:

- remember executions to avoid running the same command twice
- can save successful run to avoid duplicates commands over multiple run
- optional delay between commands
- optional user confirmation between commands

Example:

```sh
# build a list of urls
$ echo "https://github.com" > urls.txt
$ echo "https://github.com" >> urls.txt
$ echo "https://gitlab.com" >> urls.txt

# open the url with firefox
$ batxaran --yes --sleep 10 --retry 3 --execute 'firefox {}' urls.txt
[1/3] Execute:  firefox https://github.com
OK firefox https://github.com
[2/3] IGNORE firefox https://github.com
[3/3] Press ENTER or wait 10 seconds to execute: firefox https://gitlab.com
OK firefox https://gitlab.com
```

## daterenamer

`daterenamer` simply renames photos or videos and add a prefix with the creation date from the _exif_ metadata.

> Useful to organise photos and videos from phones.

## dispatch

`dispatch` copy files into folders if the given folder name is a prefix of the filename.

## hrenamer

`hrenamer` renames files to unique names built from _sha1_ (or any _hash_ algo).

# remoteborg

`remoteborg` allows you to run _borg_ commands from a remote host via _ssh_ as _borg_ only support _push_, this a a _pull_-like implementation.
