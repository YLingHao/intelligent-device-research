sudo systemctl stop jy_exe.service
sleep 1
sudo systemctl disable jy_exe.service
sleep 1
sudo systemctl daemon-reload
