#!/bin/bash

mkdir project1
cp DNSClientV3.py DNSServerV3.py readme.txt session.txt project1
tar czf project1.tar.gz project1
rm -rf project1