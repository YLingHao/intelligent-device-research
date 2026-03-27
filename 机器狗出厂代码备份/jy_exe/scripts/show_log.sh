#!/bin/bash
current_path=$(dirname `readlink -f $0`)
jy_exe_path=$(dirname $current_path)
# 获取当前日期
current_date=$(date "+%Y_%m%d")
# 定义模块名
module="deeprcs"
# 拼接字符串
log_filename="${module}.${current_date}.log"


tail -f ${jy_exe_path}/log/${current_date}/${log_filename}
#sudo journalctl -f -u jy_exe.service -n 60  -o short-precise --no-hostname
