## Rclone Commands

**Show Current Config**

```
rclone config show bt-n8n-mount
```

**Mount Remote fs**

```
rclone mount 'bt-n8n-mount:/home/brokertricks-app/htdocs/app.brokertricks.com/n8n-mount/property-image-compositor' X: --vfs-cache-mode full --vfs-cache-max-size 10G --vfs-read-chunk-size 64M --buffer-size 32M

```
  
