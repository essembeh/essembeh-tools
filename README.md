![Github](https://img.shields.io/github/tag/essembeh/essembeh-tools.svg)
![CI](https://github.com/essembeh/essembeh-tools/actions/workflows/poetry.yml/badge.svg)

# age-source

`age-source` decrypt given _age_ encypted file and run a new shell which _source_ it.

```sh
# there is no FOO in environment
$ echo $FOO

# use age-source to source an encrypted environment
$ age-source ~/test.env.age -i ~/.age/key.txt
🔐 Decrypt /home/seb/test.env.age with age -i /home/seb/.age/key.txt -d /home/seb/test.env.age
Enter passphrase for identity file "/home/seb/.age/key.txt": ***************************
$ emulate bash -c '. /tmp/tmpiht0lwf9/age.env'

# PS1 has been updated to reflect the loaded environment, FOO is now declared
(🔓 AGE:test.env.age) $ echo $FOO
bar
```

# batxaran

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

# date-renamer

`daterenamer` simply renames photos or videos and add a prefix with the creation date from the _exif_ metadata.

> Useful to organise photos and videos from phones.

# dispatch

`dispatch` copy files into folders if the given folder name is a prefix of the filename.

# ezfuse

> See [specific tool documentation](doc/ezfuse.md)

`ezfuse` is a tool handle temporary mountpoints for _Fuse_ filesystems.

# hrenamer

`hrenamer` renames files to unique names built from _sha1_ (or any _hash_ algo).

# pyfdupes

`pyfdupes` find duplicate files and remove extra copies, it uses `fdupes` internally.

# remote-borg

> See [specific tool documentation](doc/remoteborg.md)

`remote-borg` allows you to run _borg_ commands from a remote host via _ssh_ as _borg_ only support _push_, this a a _pull_-like implementation.

# virenamer

> See [specific tool documentation](doc/virenamer.md)

`virenamer` is a tool to rename files by editing their paths directly in `vi` (or in any other editor).
