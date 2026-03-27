#!/bin/bash  
sleep 6
# con-name 
CC_NAME_24G=myap24G
CC_NAME_5G=myap50G

dhcpip=192.168.2.1/26
SSID_PSK=12345678
# 5G channel 36 40 44 48 52~64 100~104  149~165
channel=36
apdevice=""

if [ -d /sys/class/net/wlan0 ];then
    apdevice=wlan0
fi

if [ -d /sys/class/net/p2p0 ];then
    apdevice=p2p0
fi

if [ $apdevice == "" ];then
    echo "no wifi device"
    exit 0
fi

id=$(cat /etc/boardinfo/sn)
SSID_50G=LHF-YZ-DEV
SSID_24G=yztest
if [ $id != "unknow" ];then
    SSID_50G=yz_$id_5G
    SSID_24G=yz_$id
fi

function create_ap_5G()
{
    nmcli radio wifi on
    iw reg set CN
    nmcli c add type wifi ifname $apdevice con-name $CC_NAME_5G autoconnect no ssid $SSID_50G
    nmcli c modify $CC_NAME_5G 802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel $channel 802-11-wireless.powersave 2 ipv4.method shared
    nmcli c modify $CC_NAME_5G 802-11-wireless-security.key-mgmt wpa-psk
    nmcli c modify $CC_NAME_5G 802-11-wireless-security.psk $SSID_PSK
    nmcli con modify $CC_NAME_5G ipv4.addresses $dhcpip
    nmcli connection up $CC_NAME_5G
}

function create_ap_24G()
{
    nmcli radio wifi on
    iw reg set CN
    nmcli c add type wifi ifname $apdevice con-name $CC_NAME_24G autoconnect no ssid $SSID_24G
    nmcli connection modify $CC_NAME_24G 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
    nmcli connection modify $CC_NAME_24G wifi-sec.key-mgmt wpa-psk
    nmcli connection modify $CC_NAME_24G wifi-sec.psk $SSID_PSK
    nmcli con modify  $CC_NAME_24G ipv4.addresses $dhcpip
    nmcli connection up $CC_NAME_24G
}

function close_ap()
{
    echo "try to close ap " 
    ret=$(nmcli c show | grep myap | awk 'NR=='1' {print$1}')
    if [ -z "$ret" ];then
        echo "no ap "
        return 0
    fi
    echo "current ap connection is $ret"
    if [ "$CC_NAME_24G" == "$ret" ] || [ "$CC_NAME_5G" == "$ret" ];then
        nmcli c delete $ret
        echo "delete ap success"
    fi
}

usage()
{
	echo "USAGE: "
	echo "./ap_start.sh start 5G    Create a 5G ap use default SSID and password"
    echo "./ap_start.sh start 24G   Create a 2.4G ap use default SSID and password"
    echo "./ap_start.sh stop        Close the created ap "
    exit 1
}

case $1 in 
    start)
        echo "start $2 ap"
        close_ap
        if [ -z $2 ];then 
            usage
        fi
        if [ $2 == "5G" ];then
            create_ap_5G
        fi
        if [ $2 == "24G" ];then
            create_ap_24G
        fi
        ;;
    stop)
        close_ap
        ;;
    *)
        usage
        ;;
esac
