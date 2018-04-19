#! /bin/sh

SCRIPT=main.py

if [ -f $SCRIPT ]
then
    echo "Python script $SCRIPT present. Executing..."
    python main.py
else
    echo "Python script $SCRIPT NOT present. Double check script and path."
fi
