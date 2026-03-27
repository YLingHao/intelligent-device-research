#!/bin/bash
current_path=$(dirname `readlink -f $0`)
jy_exe_path=$(dirname $current_path)

conf_path=$jy_exe_path/conf
bin_path=$jy_exe_path/bin
scripts_path=$jy_exe_path/scripts

# 
chmod 755 $bin_path/*
chmod 755 $scripts_path/*

echo $conf_path
cd /etc; ln -sf $conf_path/LinuxEcatKPAMaster.ini
cd /home; ln -sf $conf_path/deeprcs.json
