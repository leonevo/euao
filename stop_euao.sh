#!/bin/bash
kill `ps -ef | grep "MainWeb.py"| awk -F' ' '{print $2}' | head -1`

