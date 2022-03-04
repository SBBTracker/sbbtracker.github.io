#!/usr/bin/env bash

git pull

python update.py
git add docs/
commitmsg=$(date +%F)
git commit -m $commitmsg
git push
