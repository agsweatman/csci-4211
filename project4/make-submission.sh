#!/bin/bash

files="controller.py topology.py README.txt session.txt"
name="groupAB_project4"

mkdir -p $name
cp $files $name
zip -r $name $name
rm -rf $name
