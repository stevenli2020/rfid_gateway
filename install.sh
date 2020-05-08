apt-get install -y python-requests rng-tools
mkdir /app/data
chmod 775 /app/data
echo "tmpfs           /app/run       tmpfs   nodev,nosuid,size=128M 0 0" >> /etc/fstab
mount -a
cp /app/rfid.service /etc/systemd/system/rfid.service
systemctl enable rfid
systemctl start rfid