
#!/bin/bash

name=project2
files="program.py test_results readme.txt"

mkdir $name
cp -r $files $name
tar czf $name.tar.gz $name
rm -rf $name
