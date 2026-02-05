for i in sc*; do echo $i; yes | cp $i variance.png; ./variancetest.py ; done
