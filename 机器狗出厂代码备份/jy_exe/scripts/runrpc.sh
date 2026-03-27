#!/bin/bash
current_path=$(dirname `readlink -f $0`)
jy_exe_path=$(dirname $current_path)

jy_exe=${jy_exe_path}/bin/jy_exe

# run under root
echo "Please run under root(sudo)"

#path to EtherCAT libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./:${jy_exe_path}/lib/kpa_lib/linux-uspace

#make sure NICs are up

#for EtherCAt Studio connection: e.g.
#ifconfig eth0 192.168.0.1 netmask 255.255.255.0 up

#for EtherCAT primary NIC: e.g.
#ifconfig eth1 192.168.1.1 netmask 255.255.255.0 up

#for EtherCAT redundancy NIC (optional), e.g.
#ifconfig eth2 192.168.2.1 netmask 255.255.255.0 up


#start resource manager. it needs lo interface, so start it first
ip link set lo up
${jy_exe_path}/bin/ecatrsmngr verbose=0 && sleep 1

#use ./ecatmrpcserver to see command line arguments
#start RPC server using master.xml as ENI (EtherCAT Network Information)

#gdbserver :1234
${jy_exe_path}/bin/ecatmrpcserver  mode=usermode  configfile=../conf/master.xml  netadapter=enp2s0 cycletime=250  subcycletime=5000

# with redundancy
#./ecatmrpcserver  mode=usermode  configfile=../config/master.xml  netadappter=eth1  redundnetadapter=eth2  cycletime=1000  subcycletime=5000
