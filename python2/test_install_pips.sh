#!/bin/bash

venv=./newenv

if [[ -e $venv ]]; then
    rm -rf $venv
fi

virtualenv $venv

source $venv/bin/activate .

./install_pips.sh

exit 0
