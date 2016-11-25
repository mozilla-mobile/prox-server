Install these as follows:

```
cp *.service *.timer /etc/systemd/system/
systemctl enable prox-backend.service
systemctl start prox-backend.service
systemctl enable prox-rq-backend.service
systemctl start prox-rq-backend.service
systemctl enable prox-update-gcals.timer
systemctl start prox-update-gcals.service
```

