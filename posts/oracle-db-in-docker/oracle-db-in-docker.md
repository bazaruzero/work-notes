<!--
---
title: "Oracle Database in Docker"
slug: oracle-db-in-docker
created: 2026-07-21
updated: 2026-07-21
author: admin
categories: [oracle, miscellaneous]
tags: [oracle, docker]
pinned: false
description: "Установка Oracle Database 19c в Docker-контейнере: подготовка окружения, сборка образа, запуск контейнера и проверка работы."
---
-->

# Oracle Database in Docker

## Table of Contents

- [Docs](#docs)
- [Test environment](#test-environment)
- [Docker Install](#docker-install)
- [Download Oracle Database Software](#download-oracle-database-software)
- [Install Oracle](#install-oracle)
    - [Clone Oracle Docker Images Repo](#clone-oracle-docker-images-repo)
    - [Copy Oracle Software](#copy-oracle-software)
    - [Prepare Response Files](#prepare-response-files)
    - [Build Docker Image](#build-docker-image)
    - [Start Docker Container](#start-docker-container)
    - [Monitor Database Creation](#monitor-database-creation)
    - [Check Database Status](#check-database-status)
    - [Create Test Table](#create-test-table)
    - [Restart Docker Container](#restart-docker-container)
- [Check Access to OEM Express](#check-access-to-oem-express)
- [Useful Docker commands](#useful-docker-commands)

## Docs

- [Oracle Database container images](https://github.com/oracle/docker-images/blob/main/OracleDatabase/SingleInstance/README.md)


## Test environment

- **Model:** Lenovo ThinkPad T480
- **RAM:** 16 GB
- **CPU:** Intel® Core™ i7-8650U x 8
- **DISK:** LITEONIT LCS-256M6S 2.5 7mm 256GB
- **OS:** Ubuntu 24.04.2 LTS


## Docker Install

```
>>> admin

$ sudo apt update
$ sudo apt upgrade -y
$ sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
$ echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
$ sudo apt update
$ sudo apt install -y docker-ce docker-ce-cli containerd.io
$ sudo usermod -aG docker $USER
$ newgrp docker
$ docker --version
Docker version 28.0.4, build b8034c0
```


## Download Oracle Database Software

- [Oracle Database 19c (19.3)](https://www.oracle.com/cis/database/technologies/oracle19c-linux-downloads.html?er=228088)


## Install Oracle

### Clone Oracle Docker Images Repo

```
>>> admin

$ git clone https://github.com/oracle/docker-images.git
$ mkdir -p docker-images/OracleDatabase/SingleInstance/19.3.0
$ cd ~/docker-images/OracleDatabase/SingleInstance/dockerfiles/19.3.0
```

### Copy Oracle Software

```
>>> admin

$ cp ~/Downloads/LINUX.X64_193000_db_home.zip .
```

### Prepare Response Files

```
>>> admin

$ cd ~/docker-images/OracleDatabase/SingleInstance/dockerfiles/19.3.0

$ grep -v ^# db_inst.rsp | grep -v ^$

oracle.install.responseFileVersion=/oracle/install/rspfmt_dbinstall_response_schema_v19.0.0
oracle.install.option=INSTALL_DB_SWONLY
UNIX_GROUP_NAME=dba
INVENTORY_LOCATION=###ORACLE_BASE###/oraInventory
ORACLE_HOME=###ORACLE_HOME###
ORACLE_BASE=###ORACLE_BASE###
oracle.install.db.InstallEdition=###ORACLE_EDITION###
oracle.install.db.OSDBA_GROUP=dba
oracle.install.db.OSOPER_GROUP=dba
oracle.install.db.OSBACKUPDBA_GROUP=dba
oracle.install.db.OSDGDBA_GROUP=dba
oracle.install.db.OSKMDBA_GROUP=dba
oracle.install.db.OSRACDBA_GROUP=dba
SECURITY_UPDATES_VIA_MYORACLESUPPORT=false
DECLINE_SECURITY_UPDATES=true

$ grep -v ^# dbca.rsp.tmpl | grep -v ^$

responseFileVersion=/oracle/assistants/rspfmt_dbca_response_schema_v19.0.0
gdbName=###ORACLE_SID###
sid=###ORACLE_SID###
createAsContainerDatabase=true
numberOfPDBs=1
pdbName=###ORACLE_PDB###
pdbAdminPassword=###ORACLE_PWD###
templateName=General_Purpose.dbc
sysPassword=###ORACLE_PWD###
systemPassword=###ORACLE_PWD###
emConfiguration=DBEXPRESS
emExpressPort=5500
dbsnmpPassword=###ORACLE_PWD###
characterSet=###ORACLE_CHARACTERSET###
nationalCharacterSet=AL16UTF16
initParams=audit_trail=none,audit_sys_operations=false
automaticMemoryManagement=FALSE
totalMemory=2048
```

### Build Docker Image

```
>>> admin

$ cd ~/docker-images/OracleDatabase/SingleInstance/dockerfiles

$ ./buildContainerImage.sh -v 19.3.0 -e

  Oracle Database container image for 'ee' version 19.3.0 is ready to be extended: 
    --> oracle/database:19.3.0-ee
  Build completed in 299 seconds.

$ docker images

REPOSITORY        TAG         IMAGE ID       CREATED              SIZE
oracle/database   19.3.0-ee   4ec47ae22833   About a minute ago   6.54GB
```

### Start Docker Container

```
>>> admin

$ sudo mkdir -p /opt/oracle/oradata

$ sudo chown -R 54321:54321 /opt/oracle/oradata

$ sudo chmod -R 775 /opt/oracle/oradata

$ docker run --name oracle19c \
-p 1521:1521 \
-p 5500:5500 \
-e ORACLE_PWD=password \
-v /opt/oracle/oradata:/opt/oracle/oradata \
-d oracle/database:19.3.0-ee
```

### Monitor Database Creation

```
>>> admin

$ docker logs -f oracle19c

...
#########################
DATABASE IS READY TO USE!
#########################
The following output is now a tail of the alert.log:
ORCLPDB1(3):
ORCLPDB1(3):XDB initialized.
2025-04-18T17:20:52.118877+00:00
ALTER SYSTEM SET control_files='/opt/oracle/oradata/ORCLCDB/control01.ctl' SCOPE=SPFILE;
2025-04-18T17:20:52.135672+00:00
ALTER SYSTEM SET local_listener='' SCOPE=BOTH;
   ALTER PLUGGABLE DATABASE ORCLPDB1 SAVE STATE
Completed:    ALTER PLUGGABLE DATABASE ORCLPDB1 SAVE STATE

XDB initialized.
2025-04-18T17:30:36.451306+00:00
ORCLPDB1(3):Resize operation completed for file# 10, old size 327680K, new size 337920K
2025-04-18T18:10:38.249763+00:00
Resize operation completed for file# 3, old size 522240K, new size 532480K
```

### Check Database Status

```
>>> admin

$ docker exec -it oracle19c /bin/bash

$ ps -ef | grep -i oracle

$ . oraenv  

$ sqlplus / as sysdba

sqlplus> SELECT instance_name, status FROM v$instance;

INSTANCE_NAME	 STATUS
---------------- ------------
ORCLCDB 	     OPEN
```

### Create Test Table

```
>>> admin

$ docker exec -it oracle19c /bin/bash

$ sqlplus / as sysdba

sqlplus> CREATE SEQUENCE t1_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE TABLE t1 (
    id NUMBER DEFAULT t1_id_seq.NEXTVAL PRIMARY KEY,
    date_column DATE,
    status VARCHAR2(20)
);

INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-01-15', 'YYYY-MM-DD'), 'ACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-02-20', 'YYYY-MM-DD'), 'INACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-03-10', 'YYYY-MM-DD'), 'ACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-04-05', 'YYYY-MM-DD'), 'PENDING');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-05-12', 'YYYY-MM-DD'), 'ACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-06-18', 'YYYY-MM-DD'), 'DELETED');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-07-22', 'YYYY-MM-DD'), 'ACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-08-30', 'YYYY-MM-DD'), 'INACTIVE');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-09-14', 'YYYY-MM-DD'), 'PENDING');
INSERT INTO t1 (date_column, status) VALUES (TO_DATE('2024-10-25', 'YYYY-MM-DD'), 'ACTIVE');

sqlplus> COMMIT;
```

### Restart Docker Container

To make sure after restart all data in place.

```
>>> admin

$ docker container restart oracle19c

$ docker ps -a

CONTAINER ID   IMAGE                       COMMAND                  CREATED             STATUS                            PORTS                                         NAMES
69c7b327a3fb   oracle/database:19.3.0-ee   "/bin/bash -c 'exec …"   About an hour ago   Up 8 seconds (health: starting)   0.0.0.0:1521->1521/tcp, [::]:1521->1521/tcp   oracle19c

$ docker exec -it oracle19c /bin/bash

$ sqlplus / as sysdba

SQL> select instance_name, to_char(startup_time,'mm/dd/yyyy hh24:mi:ss') as startup_time from v$instance;

SQL> select * from t1;

	ID DATE_COLU STATUS
---------- --------- --------------------
	11 15-JAN-24 ACTIVE
	12 20-FEB-24 INACTIVE
	13 10-MAR-24 ACTIVE
	14 05-APR-24 PENDING
	15 12-MAY-24 ACTIVE
	16 18-JUN-24 DELETED
	17 22-JUL-24 ACTIVE
	18 30-AUG-24 INACTIVE
	19 14-SEP-24 PENDING
	20 25-OCT-24 ACTIVE

10 rows selected.
```


## Check Access to OEM Express

The Oracle Database inside the container also has Oracle Enterprise Manager Express configured. To access OEM Express, start your browser and follow the URL:

- **URL:** https://localhost:5500/em/
- **Login:** system
- **Password:** password
- **Container name:** ORCLPDB1


## Useful Docker commands

Get list of containers:

```
$ docker ps -a
```

Get list of images:

```
$ docker images
```

Run container:

```
$ docker run oracle19c
```

Work with container:

```
$ docker stop/start/restart oracle19c
```

Container logs:

```
$ docker logs -f oracle19
```

Loging into container:

```
$ docker exec -it oracle19c /bin/bash
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
