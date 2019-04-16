#!/bin/sh



cleanup()
{
    find $PYTEST_DIR -name '*.pyc' -delete
}



print_help()
{
    echo "Usage: run_python_tests.sh [--on-local-xserver]"
    echo ""
    echo "--on-local-xserver"
    echo "                all tests are run on local X-server. "
    echo "                User can see test in action."
    echo "                Any interaction (mouse, keyboard) should be avoided"
    echo "                By default without arguments script runs pytest on virtual X serverf."
    echo ""

    exit 1
}

main()
{
    LC_ALL=ru_RU.utf-8
    PYTEST_DIR=./tests/tools

    if [ ! -d $PYTEST_DIR ]; then
	echo "Script should be run from top directory in repository"
	exit 1;
    fi

    use_xvfb=0
    if [ "$1" != "--on-local-xserver" ]; then
	export DISPLAY=:42
	use_xvfb=1
	Xvfb $DISPLAY -screen 0 1280x1024x24 &
	sleep 1
    fi


    cleanup

    ret=0
    DELAY=400
    KILL_DELAY=$(($DELAY + 30))
    timeout -k $KILL_DELAY $DELAY pytest --timeout=10 ./tests/tools
    ret=$?

    cleanup

    [ $use_xvfb = 1 ] && pkill -9 Xvfb
    exit $ret
}


[ "$1" = "--help" -o "$1" = "-h" ] && print_help
main $@
