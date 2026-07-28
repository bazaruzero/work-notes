<!--
---
title: "Secure Patroni API"
slug: secure-patroni-api
created: 2026-07-19
updated: 2026-07-19
author: admin
categories: [postgresql, archive]
tags: [postgresql, patroni, security]
pinned: false
description: "Configuration examples on how to protect your cluster Patroni API."
---
-->

# Secure Patroni API

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Test environment](#test-environment)
- [About Patroni protection](#about-patroni-protection)
- [Case 1](#case-1)
- [Case 2](#case-2)
- [Case 3](#case-3)
- [Case 4](#case-4)
- [Case 5](#case-5)
- [Case 6](#case-6)
- [HAProxy config](#haproxy-config)
- [Appendix](#appendix)

## Docs

- [Patroni Documentation - Security Considerations - Protecting the REST API](https://patroni.readthedocs.io/en/latest/security.html)
- [Percona - Securing Patroni REST API End Points - Part 1](https://www.percona.com/blog/securing-patroni-rest-api-end-points-part-1/)
- [Percona - Securing Patroni REST API End Points Part 2: Using SSL Certificates](https://www.percona.com/blog/securing-patroni-rest-api-end-points-part-2-using-ssl-certificates/)


## Test environment

```
$ patroni --version
patroni 2.1.4
 
psql> SELECT version();
PostgreSQL 12.12 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 4.8.5 20150623 (Red Hat 4.8.5-44), 64-bit
 
$ patronictl -c /etc/patroni/postgres.yml list
+ Cluster: test_cluster (7150267844858450339) ------------------------+--------------+---------+----+-----------+
| Member                           | Host                             | Role         | State   | TL | Lag in MB |
+----------------------------------+----------------------------------+--------------+---------+----+-----------+
| srv-pg-db01.ru-central1.internal | srv-pg-db01.ru-central1.internal | Leader       | running | 69 |           |
| srv-pg-db02.ru-central1.internal | srv-pg-db02.ru-central1.internal | Sync Standby | running | 69 |         0 |
+----------------------------------+----------------------------------+--------------+---------+----+-----------+
 
$ ETCDCTL_API=3 etcdctl ${ETCD_SSL_ARGS_V3} endpoint status --cluster -w table
 
+-----------------------------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
|                   ENDPOINT                    |        ID        | VERSION | DB SIZE | IS LEADER | IS LEARNER | RAFT TERM | RAFT INDEX | RAFT APPLIED INDEX | ERRORS |
+-----------------------------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
| https://srv-pg-db01.ru-central1.internal:2379 | 9bf7cf2d10f76057 |   3.5.5 |   20 kB |      true |      false |        43 |     910910 |             910910 |        |
| https://srv-pg-db02.ru-central1.internal:2379 | a903aa5dd5b48d20 |   3.5.5 |   20 kB |     false |      false |        43 |     910910 |             910910 |        |
|  https://srv-pg-arb.ru-central1.internal:2379 | f4188b4c8dacdebb |   3.5.5 |   20 kB |     false |      false |        43 |     910911 |             910911 |        |
+-----------------------------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
```


## About Patroni protection

The Patroni REST API is used by Patroni itself during the leader race, by the patronictl tool in order to perform failovers/switchovers/reinitialize/restarts/reloads, by HAProxy or any other kind of load balancer to perform HTTP health checks, and of course could also be used for monitoring.

From the point of view of security, REST API contains safe (GET requests, only retrieve information) and unsafe (PUT, POST, PATCH and DELETE requests, change the state of nodes) endpoints.

The unsafe endpoints can be protected with HTTP basic-auth by setting the restapi.authentication.username and restapi.authentication.password parameters.

There is no way to protect the safe endpoints without enabling TLS.


## Case 1

There is no any protection of Safe/Unsafe endpoints.

Patroni config file **restapi** section example:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
```


## Case 2

Only Unsafe endpoints are protected by username/password parameters.

Patroni config file **restapi** section example:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
    authentication:
        username: patroni_api_usr
        password: Som3P@ssw0rd!23
```


## Case 3

Unsafe endpoints still protected by username/password parameters.

Enable SSL between Patroni API server and clients in order to make requests for Safe endpoints more secure.

Patroni config file **restapi** section example:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
    authentication:
        username: patroni_api_usr
        password: Som3P@ssw0rd!23
    certfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt
    keyfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.key
    cafile: /home/postgres/ssl/root.crt
```

Request examples:

```
$ curl -X GET http://$(hostname -f):8008/cluster | jq .
+++++
curl: (56) Recv failure: Connection reset by peer
+++++
 
$ curl -k -X GET https://$(hostname -f):8008/cluster | jq .
+++++
{
  "members": [
    {
      "name": "srv-pg-db01.ru-central1.internal",
      "role": "leader",
      "state": "running",
      "api_url": "https://srv-pg-db01.ru-central1.internal:8008/patroni",
      "host": "srv-pg-db01.ru-central1.internal",
      "port": 5432,
      "timeline": 70
    },
    {
      "name": "srv-pg-db02.ru-central1.internal",
      "role": "sync_standby",
      "state": "running",
      "api_url": "http://srv-pg-db02.ru-central1.internal:8008/patroni",    <--- still uses HTTP instead of HTTPS cause I'm testing only on first server
      "host": "srv-pg-db02.ru-central1.internal",
      "port": 5432,
      "timeline": 70,
      "lag": 0
    }
  ]
}
+++++
```


## Case 4

Let's add additional protection layer by adding requirement for checking client certificates for all requests to Patroni API server (safe/unsafe endpoints).

UnSafe endpoints protected by username/password, SSL and client certificates verification.

Safe endpoints protected by SSL and client certificates verification.

Patroni config file **restapi** section example:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
    authentication:
        username: patroni_api_usr
        password: Som3P@ssw0rd!23
    certfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt
    keyfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.key
    cafile: /home/postgres/ssl/root.crt
    verify_client: required
```

Request examples:

```
$ curl -k -X GET https://$(hostname -f):8008/cluster | jq .
+++++
curl: (35) NSS: client certificate not found (nickname not specified)
+++++
 
$ curl -k https://$(hostname -f):8008/cluster  --cacert /home/postgres/ssl/root.crt --cert /home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt --key /home/postgres/ssl/srv-pg-db01.ru-central1.internal.key  | jq .
+++++
{
  "members": [
    {
      "name": "srv-pg-db01.ru-central1.internal",
      "role": "leader",
      "state": "running",
      "api_url": "https://srv-pg-db01.ru-central1.internal:8008/patroni",
      "host": "srv-pg-db01.ru-central1.internal",
      "port": 5432
    },
    {
      "name": "srv-pg-db02.ru-central1.internal",
      "role": "sync_standby",
      "state": "running",
      "api_url": "http://srv-pg-db02.ru-central1.internal:8008/patroni",
      "host": "srv-pg-db02.ru-central1.internal",
      "port": 5432,
      "timeline": 70,
      "lag": 0
    }
  ]
}
+++++
```

> **NOTE:** looks like Patroni API server only checks if user certificate is signed by the same or any other trusted CA. There is no check if CN in user certificate is equal to username parameter defined in Patroni config restapi section.


## Case 5

Let's add another protection layer for UnSafe endpoints by adding `allowlist_include_members` parameter.

```
allowlist_include_members: (optional): 
If set to true it allows accessing unsafe REST API endpoints from other cluster members registered in DCS (IP address or hostname is taken from the members api_url). Be careful, it might happen that OS will use a different IP for outgoing connections.
```

Patroni config file **restapi** section example:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
    authentication:
        username: patroni_api_usr
        password: Som3P@ssw0rd!23
    certfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt
    keyfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.key
    cafile: /home/postgres/ssl/root.crt
    verify_client: required
    allowlist_include_members: true
```

Request example from another server which is not a part of database Patroni cluster:

```
$ curl -k -u patroni_api_usr:Som3P@ssw0rd!23 -X POST https://srv-pg-db01.ru-central1.internal:8008/reload --cacert /etc/etcd/ssl/root.crt --cert /etc/etcd/ssl/srv-pg-db01.ru-central1.internal.crt --key /etc/etcd/ssl/srv-pg-db01.ru-central1.internal.key
+++++
Access is denied
+++++
```


## Case 6

Add **ctl** section to avoid Python Warnings when using patronictl:

```
restapi:
    listen: 0.0.0.0:8008
    connect_address: srv-pg-db01.ru-central1.internal:8008
    authentication:
        username: patroni_api_usr
        password: Som3P@ssw0rd!23
    certfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt
    keyfile: /home/postgres/ssl/srv-pg-db01.ru-central1.internal.key
    cafile: /home/postgres/ssl/root.crt
    verify_client: required
    allowlist_include_members: true
 
ctl:
    insecure: false
```

Warning examples when ctl section is not defined and has default insecure parameter value set to true:

```
$ patronictl -c /etc/patroni/postgres.yml reload --force test_cluster
 
+ Cluster: test_cluster (7150267844858450339) ------------------------+--------------+---------+----+-----------+
| Member                           | Host                             | Role         | State   | TL | Lag in MB |
+----------------------------------+----------------------------------+--------------+---------+----+-----------+
| srv-pg-db01.ru-central1.internal | srv-pg-db01.ru-central1.internal | Leader       | running | 76 |           |
| srv-pg-db02.ru-central1.internal | srv-pg-db02.ru-central1.internal | Sync Standby | running | 76 |         0 |
+----------------------------------+----------------------------------+--------------+---------+----+-----------+
2023-06-07 15:18:37,837 - WARNING - /usr/lib/python3.6/site-packages/urllib3/connectionpool.py:1004: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
  InsecureRequestWarning,
Reload request received for member srv-pg-db02.ru-central1.internal and will be processed within 10 seconds
2023-06-07 15:18:37,858 - WARNING - /usr/lib/python3.6/site-packages/urllib3/connectionpool.py:1004: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
  InsecureRequestWarning,
Reload request received for member srv-pg-db01.ru-central1.internal and will be processed within 10 seconds
```


## HAProxy config

Here is a part of HAProxy config before enabling Patroni API protection:

```
backend pgsql_back_master
    mode                    tcp
    option                  httpchk OPTIONS /master
    http-check              expect status 200
    default-server          inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server                  srv-pg-db01.ru-central1.internal srv-pg-db01.ru-central1.internal:5432 maxconn 195 check port 8008
    server                  srv-pg-db02.ru-central1.internal srv-pg-db02.ru-central1.internal:5432 maxconn 195 check port 8008
```

After enabling Patroni API protection we will get below errors in HAProxy log:

```
Jun 07 15:41:32 srv-pg-db01.ru-central1.internal haproxy[25054]: [WARNING]  (25057) : Server pgsql_back_master/srv-pg-db01.ru-central1.internal is DOWN, reason: Socket error, info: "Connection reset by peer", check duration: 0ms. 1 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
Jun 07 15:41:33 srv-pg-db01.ru-central1.internal haproxy[25054]: [WARNING]  (25057) : Server pgsql_back_master/srv-pg-db02.ru-central1.internal is DOWN, reason: Socket error, info: "Connection reset by peer", check duration: 7ms. 0 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
Jun 07 15:41:33 srv-pg-db01.ru-central1.internal haproxy[25054]: [NOTICE]   (25057) : haproxy version is 2.4.7-b5e51a5
Jun 07 15:41:33 srv-pg-db01.ru-central1.internal haproxy[25054]: [NOTICE]   (25057) : path to executable is /usr/sbin/haproxy
Jun 07 15:41:33 srv-pg-db01.ru-central1.internal haproxy[25054]: [ALERT]    (25057) : backend 'pgsql_back_master' has no server available!
Message from syslogd@localhost at Jun  7 15:41:33 ...
 haproxy[25057]: backend pgsql_back_master has no server available!
Jun 07 15:41:34 srv-pg-db01.ru-central1.internal haproxy[25054]: [WARNING]  (25057) : Server pgsql_back_replica/srv-pg-db01.ru-central1.internal is DOWN, reason: Socket error, info: "Connection reset by peer", check duration: 1ms. 1 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
Message from syslogd@localhost at Jun  7 15:41:34 ...
 haproxy[25057]: backend pgsql_back_replica has no server available!
Jun 07 15:41:34 srv-pg-db01.ru-central1.internal haproxy[25054]: [WARNING]  (25057) : Server pgsql_back_replica/srv-pg-db02.ru-central1.internal is DOWN, reason: Socket error, info: "Connection reset by peer", check duration: 7ms. 0 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
Jun 07 15:41:34 srv-pg-db01.ru-central1.internal haproxy[25054]: [ALERT]    (25057) : backend 'pgsql_back_replica' has no server available!
```

We need to take some HAPorxy config corrections, but first we have to take below "trick" with our certs:

```
$ cat ~/ssl/srv-pg-db01.ru-central1.internal.crt ~/ssl/srv-pg-db01.ru-central1.internal.key > ~/ssl/haproxy-srv-pg-db01.ru-central1.internal.pem
 
$ cat ~/ssl/srv-pg-db02.ru-central1.internal.crt ~/ssl/srv-pg-db02.ru-central1.internal.key > ~/ssl/haproxy-srv-pg-db02.ru-central1.internal.pem
```

This is required, because otherwise we will face will another HAProxy errors:

```
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal systemd[1]: Starting HAProxy Load Balancer...
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal systemd[1]: Started HAProxy Load Balancer.
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [NOTICE]   (28014) : haproxy version is 2.4.7-b5e51a5
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [NOTICE]   (28014) : path to executable is /usr/sbin/haproxy
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : parsing [/etc/haproxy/haproxy.cfg:49] : 'server srv-pg-db01.ru-central1.internal' : No Private Key found in '/home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt.key'..
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : parsing [/etc/haproxy/haproxy.cfg:50] : 'server srv-pg-db02.ru-central1.internal' : No Private Key found in '/home/postgres/ssl/srv-pg-db02.ru-central1.internal.crt.key'..
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : parsing [/etc/haproxy/haproxy.cfg:58] : 'server srv-pg-db01.ru-central1.internal' : No Private Key found in '/home/postgres/ssl/srv-pg-db01.ru-central1.internal.crt.key'..
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : parsing [/etc/haproxy/haproxy.cfg:59] : 'server srv-pg-db02.ru-central1.internal' : No Private Key found in '/home/postgres/ssl/srv-pg-db02.ru-central1.internal.crt.key'..
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : Error(s) found in configuration file : /etc/haproxy/haproxy.cfg
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal haproxy[28014]: [ALERT]    (28014) : Fatal errors found in configuration.
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal systemd[1]: haproxy.service: main process exited, code=exited, status=1/FAILURE
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal systemd[1]: Unit haproxy.service entered failed state.
Jun 07 16:16:45 srv-pg-db01.ru-central1.internal systemd[1]: haproxy.service failed.
```

So the final version of HAProxy config changes should looks like:

```
server                  srv-pg-db01.ru-central1.internal srv-pg-db01.ru-central1.internal:5432 maxconn 195 check check-ssl verify none port 8008 crt /home/postgres/ssl/haproxy-srv-pg-db01.ru-central1.internal.pem ca-file /home/postgres/ssl/root.crt
server                  srv-pg-db02.ru-central1.internal srv-pg-db02.ru-central1.internal:5432 maxconn 195 check check-ssl verify none port 8008 crt /home/postgres/ssl/haproxy-srv-pg-db02.ru-central1.internal.pem ca-file /home/postgres/ssl/root.crt
```

Restart HAProxy to take changes:

```
$ sudo systemctl restart haproxy
```


## Appendix

All changes performed in Patroni config file requires **only** Patroni service **reload** or sending SIGHUP to Patroni main process id (kill -HUP <pid>) if reload section is not defined in Patroni service unit file.

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
