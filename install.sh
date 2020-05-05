apt-get install -y python-requests
mkdir /app/data
chmod 775 /app/data
echo "tmpfs           /app/data       tmpfs   nodev,nosuid,size=128M 0 0" >> /etc/fstab
mount -a