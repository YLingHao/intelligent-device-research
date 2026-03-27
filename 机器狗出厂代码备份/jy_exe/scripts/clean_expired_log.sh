#!/bin/bash
base_path=$(dirname `readlink -f $0`)
jy_exe_path=$(dirname $base_path)
jy_exe_log_path=$jy_exe_path/log
jy_exe_data_path=$jy_exe_path/data

expired_data=10

find $jy_exe_log_path  -mtime +$expired_data -name "*.log" -exec rm -rf {} \;
find $jy_exe_data_path -mtime +$expired_data -name "*.csv" -exec rm -rf {} \;
find $jy_exe_data_path -mtime +$expired_data -name "*.gz"  -exec rm -rf {} \;

jy_exe_data_path=/home
find $jy_exe_data_path -maxdepth 1 -mtime +$expired_data -name "*.csv" -exec rm -rf {} \;
find $jy_exe_data_path -maxdepth 1 -mtime +$expired_data -name "*.gz"  -exec rm -rf {} \;
