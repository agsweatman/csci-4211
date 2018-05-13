#!/bin/bash

mkdir -p project1

cp *.py *.txt project1

tar czvf project1.tar.gz project1

rm -rf project1
