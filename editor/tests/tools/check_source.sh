#!/bin/sh
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2017: Andrey Skvortsov
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


exit_code=0
set_exit_error()
{
    if [ $exit_code -eq 0 ]; then
       exit_code=1
    fi
}

version_gt()
{
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1";
}


compile_checks()
{
    echo "Syntax checking using python ..."
    python --version

    # remove compiled Python files
    find . -name '*.pyc' -exec rm -f {} \;

    for i in $py_files; do
        # echo $i
        python -m py_compile $i
        if [ $? -ne 0 ]; then
            echo "Syntax error in $i"
            set_exit_error
        fi
    done
    echo "DONE"
    echo ""
}


python3_compile_checks()
{
    echo "Syntax checking using python3 ..."
    python3 --version

    # remove compiled Python files
    find . -name '*.pyc' -exec rm -f {} \;

    for i in $py3_files; do
        # echo $i
        python3 -m py_compile $i
        if [ $? -ne 0 ]; then
            echo "Syntax error in $i"
            set_exit_error
        fi
    done

    # remove compiled Python files
    find . -name '*.pyc' -exec rm -f {} \;

    echo "DONE"
    echo ""
}

localization_checks()
{
    echo "Check correct localization formats"
    xgettext --version
    
    for i in $py_files; do
        xgettext -s --language=Python --package-name Beremiz --output=/tmp/m.pot $i 2>&1 | grep 'warning'
        if [ $? -eq 0 ]; then
            echo "Syntax error in $i"
            set_exit_error
        fi
    done
    echo "DONE"
    echo ""
}

# pep8 was renamed to pycodestyle
# detect existed version
pep8_detect()
{
    test -n $pep8 && (which pep8 > /dev/null) && pep8="pep8"
    test -n $pep8 && (which pycodestyle > /dev/null) && pep8="pycodestyle"
    if [ -z $pep8 ]; then
        echo "pep8/pycodestyle is not found"
        set_exit_error
    fi
    echo -n "pep8 version: "
    $pep8 --version
}

pep8_checks_default()
{
    echo "Check basic code-style problems for PEP-8"

    test -n $pep8 && pep8_detect
    test -z $pep8 && return

    user_ignore=
    user_ignore=$user_ignore,W606  # W606 'async' and 'await' are reserved keywords starting with Python 3.7

    # ignored by default,
    default_ignore=
    default_ignore=$default_ignore,E121  # E121 continuation line under-indented for hanging indent
    default_ignore=$default_ignore,E123  # E123 closing bracket does not match indentation of opening bracket’s line
    default_ignore=$default_ignore,E126  # E126 continuation line over-indented for hanging indent
    default_ignore=$default_ignore,E133  # E133 closing bracket is missing indentation
    default_ignore=$default_ignore,E226  # E226 missing whitespace around arithmetic operator
    default_ignore=$default_ignore,E241  # E241 multiple spaces after ':'
    default_ignore=$default_ignore,E242  # E242 tab after ‘,’
    default_ignore=$default_ignore,E704  # E704 multiple statements on one line (def)
    default_ignore=$default_ignore,W503  # W503 line break occurred before a binary operator
    default_ignore=$default_ignore,W504  # W504 line break occurred after a binary operator
    default_ignore=$default_ignore,W505  # W505 doc line too long (82 > 79 characters)
    ignore=$user_ignore,$default_ignore

    $pep8 --max-line-length 300 --ignore=$ignore --exclude build $py_files
    if [ $? -ne 0 ]; then
        set_exit_error
    fi

    echo "DONE"
    echo ""
}


pep8_checks_selected()
{
    echo "Check basic code-style problems for PEP-8 (selective)"

    test -n $pep8 && pep8_detect
    test -z $pep8 && return

    # select checks:
    user_select=
    user_select=$user_select,W291   # W291 trailing whitespace
    user_select=$user_select,E401   # E401 multiple imports on one line
    user_select=$user_select,E265   # E265 block comment should start with '# '
    user_select=$user_select,E228   # E228 missing whitespace around modulo operator
    user_select=$user_select,W293   # W293 blank line contains whitespace
    user_select=$user_select,E302   # E302 expected 2 blank lines, found 1
    user_select=$user_select,E301   # E301 expected 2 blank lines, found 1
    user_select=$user_select,E261   # E261 at least two spaces before inline comment
    user_select=$user_select,E271   # E271 multiple spaces after keyword
    user_select=$user_select,E231   # E231 missing whitespace after ','
    user_select=$user_select,E303   # E303 too many blank lines (2)
    user_select=$user_select,E225   # E225 missing whitespace around operator
    user_select=$user_select,E711   # E711 comparison to None should be 'if cond is not None:'
    user_select=$user_select,E251   # E251 unexpected spaces around keyword / parameter equals
    user_select=$user_select,E227   # E227 missing whitespace around bitwise or shift operator
    user_select=$user_select,E202   # E202 whitespace before ')'
    user_select=$user_select,E201   # E201 whitespace after '{'
    user_select=$user_select,W391   # W391 blank line at end of file
    user_select=$user_select,E305   # E305 expected 2 blank lines after class or function definition, found X
    user_select=$user_select,E306   # E306 expected 1 blank line before a nested definition, found X
    user_select=$user_select,E703   # E703 statement ends with a semicolon
    user_select=$user_select,E701   # E701 multiple statements on one line (colon)
    user_select=$user_select,E221   # E221 multiple spaces before operator
    user_select=$user_select,E741   # E741 ambiguous variable name 'l'
    user_select=$user_select,E111   # E111 indentation is not a multiple of four
    user_select=$user_select,E222   # E222 multiple spaces after operator
    user_select=$user_select,E712   # E712 comparison to True should be 'if cond is True:' or 'if cond:'
    user_select=$user_select,E262   # E262 inline comment should start with '# '
    user_select=$user_select,E203   # E203 whitespace before ','
    user_select=$user_select,E731   # E731 do not assign a lambda expression, use a def
    user_select=$user_select,W601   # W601 .has_key() is deprecated, use 'in'
    user_select=$user_select,E502   # E502 the backslash is redundant between brackets
    user_select=$user_select,W602   # W602 deprecated form of raising exception
    user_select=$user_select,E129   # E129 visually indented line with same indent as next logical line
    user_select=$user_select,E127   # E127 continuation line over-indented for visual indent
    user_select=$user_select,E128   # E128 continuation line under-indented for visual indent
    user_select=$user_select,E125   # E125 continuation line with same indent as next logical line
    user_select=$user_select,E114   # E114 indentation is not a multiple of four (comment)
    user_select=$user_select,E211   # E211 whitespace before '['
    user_select=$user_select,W191   # W191 indentation contains tabs
    user_select=$user_select,E101   # E101 indentation contains mixed spaces and tabs
    user_select=$user_select,E124   # E124 closing bracket does not match visual indentation
    user_select=$user_select,E272   # E272 multiple spaces before keyword
    user_select=$user_select,E713   # E713 test for membership should be 'not in'
    user_select=$user_select,E122   # E122 continuation line missing indentation or outdented
    user_select=$user_select,E131   # E131 continuation line unaligned for hanging indent
    user_select=$user_select,E721   # E721 do not compare types, use 'isinstance()'
    user_select=$user_select,E115   # E115 expected an indented block (comment)
    user_select=$user_select,E722   # E722 do not use bare except'
    user_select=$user_select,E266   # E266 too many leading '#' for block comment
    user_select=$user_select,E402   # E402 module level import not at top of file
    user_select=$user_select,W503   # W503 line break before binary operator

    $pep8 --select $user_select --exclude=build $py_files
    if [ $? -ne 0 ]; then
        set_exit_error
    fi

    echo "DONE"
    echo ""
}

flake8_checks()
{
    echo "Check for problems using flake8 ..."

    which flake8 > /dev/null
    if [ $? -ne 0 ]; then
        echo "flake8 is not found"
        set_exit_error
        return
    fi

    echo -n "flake8 version: "
    flake8 --version

    flake8 --max-line-length=300  --exclude=build --builtins="_" $py_files
    if [ $? -ne 0 ]; then
        set_exit_error
    fi

    echo "DONE"
    echo ""
}

pylint_checks()

{
    echo "Check for problems using pylint ..."

    which pylint > /dev/null
    if [ $? -ne 0 ]; then
        echo "pylint is not found"
        set_exit_error
        return
    fi
    pylint --version

    export PYTHONPATH="$PWD/../CanFestival-3/objdictgen":$PYTHONPATH

    disable=
    # These warnings most likely will not be fixed

    disable=$disable,C0103        # invalid-name
    disable=$disable,C0326        # bad whitespace
    disable=$disable,W0110        # (deprecated-lambda) map/filter on lambda could be replaced by comprehension
    disable=$disable,W0613        # (unused-argument) Unused argument 'X'
    disable=$disable,W0622        # (redefined-builtin) Redefining built-in
    disable=$disable,W0621        # (redefined-outer-name) Redefining name 'Y' from outer scope (line X)
    disable=$disable,W0122        # (exec-used) Use of exec
    disable=$disable,W0123        # (eval-used) Use of eval
    disable=$disable,I0011        # (locally-disabled) Locally disabling ungrouped-imports (C0412)
    disable=$disable,R0204        # (redefined-variable-type) Redefinition of current type from X to Y
    disable=$disable,R0201        # (no-self-use) Method could be a function
    disable=$disable,W0221        # (arguments-differ) Arguments number differs from overridden 'X' method
    disable=$disable,C0201        # (consider-iterating-dictionary) Consider iterating the dictionary directly instead of calling .keys()
    disable=$disable,W0201        # (attribute-defined-outside-init) Attribute 'X' defined outside __init__
    disable=$disable,I1101        # (c-extension-no-member) Module 'lxml.etree' has not 'X' member,
                                  # but source is unavailable. Consider adding this module to extension-pkg-whitelist
                                  # if you want to perform analysis based on run-time introspection of living objects.

    # It'd be nice to fix warnings below some day
    disable=$disable,C0111        # missing-docstring
    disable=$disable,W0703        # broad-except
    disable=$disable,C0301        # Line too long
    disable=$disable,C0302        # Too many lines in module
    disable=$disable,W0511        # fixme
    disable=$disable,R0901        # (too-many-ancestors) Too many ancestors (9/7)
    disable=$disable,R0902        # (too-many-instance-attributes) Too many instance attributes (10/7)
    disable=$disable,R0903        # (too-few-public-methods) Too few public methods (0/2)
    disable=$disable,R0904        # (too-many-public-methods) Too many public methods (41/20)
    disable=$disable,R0911        # (too-many-return-statements) Too many return statements (7/6)
    disable=$disable,R0912        # (too-many-branches) Too many branches (61/12)
    disable=$disable,R0913        # (too-many-arguments) Too many arguments (6/5)
    disable=$disable,R0914        # (too-many-locals) Too many local variables (18/15)
    disable=$disable,R0915        # (too-many-statements) Too many statements (57/50)
    disable=$disable,R0916        # (too-many-boolean-expressions) Too many boolean expressions in if statement (6/5)
    disable=$disable,R0101        # (too-many-nested-blocks) Too many nested blocks (7/5)
    disable=$disable,R0801        # (duplicate-code) Similar lines in N files
    disable=$disable,W0401        # (wildcard-import) Wildcard import 
    disable=$disable,W0614        # (unused-wildcard-import), ] Unused import X from wildcard import
    disable=$disable,W0212        # (protected-access) Access to a protected member X of a Y class
    disable=$disable,E1101        # (no-member) Instance of 'X' has no 'Y' member
    
    enable=
    enable=$enable,E1601          # print statement used
    enable=$enable,C0325          # (superfluous-parens) Unnecessary parens after keyword
    enable=$enable,W0404          # reimported module
    enable=$enable,C0411          # (wrong-import-order) standard import "import x" comes before "import y"
    enable=$enable,W0108          # (unnecessary-lambda) Lambda may not be necessary
    enable=$enable,C0412          # (ungrouped-imports) Imports from package X are not grouped
    enable=$enable,C0321          # (multiple-statements) More than one statement on a single line
    enable=$enable,W0231          # (super-init-not-called) __init__ method from base class is not called
    enable=$enable,W0105          # (pointless-string-statement) String statement has no effect
    enable=$enable,W0311          # (bad-indentation) Bad indentation. Found 16 spaces, expected 12
    enable=$enable,W0101          # (unreachable) Unreachable code
    enable=$enable,E0102          # (function-redefined) method already defined
    enable=$enable,W0602          # (global-variable-not-assigned) Using global for 'X' but no assignment is done
    enable=$enable,W0611          # (unused-import) Unused import X
    enable=$enable,C1001          # (old-style-class) Old-style class defined. Problem with PyJS
    enable=$enable,W0102          # (dangerous-default-value) Dangerous default value {} as argument
    enable=$enable,C0112          # (empty-docstring)
    enable=$enable,W0631          # (undefined-loop-variable) Using possibly undefined loop variable 'X'
    enable=$enable,W0104          # (pointless-statement) Statement seems to have no effect
    enable=$enable,W0107          # (unnecessary-pass) Unnecessary pass statement
    enable=$enable,W0406          # (import-self) Module import itself
    enable=$enable,C0413          # (wrong-import-position) Import "import X" should be placed at the top of the module
    enable=$enable,E1305          # (too-many-format-args) Too many arguments for format string
    enable=$enable,E0704          # (misplaced-bare-raise) The raise statement is not inside an except clause
    enable=$enable,C0123          # (unidiomatic-typecheck) Using type() instead of isinstance() for a typecheck.
    enable=$enable,E0601          # (used-before-assignment) Using variable 'X' before assignment
    enable=$enable,E1120          # (no-value-for-parameter) No value for argument 'X' in function call
    enable=$enable,E0701          # (bad-except-order) Bad except clauses order (X is an ancestor class of Y)
    enable=$enable,E0611          # (no-name-in-module) No name 'X' in module 'Y'
    enable=$enable,E0213          # (no-self-argument) Method should have "self" as first argument
    enable=$enable,E0401          # (import-error) Unable to import 'X'
    enable=$enable,E1121          # (too-many-function-args) Too many positional arguments for function call
    enable=$enable,W0232          # (no-init) Class has no __init__ method
    enable=$enable,W0233          # (non-parent-init-called) __init__ method from a non direct base class 'X' is called
    enable=$enable,W0601          # (global-variable-undefined) Global variable 'X' undefined at the module level
    enable=$enable,W0111          # (assign-to-new-keyword) Name async will become a keyword in Python 3.7
    enable=$enable,W0623          # (redefine-in-handler) Redefining name 'X' from outer scope (line Y) in exception handler
    enable=$enable,W0109          # (duplicate-key) Duplicate key 'X' in dictionary
    enable=$enable,E1310          # (bad-str-strip-call) Suspicious argument in str.strip call
    enable=$enable,E1300          # (bad-format-character) Unsupported format character '"' (0x22) at index 17
    enable=$enable,E1304          # (missing-format-string-key) Missing key 'X_name' in format string dictionary
    enable=$enable,R1701          # (consider-merging-isinstance) Consider merging these isinstance calls to isinstance(CTNLDFLAGS, (str, unicode))
    enable=$enable,R1704          # (redefined-argument-from-local) Redefining argument with the local name 'Y'
    enable=$enable,W0106          # (expression-not-assigned) Expression "X" is assigned to nothing
    enable=$enable,E1136          # (unsubscriptable-object) Value 'X' is unsubscriptable
    enable=$enable,E0602          # (undefined-variable) Undefined variable 'X'
    enable=$enable,W1618          # (no-absolute-import) import missing `from __future__ import absolute_import`
    enable=$enable,W0403          # (relative-import) Relative import 'Y', should be 'X.Y '
    enable=$enable,W0612          # (unused-variable) Unused variable 'X'
    enable=$enable,C0330          # (bad-continuation) Wrong hanging indentation before block
    enable=$enable,R0123          # (literal-comparison) Comparison to literal

    # python3 compatibility checks
    enable=$enable,W1648          # (bad-python3-import) Module moved in Python 3
    enable=$enable,W1613          # (xrange-builtin) xrange built-in referenced
    enable=$enable,W1612          # (unicode-builtin) unicode built-in referenced
    enable=$enable,W1619          # (old-division) division w/o __future__ statement
    enable=$enable,W1601          # (apply-builtin) apply built-in referenced
    enable=$enable,W1659          # (xreadlines-attribute) Accessing a removed xreadlines attribute
    enable=$enable,W1607          # (file-builtin) file built-in referenced
    enable=$enable,W1606          # (execfile-builtin) execfile built-in referenced
    enable=$enable,W1629          # (nonzero-method) __nonzero__ method defined
    enable=$enable,W1602          # (basestring-builtin) basestring built-in referenced
    enable=$enable,W1646          # (invalid-str-codec) non-text encoding used in str.decode
    enable=$enable,W1645          # (exception-message-attribute) Exception.message removed in Python 3
    enable=$enable,W1649          # (deprecated-string-function) Accessing a deprecated function on the string module
    enable=$enable,W1651          # (deprecated-itertools-function) Accessing a deprecated function on the itertools module
    enable=$enable,W1652          # (deprecated-types-field) Accessing a deprecated fields on the types module
    enable=$enable,W1611          # (standarderror-builtin) StandardError built-in referenced
    enable=$enable,W1624          # (indexing-exception) Indexing exceptions will not work on Python 3
    enable=$enable,W1625          # (raising-string) Raising a string exception
    enable=$enable,W1622          # (next-method-called) Called a next() method on an object
    enable=$enable,W1653          # (next-method-defined) next method defined
    enable=$enable,W1610          # (reduce-builtin) reduce built-in referenced
    enable=$enable,W1633          # (round-builtin) round built-in referenced
    # enable=

    options=

    ver=$(pylint --version 2>&1 | grep pylint  | awk '{ print $2 }')
    if version_gt $ver '1.6.8'; then
	echo "Use multiple threads for pylint"
	options="$options --jobs=0 "
    fi
    options="$options --rcfile=.pylint"
    # options="$options --py3k"   # report errors for Python 3 porting

    if [ -n "$enable" ]; then
        options="$options --disable=all"
        options="$options --enable=$enable"
    else
        options="$options --disable=$disable"
    fi
    # echo $options

    echo $py_files | xargs pylint $options
    if [ $? -ne 0 ]; then
        set_exit_error
    fi

    echo "DONE"
    echo ""
}


get_files_to_check()
{
    py_files=$(find . -name '*.py' -not -path '*/build/*')
    if [ -e .hg/skiphook ]; then
	echo "Skipping checks in the hook ..."
	exit 0
    fi
    if [ "$1" = "--only-changes" ]; then
        if which hg > /dev/null; then
            if [ ! -z "$HG_NODE" ]; then
                hg_change="--change $HG_NODE"
                msg="for commit $HG_NODE"
            else
                hg_change=""
                msg="in local repository"
            fi
            echo "Only changes ${msg} will be checked"
            echo ""
            py_files=$(hg status -m -a -n -I '**.py' $hg_change)
            if [ $? -ne 0 ]; then
                exit 1;
            fi
       fi
    fi
    if [ "$1" = "--files-to-check" ]; then
        list="$2"
        if [ -z "$list" ]; then
            echo "--files-to-check requires filename as argument"
            print_help
        fi
        if [ -e "$list" ]; then
            py_files=$(cat $2 | grep '\.py$')
        fi
    fi
    if [ -z "$py_files" ]; then
        echo "No files to check"
        exit 0;
    fi

    py3_files=$(echo $py_files | sed 's/ [[:alnum:]_\-\/.]*pyjslib.py//')
}


print_help()
{
    echo "Usage: check_source.sh [--only-changes | --files-to-check <filename> ]"
    echo ""
    echo "By default without arguments script checks all python source files"
    echo ""
    echo "--only-changes"
    echo "                only files with local changes are checked. "
    echo "                If script is called from mercurial pretxncommit hook,"
    echo "                then only commited files are checked"
    echo ""
    echo "--files-to-check <file.lst>"
    echo "                script read list of files to check from file.lst"

    exit 1
}

main()
{
    get_files_to_check $@
    python3_compile_checks
    compile_checks
    localization_checks
    pep8_checks_default
    # pep8_checks_selected

    # flake8_checks
    pylint_checks
    exit $exit_code
}

[ "$1" = "--help" -o "$1" = "-h" ] && print_help
main $@
