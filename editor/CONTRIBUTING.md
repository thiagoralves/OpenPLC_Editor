How Do I Submit A Good Pull Request?
----------------------------------

It's highly recommended to write nice and clean python code. Beremiz
project tries to follows most of PEP-8 recommendations. They are
automatically checked on every push and merge by Bitbucket pipelines.

To avoid pushing "unclean" code, i's recommended to add one of the following
commands to pre commit Mercurial hook into .hg/hgrc configuration file.

Unfortunately script can't distinguish between real commit and shelve. If you
are using shelve (or maybe some other affected commands), it's recommended to
use pre-<command> and post-<command> hooks to create flags to skip checks on
some operations.


```
[hooks]
pre-shelve.linter = touch .hg/skiphook
post-shelve.linter = rm .hg/skiphook
pretxncommit.linter = ./tests/tools/check_source.sh --only-changes
```
or the same done using Docker container, so result will be the same as
on Bitbucket pipeline.

```
[hooks]
pre-shelve.linter = touch .hg/skiphook
post-shelve.linter = rm .hg/skiphook
pretxncommit.linter = hg status -m -n -a -n -I '**.py' --change $HG_NODE > files.lst && docker run --volume=$PWD:/beremiz --workdir="/beremiz" --volume=$PWD/../CanFestival-3:/CanFestival-3 --memory=1g --entrypoint=/beremiz/tests/tools/check_source.sh skvorl/beremiz-requirements --files-to-check files.lst
```
