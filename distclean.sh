#!/bin/bash

OPENPLC_DIR="$(dirname "$(readlink -f "$0")")"

git checkout -- ${OPENPLC_DIR}/editor/arduino/ ${OPENPLC_DIR}/matiec/
git clean -fdx ${OPENPLC_DIR}/matiec/ ${OPENPLC_DIR}/editor/arduino
rm -f ${OPENPLC_DIR}/openplc_editor.sh
