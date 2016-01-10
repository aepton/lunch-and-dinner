#!/bin/sh

PROJECT='lunch-and-dinner'
ROOT=/home/ubuntu/$PROJECT
VIRTUAL_ENV=/home/ubuntu/.virtualenvs/$PROJECT
SECRETS=/home/ubuntu/secrets.sh

. $VIRTUAL_ENV/bin/activate
. $SECRETS
cd $ROOT
exec python processor.py