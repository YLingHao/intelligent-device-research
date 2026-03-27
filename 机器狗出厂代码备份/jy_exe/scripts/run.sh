#!/bin/bash
current_path=$(dirname `readlink -f $0`)
jy_exe_path=$(dirname $current_path)
echo ${jy_exe_path}
jy_exe=${jy_exe_path}/bin/jy_exe


echo performance | tee $(ls /sys/bus/cpu/devices/cpu*/cpufreq/scaling_governor)
echo 1 > /proc/irq/81/smp_affinity_list
echo 2 > /proc/irq/82/smp_affinity_list
echo 3 > /proc/irq/83/smp_affinity_list


# 清理过期日志
${jy_exe_path}/scripts/clean_expired_log.sh

# 运行程序
if [ ! -x ${jy_exe} ]; then
  chmod a+x ${jy_exe}
fi
cd ${jy_exe_path}/bin
echo ${jy_exe}
catchsegv ${jy_exe} $1 | tee ${jy_exe_path}/log/$(date +"%Y-%m-%d_%H:%M:%S").log

