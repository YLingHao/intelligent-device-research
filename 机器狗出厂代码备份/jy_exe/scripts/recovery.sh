#!/bin/bash
if [ ! -h /home/ysc/jy_exe/bin/jy_exe ]
then 
	cp /home/ysc/jy_exe/bin/jy_exe /home/ysc/jy_exe/bin/jy_exe.test_main_bak
else
	echo bash: jy_exe is a soft link
fi
ln -sf ./../../bin/backup/libdeepras.so /home/ysc/jy_exe/lib/ras_lib/libdeepras.so
ln -sf backup/jy_exe /home/ysc/jy_exe/bin/jy_exe
echo 'deploy over .'
