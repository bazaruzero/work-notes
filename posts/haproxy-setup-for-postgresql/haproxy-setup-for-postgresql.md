<!--
---
title: "HAProxy Setup for PostgreSQL"
slug: haproxy-setup-for-postgresql
created: 2026-07-16
updated: 2026-07-16
author: admin
categories: [postgresql, archive, miscellaneous]
tags: [haproxy, postgresql, proxy]
pinned: false
description: "Example on how to configure HAProxy for PostgreSQL."
---
-->

# HAProxy Setup for PostgreSQL

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Test environment](#test-environment)
- [Installation](#installation)
- [Configure HAProxy](#configure-haproxy)
- [Configure Rsyslog](#configure-rsyslog)
- [Create sudoers config](#create-sudoers-config)
- [Start HAProxy](#start-haproxy)
- [Log Rotation](#log-rotation)

## Docs

- [HAProxy Download](https://www.haproxy.org/download/)
- [Lua Download](https://www.lua.org/ftp/)
- [Installation instructions for HAProxy](https://github.com/haproxy/haproxy/blob/master/INSTALL)
- [The Four Essential Sections of an HAProxy Configuration](https://www.haproxy.com/blog/the-four-essential-sections-of-an-haproxy-configuration/)
- [Difference between global maxconn and server maxconn haproxy](https://stackoverflow.com/questions/8750518/difference-between-global-maxconn-and-server-maxconn-haproxy)
- [Protect Servers with HAProxy Connection Limits and Queues](https://www.haproxy.com/blog/protect-servers-with-haproxy-connection-limits-and-queues)
- [Introduction to HAProxy Logging](https://www.haproxy.com/blog/introduction-to-haproxy-logging/)
- [HAProxy SSL Termination](https://www.haproxy.com/blog/haproxy-ssl-termination/)


## Test environment

```
Provider: Yandex Cloud
RAM     : 2 GB
vCPU    : 2 (20%)
HDD     : 20 GB
OS      : CentOS Linux release 7.9.2009 (Core)
Kernel  : 3.10.0-1160.76.1.el7.x86_64
```


## Installation

Install additional packages:

```
>>> admin
 
sudo yum install gcc openssl-devel readline-devel systemd-devel make pcre-devel
 
sudo yum list installed | egrep -i 'gcc|openssl-devel|readline-devel|systemd-devel|make|pcre-devel'
```

Create additional directories:

```
>>> admin
 
sudo mkdir -p /var/lib/haproxy
sudo chmod -R 755 /var/lib/haproxy
sudo chown -R postgres:postgres /var/lib/haproxy
```

Install Lua:

```
>>> admin
 
tar -xvf ~/lua-5.4.3.tar.gz
cd ~/lua-5.4.3
sudo make INSTALL_TOP=/opt/lua-5.4.3 linux install
```

Compile HAProxy:

```
>>> admin
 
tar -xvf ~/haproxy-2.4.7.tar.gz
cd ~/haproxy-2.4.7
sudo make USE_NS=1 \
USE_TFO=1 \
USE_OPENSSL=1 \
USE_ZLIB=1 \
USE_LUA=1 \
USE_PCRE=1 \
USE_SYSTEMD=1 \
USE_LIBCRYPT=1 \
USE_THREAD=1 \
TARGET=linux-glibc \
LUA_INC=/opt/lua-5.4.3/include \
LUA_LIB=/opt/lua-5.4.3/lib 
 
sudo make PREFIX=/opt/haproxy-2.4.7 install
sudo ln -s /opt/haproxy-2.4.7/sbin/haproxy /usr/sbin/haproxy
haproxy -v
```

Create systemd config:

```
>>> admin
 
sudo view /usr/lib/systemd/system/haproxy.service
-------------------------------------------------
[Unit]
Description=HAProxy Load Balancer
After=syslog.target network.target
 
[Service]
Environment="CONFIG=/etc/haproxy/haproxy.cfg" "PIDFILE=/var/run/haproxy/haproxy.pid"
ExecStartPre=/bin/mkdir -p /var/run/haproxy
ExecStart=/usr/sbin/haproxy -Ws -f $CONFIG -p $PIDFILE
ExecReload=/bin/kill -USR2 $MAINPID
KillMode=mixed
 
[Install]
WantedBy=multi-user.target
-------------------------------------------------
 
sudo systemctl daemon-reload
```


## Configure HAProxy

**For Standalone Postgres:**

> **NOTE:** check Postgres "max_connections" and "superuser_reserved_connections" (or pgBouncer "max_client_conn" if you forward connections from HAProxy to pgBouncer) parameters and correct "maxconn" (in the Backend related section) parameter value of HAProxy config accordingly.

I have "max_connections" set to 200 and "superuser_reserved_connections" set to 5, then HAProxy config looks like below:

```
>>> admin
 
sudo mkdir -p /etc/haproxy
sudo chown -R postgres:postgres /etc/haproxy
 
>>> postgres
 
touch /etc/haproxy/haproxy.cfg && chmod 755 /etc/haproxy/haproxy.cfg
view /etc/haproxy/haproxy.cfg
-------------------------------------------------
global
    log                     127.0.0.1:514  local0
    chroot                  /var/lib/haproxy
    pidfile                 /var/run/haproxy.pid
    maxconn                 2000
    user                    postgres
    group                   postgres
    stats socket            /var/lib/haproxy/stats
    nbproc                  1
    daemon
 
 
defaults
    log                     global
    maxconn                 2000
    option                  httplog
    option                  dontlognull
    option                  http-server-close
    option                  redispatch
    retries                 3
    timeout http-keep-alive 10s
    timeout http-request    10s
    timeout connect         5s
    timeout check           5s
    timeout queue           1m
    timeout client          30m
    timeout server          30m
 
 
frontend pgsql_front
    mode                    tcp
    option                  tcplog
    bind                    *:5000
    default_backend         pgsql_back
 
 
backend pgsql_back
    mode                    tcp
    option                  tcp-check
    default-server          inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server                  srv-pg-db01.ru-central1.internal srv-pg-db01.ru-central1.internal:5432 maxconn 195 check
 
 
listen stats
    mode                    http
    bind                    *:7000
    stats                   enable
    stats uri               /
-------------------------------------------------
```


**For Patroni Cluster:**

> **NOTE:** check Postgres "max_connections" and "superuser_reserved_connections" (or pgBouncer "max_client_conn" if you forward connections from HAProxy to pgBouncer) parameters and correct "maxconn" (in the Backend related section) parameter value of HAProxy config accordingly.

I have "max_connections" set to 200 and "superuser_reserved_connections" set to 5, then HAProxy config looks like below:

```
>>> admin
 
sudo mkdir -p /etc/haproxy
sudo chown -R postgres:postgres /etc/haproxy
 
>>> postgres
 
touch /etc/haproxy/haproxy.cfg && chmod 755 /etc/haproxy/haproxy.cfg
view /etc/haproxy/haproxy.cfg
-------------------------------------------------
global
    log                     127.0.0.1:514  local0
    chroot                  /var/lib/haproxy
    pidfile                 /var/run/haproxy.pid
    maxconn                 2000
    user                    postgres
    group                   postgres
    stats socket            /var/lib/haproxy/stats
    nbproc                  1
    daemon
 
 
defaults
    log                     global
    maxconn                 2000
    option                  httplog
    option                  dontlognull
    option                  http-server-close
    option                  redispatch
    retries                 3
    timeout http-keep-alive 10s
    timeout http-request    10s
    timeout connect         5s
    timeout check           5s
    timeout queue           1m
    timeout client          30m
    timeout server          30m
 
 
frontend pgsql_front_master
    mode                    tcp
    option                  tcplog
    bind                    *:5000
    default_backend         pgsql_back_master
 
 
frontend pgsql_front_replica
    mode                    tcp
    option                  tcplog
    bind                    *:5001
    default_backend         pgsql_back_replica
 
 
backend pgsql_back_master
    mode                    tcp
    option                  httpchk OPTIONS /master
    http-check              expect status 200
    default-server          inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server                  srv-pg-db01.ru-central1.internal srv-pg-db01.ru-central1.internal:5432 maxconn 195 check port 8008
    server                  srv-pg-db02.ru-central1.internal srv-pg-db02.ru-central1.internal:5432 maxconn 195 check port 8008
 
 
backend pgsql_back_replica
    mode                    tcp
    option                  httpchk OPTIONS /replica
    http-check              expect status 200
    default-server          inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server                  srv-pg-db01.ru-central1.internal srv-pg-db01.ru-central1.internal:5432 maxconn 195 check port 8008
    server                  srv-pg-db02.ru-central1.internal srv-pg-db02.ru-central1.internal:5432 maxconn 195 check port 8008
 
 
listen stats
    mode                    http
    bind                    *:7000
    stats                   enable
    stats uri               /
-------------------------------------------------
```


## Configure Rsyslog

```
>>> admin
 
systemctl status rsyslog
sudo view /etc/rsyslog.d/haproxy.conf
-------------------------------
# Collect log with UDP
$ModLoad imudp
$UDPServerAddress 127.0.0.1
$UDPServerRun 514
 
# Creating separate log files based on the severity
$fileOwner postgres
$fileGroup postgres
local0.* /pgdata/12/logs/haproxy-traffic.log
local0.notice /pgdata/12/logs/haproxy-admin.log
-------------------------------
 
sudo systemctl restart rsyslog
```


## Create sudoers config

```
>>> admin
  
sudo visudo -f /etc/sudoers.d/haproxy
+++++
postgres ALL=(ALL) NOPASSWD: /bin/systemctl start haproxy, /bin/systemctl stop haproxy, /bin/systemctl restart haproxy, /bin/systemctl enable haproxy, /bin/systemctl disable haproxy, /bin/systemctl reload haproxy
+++++
```


## Start HAProxy

```
>>> postgres
 
sudo systemctl enable haproxy
sudo systemctl start haproxy
systemctl status haproxy -l
```


## Log Rotation

```
>>> admin
 
yum list installed | grep -i logrotate
------------------------------------------------
logrotate.x86_64                    3.8.6-19.el7                 installed
------------------------------------------------
 
grep -i include /etc/logrotate.conf
------------------------------------------------
include /etc/logrotate.d
------------------------------------------------
 
sudo view /etc/logrotate.d/haproxy.conf
------------------------------------------------
/pgdata/12/logs/haproxy*.log {
daily
rotate 7
missingok
notifempty
compress
delaycompress
create 644 postgres postgres
sharedscripts
postrotate
    systemctl reload haproxy
endscript
}
------------------------------------------------
 
sudo logrotate -d /etc/logrotate.d/haproxy.conf
```

---

<p align="center"><strong><sub>DISCLAIMER</sub></strong></p>

<p align="center">
<sub>
The information presented here is intended for informational purposes only.
The author assumes no responsibility or liability for any damages resulting
from the application of the techniques described herein. Use this content at
your own risk.
<br><br>
Always create backups and test configurations thoroughly before implementing
them in live environments.
</sub>
</p>
