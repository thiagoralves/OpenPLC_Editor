#! gmake

# beremiz/tests/Makefile :
#
#   Makefile to prepare and run Beremiz tests.
#
#   For developper to:
#       - quickly run a test (TDD) on current code 
#       - write new tests, debug existing tests 
#
#     Use cases :
#
#       run given tests
#           $ make run_python_exemple.sikuli
#
#       run tests from particular test classes
#           $ make ide_tests
#
#       run one particular test in a Xnest window
#           $ make xnest_run_python_exemple.sikuli
#
#       run Xnest window with just xterm
#           $ make xnest_xterm
#
#       run Xnest window with sikuli IDE and xterm
#           $ make xnest_sikuli
#
#       build minimal beremiz and matiec to run tests
#           $ make built_apps
#
#   For CI/CD scripts to catch and report all failures. Use cases :
#
#       run all tests
#           $ make
#
#   
#   Test results, and other test byproducts are in $(test_dir), 
#   $(test_dir) defaults to $(HOME)/test and can be overloaded:
#       $ make test_dir=${HOME}/other_test_dir
#
#   Makefile attemps to use xvfb-run to run each test individually with its own
#   X server instance. This behavior can be overloaded
#       $ DISPLAY=:42 make xserver_command='echo "Using $DISPLAY X Server !";'
#
#   Matiec and Beremiz code are expected to be clean, ready to build
#   Any change in Matiec directory triggers rebuild of matiec.
#   Any change in Matiec and Beremiz directory triggers copy of source code
#   to $(test_dir)/build.
#
#   BEREMIZPYTHONPATH is expected to be absolute path to python interpreter
#
#   Please note:
#       In order to run asside a freshly build Matiec, tested beremiz instance
#       needs to run on code from $(test_dir)/build/beremiz, a fresh copy
#       of the Beremiz directory $(src)/beremiz, where we run tests from.
#   

all: source_check cli_tests ide_tests runtime_tests 

# Variable $(src) is directory such that executed 
# $(src)/Makefile is this file.
src := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# $(workspace) is directory containing this project
workspace ?= $(abspath $(src)/../..)

test_dir ?= $(HOME)/test
build_dir = $(test_dir)/build

#
# SOURCE and BUILD
#

BUILT_PROJECTS=beremiz matiec open62541

tar_opts=--absolute-names --exclude=.hg --exclude=.git --exclude=.*.pyc --exclude=.*.swp

# sha1 checksum of source is used to force copy/compile on each change

define make_checksum_assign
$(1)_checksum = $(shell tar $(tar_opts) -c $(workspace)/$(1) | sha1sum | cut -d ' ' -f 1)
endef
$(foreach project,$(BUILT_PROJECTS),$(eval $(call make_checksum_assign,$(project))))

$(build_dir):
	mkdir -p $(build_dir)

define make_src_rule
$(build_dir)/$(1)/$($(1)_checksum).sha1: | $(build_dir) $(workspace)/$(1)
	rm -rf $(build_dir)/$(1)
	tar -C $(workspace) $(tar_opts) -c $(1) | tar -C $(build_dir) -x
	touch $$@
endef
$(foreach project,$(BUILT_PROJECTS),$(eval $(call make_src_rule,$(project))))

$(build_dir)/matiec/iec2c: $(build_dir)/matiec/$(matiec_checksum).sha1
	cd $(build_dir)/matiec && \
    autoreconf -i && \
    ./configure && \
    make

$(build_dir)/open62541/build/bin/libopen62541.a: $(build_dir)/open62541/$(open62541_checksum).sha1
	cd $(build_dir)/open62541 && \
    rm -rf build && mkdir build && cd build && \
	cmake -D UA_ENABLE_ENCRYPTION=OPENSSL .. && \
	make

built_apps: $(build_dir)/matiec/iec2c $(build_dir)/beremiz/$(beremiz_checksum).sha1 $(build_dir)/open62541/build/bin/libopen62541.a
	touch $@

define log_command
	$(call $(1),$(2)) | tee test_stdout.txt; exit $$$${PIPESTATUS[0]}
endef

define prep_test
	rm -rf $(test_dir)/$(1)_results
	mkdir $(test_dir)/$(1)_results
	cd $(test_dir)/$(1)_results
endef

#
# IDE TESTS
#

ide_test_dir = $(src)/ide_tests
sikuli_ide_tests = $(subst $(ide_test_dir)/,,$(wildcard $(ide_test_dir)/*.sikuli))
pytest_ide_tests = $(subst $(ide_test_dir)/,,$(wildcard $(ide_test_dir)/*.pytest))

define sikuli_idetest_command
	(fluxbox >/dev/null 2>&1 &); BEREMIZPATH=$(build_dir)/beremiz sikulix -r $(src)/ide_tests/$(1)
endef


DELAY=400
KILL_DELAY=430
PYTEST=$(dir $(BEREMIZPYTHONPATH))/pytest
define pytest_idetest_command
	(fluxbox >/dev/null 2>&1 &); PYTHONPATH=$(ide_test_dir) timeout -k $(KILL_DELAY) $(DELAY) $(PYTEST) --maxfail=1 --timeout=100  $(src)/ide_tests/$(1)
endef

# Xnest based interactive sessions for tests edit and debug. 
# Would be nice with something equivalent to xvfb-run, waiting for USR1.
# Arbitrary "sleep 1" is probably enough for interactive use
define xnest_run
	Xnest :42 -geometry 1920x1080+0+0 & export xnestpid=$$!; sleep 1; DISPLAY=:42 $(1); export res=$$?; kill $${xnestpid} 2>/dev/null; exit $${res}
endef

xserver_command ?= xvfb-run -s '-screen 0 1920x1080x24'

define make_idetest_rule
$(test_dir)/$(1)_results/.passed: built_apps
	$(call prep_test,$(1)); $(xserver_command) bash -c '$(call log_command,$(2),$(1))'
	touch $$@

# Manually invoked rule {testname}.sikuli
$(1): $(test_dir)/$(1)_results/.passed

# Manually invoked rule xnest_{testname}.sikuli
# runs test in xnest so that one can see what happens
xnest_$(1): built_apps
	$(call prep_test,$(1)); $$(call xnest_run, bash -c '$(call log_command,$(2),$(1))')

ide_tests_targets += $(test_dir)/$(1)_results/.passed
endef
$(foreach idetest,$(sikuli_ide_tests),$(eval $(call make_idetest_rule,$(idetest),sikuli_idetest_command)))
$(foreach idetest,$(pytest_ide_tests),$(eval $(call make_idetest_rule,$(idetest),pytest_idetest_command)))

ide_tests : $(ide_tests_targets)
	echo "$(ide_tests_targets) : Passed"

xnest_xterm: built_apps
	$(call xnest_run, bash -c '(fluxbox &);xterm')

xnest_sikuli: built_apps
	$(call xnest_run, bash -c '(fluxbox &);(BEREMIZPATH=$(build_dir)/beremiz xterm -e sikulix &);xterm')

xvfb_sikuli: built_apps
	echo "******************************************"
	echo "On host, run 'xvncviewer 127.0.0.1:5900' to see sikuli X session"
	echo "Docker container must be created with TESTDEBUG=YES. For example :"
	echo "./clean_docker_container.sh && ./build_docker_image.sh && TESTDEBUG=YES ./create_docker_container.sh && ./do_test_in_docker.sh xvfb_sikuli"
	echo "******************************************"
	$(xserver_command) bash -c '(fluxbox &);(x11vnc &);(BEREMIZPATH=$(build_dir)/beremiz xterm -e sikulix &);xterm'

#
# CLI TESTS
#

cli_test_dir = $(src)/cli_tests
cli_tests = $(subst $(cli_test_dir)/,,$(wildcard $(cli_test_dir)/*.bash))

define clitest_command
	BEREMIZPATH=$(build_dir)/beremiz source $(src)/cli_tests/$(1)
endef

define make_clitest_rule
$(test_dir)/$(1)_results/.passed: built_apps
	$(call prep_test,$(1)); bash -c '$(call log_command,$(2),$(1))'
	touch $$@

# Manually invoked rule
$(1): $(test_dir)/$(1)_results/.passed

cli_tests_targets += $(test_dir)/$(1)_results/.passed
endef
$(foreach clitest,$(cli_tests),$(eval $(call make_clitest_rule,$(clitest),clitest_command)))

cli_tests: $(cli_tests_targets)
	echo "$(cli_tests_targets) : Passed"

clean_results:
	rm -rf $(test_dir)/*_results

clean: clean_results
	rm -rf $(build_dir)


# TODOs 

source_check:
	echo TODO $@

runtime_tests:
	echo TODO $@



