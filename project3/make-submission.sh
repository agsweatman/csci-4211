#!/bin/bash

files="q1_pseudo_code.txt ethernet_learning.py q3_topo_* q4_tree_topo*"
name="groupAB_project3"

mkdir -p $name
cp $files $name
zip -r $name $name
rm -rf $name
