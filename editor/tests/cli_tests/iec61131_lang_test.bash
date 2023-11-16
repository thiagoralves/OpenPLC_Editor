#!/bin/bash

# Run IEC61131 language test through command line, and check for success in output

coproc setsid $BEREMIZPYTHONPATH $BEREMIZPATH/Beremiz_cli.py -k --project-home $BEREMIZPATH/tests/projects/iec61131_lang_test build transfer run;

while read -t 5 -u ${COPROC[0]} line; do 
    echo "$line"
    if [[ "$line" == *ALL\ TESTS\ OK* ]]; then
        pkill -9 -s $COPROC_PID 
        exit 0
    fi
done

exit 42
