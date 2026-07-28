<!--
---
title: "Oracle ADG setup with FSFO"
slug: oracle-adg-fsfo
created: 2026-07-15
updated: 2026-07-15
author: admin
categories: [oracle, archive]
tags: [oracle, data guard, replication, fsfo]
pinned: false
description: "Example on how to setup Oracle Active Data Guard with enabled Fast Start Failover option."
---
-->

# Oracle ADG setup with FSFO

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Test environment](#test-environment)
- [What is Observer?](#what-is-observer)
- [Storage setup](#storage-setup)
- [Server setup](#server-setup)
- [Oracle Software setup](#oracle-software-setup)
- [Create Primary database](#create-primary-database)
- [Patch Primary Home](#patch-primary-home)
- [Prepare Oracle Software on Standby server](#prepare-oracle-software-on-standby-server)
- [Replication setup](#replication-setup)
- [Broker setup](#broker-setup)
- [Observer setup](#observer-setup)
- [FSFO test](#fsfo-test)
- [Network Outage tests](#network-outage-tests)
    - [Commands](#commands)
    - [Max Performance](#max-performance)
        - [Test 1: Primary network outage (Max Performance)](#test-1-primary-network-outage-max-performance)
        - [Test 2: Standby network outage (Max Performance)](#test-2-standby-network-outage-max-performance)
        - [Test 3: Observer network outage (Max Performance)](#test-3-observer-network-outage-max-performance)
        - [Test 4: Data Loss (Max Performance)](#test-4-data-loss-max-performance)
    - [Max Availability](#max-availability)
        - [Switch to Max Availability mode](#switch-to-max-availability-mode)
        - [Test 1: Primary network outage (Max Availability)](#test-1-primary-network-outage-max-availability)
        - [Test 2: Standby network outage (Max Availability)](#test-2-standby-network-outage-max-availability)
        - [Test 3: Observer network outage (Max Availability)](#test-3-observer-network-outage-max-availability)
        - [Test 4: Data Loss (Max Availability)](#test-4-data-loss-max-availability)

## Docs

- [Guide to Oracle Data Guard Fast-Start Failover](https://www.oracle.com/technical-resources/articles/smiley-fsfo.html)
- [Oracle Data Guard Broker Properties](https://docs.oracle.com/database/121/DGBKR/dbpropref.htm#DGBKR745)
- [Oracle DBA Place - Setting up an Observer](https://oracledba.blogspot.com/2017/11/setting-up-observer.html)
- [Oracle DBA Place - Starting the Oracle Data Guard Broker OBSERVER in the BACKGROUND](https://oracledba.blogspot.com/2017/11/starting-oracle-data-guard-broker.html)
- [OTUS - Configure Fast Start Failover](https://otus.ru/nest/post/720/)
- Metalink:
    - Oracle 12.2 - Simplified OBSERVER Management for Multiple Fast-Start Failover Configurations (Doc ID 2285891.1)
    - Data Guard Broker - Configure Fast Start Failover, Data Protection Levels and the Data Guard Observer (Doc ID 1508729.1)
    - Oracle Data Guard FSFO Configuration with Max Availability Protection Mode (Doc ID 2385393.1)
    - 12.1 Data guard Broker(DGMGRL) Enhancements - Complete Reference (Doc ID 2010503.1)
    - ORACLE 12.2 - Starting the Oracle Data Guard Broker OBSERVER in the BACKGROUND (Doc ID 2285158.1)
    - From which server to initiate failover or switchover in an Oracle Audit Vault and Firewall in an HA configuration (Doc ID 2562943.1)


## Test environment

```
-----
Host:       yc-oracle-db1
OS:         CentOS 7 x64
vCPU:       4
RAM:        8 GB
DISK:       100 GB
  
-----
Host:       yc-oracle-db2
OS:         CentOS 7 x64
vCPU:       4
RAM:        8 GB
DISK:       100 GB
  
-----
Host:       yc-oracle-observer
OS:         CentOS 7 x64
vCPU:       2
RAM:        4 GB
DISK:       100 GB
```


## What is Observer?

The observer is the third party in an otherwise typical primary/standby Data Guard configuration. It is actually a low-footprint OCI client built into the DGMGRL CLI (Data Guard Broker Command Line Interface) and, like any other client, may be run on a different hardware platform than the database servers. Its primary job is to perform a failover when conditions permit it to do so without violating the data durability constraints set by the DBA. Only the observer can initiate FSFO failover. It's secondary job is to automatically reinstate a failed primary as a standby if that feature is enabled (the default). The observer is the key element that separates Data Guard failover from its pre-FSFO role as the plan of last resort to its leading role in a robust high availability solution.


## Storage setup

```
>>> admin@db1/db2/observer
 
$ sudo yum install -y lvm2
 
$ lsblk /dev/vdb
+++++++++++++++
NAME MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
vdb  253:16   0  100G  0 disk
+++++++++++++++
 
$ sudo pvcreate /dev/vdb
+++++++++++++++
  Physical volume "/dev/vdb" successfully created.
+++++++++++++++
 
$ sudo vgcreate oravg /dev/vdb
+++++++++++++++
  Volume group "oravg" successfully created
+++++++++++++++
 
$ sudo lvcreate --size 99.9G --name orahome oravg
+++++++++++++++
  Rounding up size to full physical extent 99.90 GiB
  Logical volume "orahome" created.
+++++++++++++++
 
$ sudo mkfs.xfs /dev/oravg/orahome
+++++++++++++++
meta-data=/dev/oravg/orahome     isize=512    agcount=4, agsize=6547200 blks
         =                       sectsz=4096  attr=2, projid32bit=1
         =                       crc=1        finobt=0, sparse=0
data     =                       bsize=4096   blocks=26188800, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal log           bsize=4096   blocks=12787, version=2
         =                       sectsz=4096  sunit=1 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
+++++++++++++++
 
$ sudo mkdir -p /u01
 
$ cat /etc/fstab | grep -i ora
+++++++++++++++
/dev/mapper/oravg-orahome   /u01       xfs   defaults 0    2
+++++++++++++++
 
$ sudo mount /u01
 
$ df -hT /u01
+++++++++++++++
Filesystem                Type  Size  Used Avail Use% Mounted on
/dev/mapper/oravg-orahome xfs   100G   33M  100G   1% /u01
+++++++++++++++
```


## Server setup

```
>>> admin@db1/db2/observer
 
$ cat /etc/hosts
+++++++++++++++
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
 
10.128.0.9     yc-oracle-db1.ru-central1.internal        yc-oracle-db1
10.128.0.16    yc-oracle-db2.ru-central1.internal        yc-oracle-db2
10.128.0.32    yc-oracle-observer.ru-central1.internal   yc-oracle-observer
+++++++++++++++
 
$ cat /etc/hostname
+++++++++++++++
yc-oracle-db1.ru-central1.internal
+++++++++++++++
yc-oracle-db2.ru-central1.internal
+++++++++++++++
yc-oracle-observer.ru-central1.internal
+++++++++++++++
 
$ sudo curl -o oracle-database-preinstall-19c-1.0-1.el7.x86_64.rpm https://yum.oracle.com/repo/OracleLinux/OL7/latest/x86_64/getPackage/oracle-database-preinstall-19c-1.0-1.el7.x86_64.rpm
 
$ sudo yum -y localinstall oracle-database-preinstall-19c-1.0-1.el7.x86_64.rpm
 
$ id oracle
+++++++++++++++
uid=54321(oracle) gid=54321(oinstall) groups=54321(oinstall),54322(dba),54323(oper),54324(backupdba),54325(dgdba),54326(kmdba),54330(racdba)
+++++++++++++++
 
$ cat /etc/selinux/config
+++++++++++++++
# This file controls the state of SELinux on the system.
# SELINUX= can take one of these three values:
#     enforcing - SELinux security policy is enforced.
#     permissive - SELinux prints warnings instead of enforcing.
#     disabled - No SELinux policy is loaded.
SELINUX=permissive
# SELINUXTYPE= can take one of three values:
#     targeted - Targeted processes are protected,
#     minimum - Modification of targeted policy. Only selected processes are protected.
#     mls - Multi Level Security protection.
SELINUXTYPE=targeted
+++++++++++++++
 
$ sudo setenforce Permissive
 
$ {
sudo mkdir -p /u01/app/oracle/product/19/dbhome_1
sudo mkdir -p /u01/app/oraInventory
sudo chown -R oracle:oinstall /u01
sudo chmod -R 755 /u01
}
```


## Oracle Software setup

```
>>> oracle@db1/db2/observer
 
$ {
mkdir -p ~/.ssh
ssh-keygen -f ~/.ssh/id_rsa -t rsa -b 4096 -N ""
touch ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 755 ~
}
 
$ cat ORCL.env
+++++++++++++++
export ORACLE_SID=ORCL
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=$ORACLE_BASE/product/19/dbhome_1
export ORACLE_HOSTNAME=$(hostname -f)
export TMP=/tmp
export TMPDIR=$TMP
export PATH=/usr/sbin:$PATH
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:/usr/sbin:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
export PS1='\[\033[0;32m\]$ORACLE_SID> \[\033[0;33m\]\u@\h\[\033[00m\] [\t] \w]\$ '
alias sp="${ORACLE_HOME}/bin/sqlplus / as sysdba"
+++++++++++++++
```

Copy installation archive to the server and start `runInstaller` script.

```
>>> admin@db1/db2/observer
 
$ source ORCL.env
 
$ unzip /home/oracle/LINUX.X64_193000_db_home.zip -d ${ORACLE_HOME}/
 
$ $ORACLE_HOME/runInstaller -ignorePrereq -waitforcompletion -silent \
-responseFile ${ORACLE_HOME}/install/response/db_install.rsp \
oracle.install.option=INSTALL_DB_SWONLY \
ORACLE_HOSTNAME=${ORACLE_HOSTNAME} \
UNIX_GROUP_NAME=oinstall \
INVENTORY_LOCATION=/u01/app/oraInventory \
SELECTED_LANGUAGES=en,en_GB \
ORACLE_HOME=${ORACLE_HOME} \
ORACLE_BASE=${ORACLE_BASE} \
oracle.install.db.InstallEdition=EE \
oracle.install.db.OSDBA_GROUP=dba \
oracle.install.db.OSBACKUPDBA_GROUP=dba \
oracle.install.db.OSDGDBA_GROUP=dba \
oracle.install.db.OSKMDBA_GROUP=dba \
oracle.install.db.OSRACDBA_GROUP=dba \
SECURITY_UPDATES_VIA_MYORACLESUPPORT=false \
DECLINE_SECURITY_UPDATES=true
+++++++++++++++
[WARNING] [INS-13014] Target environment does not meet some optional requirements.
   CAUSE: Some of the optional prerequisites are not met. See logs for details. installActions2022-04-12_09-56-01AM.log
   ACTION: Identify the list of failed prerequisite checks from the log: installActions2022-04-12_09-56-01AM.log. Then either from the log file or from installation manual find the appropriate configuration to meet the prerequisites and fix it manually.
The response file for this session can be found at:
 /u01/app/oracle/product/19/dbhome_1/install/response/db_2022-04-12_09-56-01AM.rsp
 
You can find the log of this install session at:
 /tmp/InstallActions2022-04-12_09-56-01AM/installActions2022-04-12_09-56-01AM.log
 
As a root user, execute the following script(s):
        1. /u01/app/oraInventory/orainstRoot.sh
        2. /u01/app/oracle/product/19/dbhome_1/root.sh
 
Execute /u01/app/oraInventory/orainstRoot.sh on the following nodes:
[yc-oracle-db1]
Execute /u01/app/oracle/product/19/dbhome_1/root.sh on the following nodes:
[yc-oracle-db1]
 
Successfully Setup Software with warning(s).
Moved the install session logs to:
 /u01/app/oraInventory/logs/InstallActions2022-04-12_09-56-01AM
+++++++++++++++
 
$ sudo /u01/app/oraInventory/orainstRoot.sh
+++++++++++++++
Changing permissions of /u01/app/oraInventory.
Adding read,write permissions for group.
Removing read,write,execute permissions for world.
 
Changing groupname of /u01/app/oraInventory to oinstall.
The execution of the script is complete.
+++++++++++++++
 
$ sudo /u01/app/oracle/product/19/dbhome_1/root.sh
+++++++++++++++
Check /u01/app/oracle/product/19/dbhome_1/install/root_yc-oracle-db1.ru-central1.internal_2022-04-12_10-03-18-733896241.log for the output of root script
+++++++++++++++
```


## Create Primary database

```
>>> oracle@db1
 
$ mkdir -p /u01/data /u01/redo /u01/arch
 
$ cp $ORACLE_HOME/assistants/dbca/templates/General_Purpose.dbc $ORACLE_HOME/assistants/dbca/templates/General_Purpose.dbc_orig
 
$ nohup dbca -silent -createDatabase \
-templateName General_Purpose.dbc \
-gdbname ORCL \
-characterSet AL32UTF8 \
-sysPassword sysorcl \
-systemPassword sysorcl \
-createAsContainerDatabase false \
-databaseType MULTIPURPOSE \
-automaticMemoryManagement false \
-totalMemory 6144 \
-emConfiguration NONE \
-enableArchive true \
-archiveLogDest "/u01/arch" \
-ignorePreReqs > ~/dbca.log 2>&1 &
 
$ cat dbca.log
+++++++++++++++
[WARNING] [DBT-06208] The 'SYS' password entered does not conform to the Oracle recommended standards.
   CAUSE:
a. Oracle recommends that the password entered should be at least 8 characters in length, contain at least 1 uppercase character, 1 lower case character and 1 digit [0-9].
b.The password entered is a keyword that Oracle does not recommend to be used as password
   ACTION: Specify a strong password. If required refer Oracle documentation for guidelines.
[WARNING] [DBT-06208] The 'SYSTEM' password entered does not conform to the Oracle recommended standards.
   CAUSE:
a. Oracle recommends that the password entered should be at least 8 characters in length, contain at least 1 uppercase character, 1 lower case character and 1 digit [0-9].
b.The password entered is a keyword that Oracle does not recommend to be used as password
   ACTION: Specify a strong password. If required refer Oracle documentation for guidelines.
Prepare for db operation
10% complete
Copying database files
40% complete
Creating and starting Oracle instance
42% complete
46% complete
50% complete
54% complete
60% complete
Completing Database Creation
66% complete
69% complete
70% complete
Executing Post Configuration Actions
100% complete
Database creation complete. For details check the logfiles at:
 /u01/app/oracle/cfgtoollogs/dbca/ORCL.
Database Information:
Global Database Name:ORCL
System Identifier(SID):ORCL
Look at the log file "/u01/app/oracle/cfgtoollogs/dbca/ORCL/ORCL.log" for further details.
+++++++++++++++
 
$ ln -s /u01/app/oracle/diag/rdbms/orcl/ORCL/trace/alert_ORCL.log /home/oracle/alert_ORCL.log
```


## Patch Primary Home

```
>>> oracle@db1
 
$ opatch lspatches
+++++++++++++++
29585399;OCW RELEASE UPDATE 19.3.0.0.0 (29585399)
29517242;Database Release Update : 19.3.0.0.190416 (29517242)
 
OPatch succeeded.
+++++++++++++++
 
SQL> set lines 222 pages 999;
col COMMENTS format a60;
col ACTION format a11;
col VERSION format a15;
col NAMESPACE format a10;
col BUNDLE_SERIES format a10;
col ACTION_TIME format a35;
select * from registry$history
order by ACTION_TIME;
 
+++++++++++++++
ACTION_TIME                         ACTION      NAMESPACE  VERSION                 ID COMMENTS                                                     BUNDLE_SER
----------------------------------- ----------- ---------- --------------- ---------- ------------------------------------------------------------ ----------
12-APR-22 10.11.02.228394 AM        RU_APPLY    SERVER     19.0.0.0.0                 Patch applied on 19.3.0.0.0: Release_Update - 190410122720
                                    BOOTSTRAP   DATAPATCH  19                         RDBMS_19.3.0.0.0DBRU_LINUX.X64_190417
+++++++++++++++
 
// Stop database //
 
SQL> shu immediate;
 
// Upgrade OPatch version: //
 
$ opatch version
+++++++++++++++
OPatch Version: 12.2.0.1.17
 
OPatch succeeded.
+++++++++++++++
 
$ unzip ~/p6880880_190000_Linux-x86-64.zip -d $ORACLE_HOME/
 
$ opatch version
+++++++++++++++
OPatch Version: 12.2.0.1.21
 
OPatch succeeded.
+++++++++++++++
 
// Apply patch 31281355 - Database Release Update 19.8.0.0.200714 //
 
$ unzip ~/p31281355_190000_Linux-x86-64.zip
 
$ cd ~/31281355
 
$ opatch prereq CheckConflictAgainstOHWithDetail -ph ./
 
$ opatch apply
+++++++++++++++
Patch 31281355 successfully applied.
Sub-set patch [29517242] has become inactive due to the application of a super-set patch [31281355].
Please refer to Doc ID 2161861.1 for any possible further required actions.
Log file location: /u01/app/oracle/product/19/dbhome_1/cfgtoollogs/opatch/opatch2022-04-12_11-40-04AM_1.log
 
OPatch succeeded.
+++++++++++++++
 
// Apply patch 31219897 - Oracle JavaVM Component Release Update 19.8.0.0.200714 //
 
$ unzip ~/p31219897_190000_Linux-x86-64.zip
 
$ cd 31219897
 
$ opatch prereq CheckConflictAgainstOHWithDetail -ph ./
 
$ opatch apply
+++++++++++++++
Patch 31219897 successfully applied.
Log file location: /u01/app/oracle/product/19/dbhome_1/cfgtoollogs/opatch/opatch2022-04-12_11-47-51AM_1.log
 
OPatch succeeded.
+++++++++++++++
 
// Startup and run datapatch //
 
SQL> startup;
 
$ $ORACLE_HOME/OPatch/datapatch -verbose
+++++++++++++++
SQL Patching tool version 19.8.0.0.0 Production on Tue Apr 12 11:50:42 2022
Copyright (c) 2012, 2020, Oracle.  All rights reserved.
 
Log file for this invocation: /u01/app/oracle/cfgtoollogs/sqlpatch/sqlpatch_6675_2022_04_12_11_50_42/sqlpatch_invocation.log
 
Connecting to database...OK
Gathering database info...done
Bootstrapping registry and package to current versions...done
Determining current state...done
 
Current state of interim SQL patches:
Interim patch 31219897 (OJVM RELEASE UPDATE: 19.8.0.0.200714 (31219897)):
  Binary registry: Installed
  SQL registry: Not installed
 
Current state of release update SQL patches:
  Binary registry:
    19.8.0.0.0 Release_Update 200703031501: Installed
  SQL registry:
    Applied 19.3.0.0.0 Release_Update 190410122720 successfully on 12-APR-22 10.11.08.247598 AM
 
Adding patches to installation queue and performing prereq checks...done
Installation queue:
  No interim patches need to be rolled back
  Patch 31281355 (Database Release Update : 19.8.0.0.200714 (31281355)):
    Apply from 19.3.0.0.0 Release_Update 190410122720 to 19.8.0.0.0 Release_Update 200703031501
  The following interim patches will be applied:
    31219897 (OJVM RELEASE UPDATE: 19.8.0.0.200714 (31219897))
 
Installing patches...
 
Patch installation complete.  Total patches installed: 2
 
Validating logfiles...done
Patch 31281355 apply: SUCCESS
  logfile: /u01/app/oracle/cfgtoollogs/sqlpatch/31281355/23688465/31281355_apply_ORCL_2022Apr12_11_52_12.log (no errors)
Patch 31219897 apply: SUCCESS
  logfile: /u01/app/oracle/cfgtoollogs/sqlpatch/31219897/23619699/31219897_apply_ORCL_2022Apr12_11_51_21.log (no errors)
SQL Patching tool complete on Tue Apr 12 11:58:27 2022
+++++++++++++++
 
SQL> set lines 222 pages 999;
col COMMENTS format a60;
col ACTION format a11;
col VERSION format a15;
col NAMESPACE format a10;
col BUNDLE_SERIES format a10;
col ACTION_TIME format a35;
select * from registry$history
order by ACTION_TIME;
 
+++++++++++++++
ACTION_TIME                         ACTION      NAMESPACE  VERSION                 ID COMMENTS                                                     BUNDLE_SER
----------------------------------- ----------- ---------- --------------- ---------- ------------------------------------------------------------ ----------
12-APR-22 10.11.02.228394 AM        RU_APPLY    SERVER     19.0.0.0.0                 Patch applied on 19.3.0.0.0: Release_Update - 190410122720
12-APR-22 11.52.12.296471 AM        jvmpsu.sql  SERVER     19.8.0.0.200714          0 RAN jvmpsu.sql
                                                           OJVMRU
 
12-APR-22 11.52.12.315444 AM        APPLY       SERVER     19.8.0.0.200714          0 OJVM RU post-install
                                                           OJVMRU
 
12-APR-22 11.57.47.722593 AM        RU_APPLY    SERVER     19.0.0.0.0                 Patch applied from 19.3.0.0.0 to 19.8.0.0.0: Release_Update
                                                                                      - 200703031501
 
                                    BOOTSTRAP   DATAPATCH  19                         RDBMS_19.8.0.0.0DBRU_LINUX.X64_200702
+++++++++++++++
 
$ opatch lspatches
+++++++++++++++
31219897;OJVM RELEASE UPDATE: 19.8.0.0.200714 (31219897)
31281355;Database Release Update : 19.8.0.0.200714 (31281355)
29585399;OCW RELEASE UPDATE 19.3.0.0.0 (29585399)
 
OPatch succeeded.
+++++++++++++++
```


## Prepare Oracle Software on Standby server

```
>>> oracle@db01
 
$ scp -rp $ORACLE_HOME/* oracle@yc-oracle-db2:/u01/app/oracle/product/19/dbhome_1/
 
 
>>> oracle@db2
 
$ source ORCL.env
 
$ $ORACLE_HOME/runInstaller -ignorePrereq -waitforcompletion -silent \
-responseFile ${ORACLE_HOME}/install/response/db_install.rsp \
oracle.install.option=INSTALL_DB_SWONLY \
ORACLE_HOSTNAME=${ORACLE_HOSTNAME} \
UNIX_GROUP_NAME=oinstall \
INVENTORY_LOCATION=/u01/app/oraInventory \
SELECTED_LANGUAGES=en,en_GB \
ORACLE_HOME=${ORACLE_HOME} \
ORACLE_BASE=${ORACLE_BASE} \
oracle.install.db.InstallEdition=EE \
oracle.install.db.OSDBA_GROUP=dba \
oracle.install.db.OSBACKUPDBA_GROUP=dba \
oracle.install.db.OSDGDBA_GROUP=dba \
oracle.install.db.OSKMDBA_GROUP=dba \
oracle.install.db.OSRACDBA_GROUP=dba \
SECURITY_UPDATES_VIA_MYORACLESUPPORT=false \
DECLINE_SECURITY_UPDATES=true
 
>>> admin@db2
 
$ sudo /u01/app/oraInventory/orainstRoot.sh
 
$ sudo /u01/app/oracle/product/19/dbhome_1/root.sh
```


## Replication setup

```
>>> oracle@db1/db2
 
$ cat $ORACLE_HOME/network/admin/tnsnames.ora
++++++++++
ORCL =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db1.ru-central1.internal)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = ORCL)
      (INSTANCE_NAME = ORCL)
    )
  )
 
ORCL_STBY =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db2.ru-central1.internal)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = ORCL)
      (INSTANCE_NAME = ORCL)
    )
  )
++++++++++
 
>>> oracle@db1
 
$ cat $ORACLE_HOME/network/admin/listener.ora
++++++++++
LIORCL =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db1.ru-central1.internal)(PORT = 1521))
    )
  )
 
SID_LIST_LIORCL =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
   )
++++++++++
 
$ lsnrctl start LIORCL
 
$ lsnrctl status LIORCL
 
>>> oracle@db2
 
$ cat $ORACLE_HOME/network/admin/listener.ora
++++++++++
LIORCL =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db2.ru-central1.internal)(PORT = 1521))
    )
  )
 
SID_LIST_LIORCL =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
   )
++++++++++
 
$ lsnrctl start LIORCL
 
$ lsnrctl status LIORCL
 
// Put PRIMARY in ARCHIVELOG mode (already enabled): //
 
SQL> archive log list;
Database log mode              Archive Mode
Automatic archival             Enabled
Archive destination            /u01/arch
Oldest online log sequence     3
Next log sequence to archive   5
Current log sequence           5
 
// Put PRIMARY in force logging mode: //
 
SQL> select force_logging from v$database;
 
FORCE_LOGGING
---------------------------------------
NO
 
SQL> alter database force logging;
 
Database altered.
 
SQL> select force_logging from v$database;
 
FORCE_LOGGING
---------------------------------------
YES
 
// Set parameters on PRIMARY: //
 
SQL> alter system set log_archive_config='dg_config=(ORCL,ORCL_STBY)';
SQL> alter system set log_archive_dest_state_2=DEFER;
SQL> alter system set log_archive_dest_2='SERVICE=ORCL_STBY LGWR ASYNC NOAFFIRM VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) DB_UNIQUE_NAME=ORCL_STBY';
SQL> alter system set standby_file_management=AUTO;
SQL> alter system set fal_server=ORCL_STBY;
SQL> alter system set fal_client=ORCL;
 
// Create / copy password file: //
 
$ orapwd file=$ORACLE_HOME/dbs/orapwORCL password=sysorcl format=12 force=y
$ scp $ORACLE_HOME/dbs/orapwORCL oracle@yc-oracle-db2.ru-central1.internal:$ORACLE_HOME/dbs/orapwORCL
 
// Create standby redo logs on PRIMARY: //
 
SQL> alter database add standby logfile group 4 ('/u01/redo/ORCL/redo01_STBY.log') size 512M;
SQL> alter database add standby logfile group 5 ('/u01/redo/ORCL/redo02_STBY.log') size 512M;
SQL> alter database add standby logfile group 6 ('/u01/redo/ORCL/redo03_STBY.log') size 512M;
SQL> select * from v$logfile order by 1;
 
    GROUP# STATUS  TYPE    MEMBER                                                                                   IS_     CON_ID
---------- ------- ------- ---------------------------------------------------------------------------------------- --- ----------
         1         ONLINE  /u01/redo/ORCL/redo01.log                                                                NO           0
         2         ONLINE  /u01/redo/ORCL/redo02.log                                                                NO           0
         3         ONLINE  /u01/redo/ORCL/redo03.log                                                                NO           0
         4         STANDBY /u01/redo/ORCL/redo01_STBY.log                                                           NO           0
         5         STANDBY /u01/redo/ORCL/redo02_STBY.log                                                           NO           0
         6         STANDBY /u01/redo/ORCL/redo03_STBY.log                                                           NO           0
 
6 rows selected.
 
// Create parameter file for STANDBY: //
 
>>> oracle@db2
 
$ mkdir -p /u01/data /u01/redo /u01/arch /u01/app/oracle/admin/ORCL_STBY/adump
 
$ cat $ORACLE_HOME/dbs/initORCL.ora
++++++++++
db_name='ORCL'
db_unique_name='ORCL_STBY'
control_files='/u01/data/ORCL_STBY/control01.ctl','/u01/redo/ORCL_STBY/control02.ctl'
audit_file_dest='/u01/app/oracle/admin/ORCL_STBY/adump'
sga_max_size=4608M
sga_target=4608M
pga_aggregate_limit=3G
pga_aggregate_target=1536M
db_file_name_convert  = ('/u01/data/ORCL/','/u01/data/ORCL_STBY/')
log_file_name_convert  = ('/u01/redo/ORCL/','/u01/redo/ORCL_STBY/')
log_archive_config='dg_config=(ORCL,ORCL_STBY)'
log_archive_dest_1='LOCATION=/u01/arch'
log_archive_dest_2='SERVICE=ORCL LGWR ASYNC NOAFFIRM VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) DB_UNIQUE_NAME=ORCL'
log_archive_dest_state_2='DEFER'
log_archive_format='log%t_%s_%r.arc'
fal_server='ORCL'
fal_client='ORCL_STBY'
standby_file_management='AUTO'
REMOTE_LOGIN_PASSWORDFILE=EXCLUSIVE
++++++++++
 
SQL> create spfile from pfile;
 
 
// Start STANDBY instance: //
 
SQL> startup nomount;
SQL> select instance_name, status from v$instance;
 
INSTANCE_NAME    STATUS
---------------- ------------
ORCL             STARTED
 
$ ln -s /u01/app/oracle/diag/rdbms/orcl_stby/ORCL/trace/alert_ORCL.log /home/oracle/alert_ORCL.log
 
// Start RMAN duplicate: //
 
>>> oracle@db2
 
$ rman
$ connect target sys/sysorcl@ORCL
$ connect auxiliary sys/sysorcl@ORCL_STBY
 
RMAN> run {
allocate channel p1 type disk;
allocate channel p2 type disk;
allocate auxiliary channel s1 type disk;
allocate auxiliary channel s2 type disk;
duplicate target database for standby from active database dorecover nofilenamecheck;
}
 
// Start redo apply in real time mode on STANDBY: //
 
>>> oracle@db1
 
SQL> alter system set log_archive_dest_state_2='ENABLE';
 
>>> oracle@db2
 
SQL> alter database recover managed standby database cancel;
 
SQL> ALTER DATABASE OPEN READ ONLY;
 
SQL> alter database recover managed standby database disconnect from session using current logfile;
 
SQL> SET LINES 180
col DEST_NAME for a30
select DEST_ID,dest_name,status,type,srl,recovery_mode from v$archive_dest_status where dest_id=1;
++++++++++
   DEST_ID DEST_NAME                      STATUS    TYPE             SRL RECOVERY_MODE
---------- ------------------------------ --------- ---------------- --- ----------------------------------
         1 LOG_ARCHIVE_DEST_1             VALID     LOCAL            NO  MANAGED REAL TIME APPLY
++++++++++
 
SQL> select protection_mode, protection_level from v$database;
++++++++++
PROTECTION_MODE      PROTECTION_LEVEL
-------------------- --------------------
MAXIMUM PERFORMANCE  MAXIMUM PERFORMANCE
++++++++++
```


## Broker setup

```
>>> oracle@db1/db2
 
SQL> ALTER SYSTEM SET dg_broker_start=true scope=both;
 
// Register PRIMARY in broker: //
 
>>> oracle@db1
 
$ dgmgrl sys/sysorcl@ORCL
++++++++++
DGMGRL> CREATE CONFIGURATION dg_config_test1 AS PRIMARY DATABASE IS ORCL CONNECT IDENTIFIER IS ORCL;
Configuration "dg_config_test1" created with primary database "orcl"
DGMGRL>
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl - Primary database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
DISABLED
++++++++++
 
// Register STANDBY in broker: //
 
>>> oracle@db2
 
SQL> alter system set log_archive_dest_2='' scope=both;         <<<<<<<<<< Otherwise you will get an error during the registration in Broker "Error: ORA-16698: member has a LOG_ARCHIVE_DEST_n parameter with SERVICE attribute set" = Doc ID 1582179.1
 
>>> oracle@db1 !!!
 
$ dgmgrl sys/sysorcl@ORCL
++++++++++
DGMGRL> ADD DATABASE ORCL_STBY AS CONNECT IDENTIFIER IS ORCL_STBY MAINTAINED AS PHYSICAL;
Database "orcl_stby" added
 
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - Physical standby database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
DISABLED
++++++++++
 
// Enable configuration: //
 
>>> oracle@db1 !!!
 
$ dgmgrl sys/sysorcl@ORCL
++++++++++
DGMGRL> ENABLE CONFIGURATION;
Enabled.
DGMGRL>
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - Physical standby database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
SUCCESS   (status updated 13 seconds ago)
 
DGMGRL>
DGMGRL> SHOW DATABASE ORCL;
 
Database - orcl
 
  Role:               PRIMARY
  Intended State:     TRANSPORT-ON
  Instance(s):
    ORCL
 
Database Status:
SUCCESS
 
DGMGRL>
DGMGRL> SHOW DATABASE ORCL_STBY;
 
Database - orcl_stby
 
  Role:               PHYSICAL STANDBY
  Intended State:     APPLY-ON
  Transport Lag:      0 seconds (computed 1 second ago)
  Apply Lag:          0 seconds (computed 1 second ago)
  Average Apply Rate: 1.00 KByte/s
  Real Time Query:    ON
  Instance(s):
    ORCL
 
Database Status:
SUCCESS
++++++++++
 
// Prepare for Switchover: //
 
>>> oracle@db1
 
$ cat $ORACLE_HOME/network/admin/listener.ora
++++++++++
LIORCL =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db1.ru-central1.internal)(PORT = 1521))
    )
  )
 
SID_LIST_LIORCL =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL_DGMGRL)                         <<<<<<<<<< For the Broker could remotely connect to the instance and restart it (2312510.1 : GLOBAL_DBNAME = The listener tries to match the value of this parameter with the value of the SERVICE_NAME parameter in the client connect descriptor.)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
   )
++++++++++
 
 
$ lsnrctl stop LIORCL && lsnrctl start LIORCL
 
>>> oracle@db2
 
$ cat $ORACLE_HOME/network/admin/listener.ora
++++++++++
LIORCL =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = yc-oracle-db2.ru-central1.internal)(PORT = 1521))
    )
  )
 
SID_LIST_LIORCL =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
    (SID_DESC =
      (GLOBAL_DBNAME = ORCL_STBY_DGMGRL)                <<<<<<<<<< For the Broker could remotely connect to the instance and restart it (2312510.1 : GLOBAL_DBNAME = The listener tries to match the value of this parameter with the value of the SERVICE_NAME parameter in the client connect descriptor.)
      (ORACLE_HOME = /u01/app/oracle/product/19/dbhome_1)
      (SID_NAME = ORCL)
    )
   )
++++++++++
 
$ lsnrctl stop LIORCL && lsnrctl start LIORCL
 
// Test Switchover functionality: "11.2 Data Guard Physical Standby Switchover Best Practices using the Broker (Doc ID 1305019.1)" //
 
>>> oracle@db1
 
$ dgmgrl sys/sysorcl@ORCL
+++++++++++++++++++++++++++++++++++++++++
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - Physical standby database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
SUCCESS   (status updated 10 seconds ago)
 
DGMGRL> SWITCHOVER TO ORCL_STBY;
Performing switchover NOW, please wait...
Operation requires a connection to database "orcl_stby"
Connecting ...
Connected to "ORCL_STBY"
Connected as SYSDBA.
New primary database "orcl_stby" is opening...
Operation requires start up of instance "ORCL" on database "orcl"
Starting instance "ORCL"...
Connected to an idle instance.
ORACLE instance started.
Connected to "ORCL"
Database mounted.
Database opened.
Connected to "ORCL"
Switchover succeeded, new primary is "orcl_stby"
DGMGRL>
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl_stby - Primary database
    orcl      - Physical standby database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
SUCCESS   (status updated 67 seconds ago)
+++++++++++++++++++++++++++++++++++++++++
 
// And switch back
 
DGMGRL> SWITCHOVER TO ORCL;
```


## Observer setup

```
>>> oracle@observer
 
$ {
mkdir -p ~/.ssh
ssh-keygen -f ~/.ssh/id_rsa -t rsa -b 4096 -N ""
touch ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 755 ~
}
 
$ cat ORCL.env
+++++++++++++++
export ORACLE_SID=ORCL
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=$ORACLE_BASE/product/19/dbhome_1
export ORACLE_HOSTNAME=$(hostname -f)
export TMP=/tmp
export TMPDIR=$TMP
export PATH=/usr/sbin:$PATH
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:/usr/sbin:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
export PS1='\[\033[0;32m\]$ORACLE_SID> \[\033[0;33m\]\u@\h\[\033[00m\] [\t] \w]\$ '
alias sp="${ORACLE_HOME}/bin/sqlplus / as sysdba"
+++++++++++++++
 
>>> oracle@db01
 
$ scp -rp $ORACLE_HOME/* oracle@yc-oracle-observer:/u01/app/oracle/product/19/dbhome_1/
 
>>> oracle@observer
 
$ source ORCL.env
 
$ $ORACLE_HOME/runInstaller -ignorePrereq -waitforcompletion -silent \
-responseFile ${ORACLE_HOME}/install/response/db_install.rsp \
oracle.install.option=INSTALL_DB_SWONLY \
ORACLE_HOSTNAME=${ORACLE_HOSTNAME} \
UNIX_GROUP_NAME=oinstall \
INVENTORY_LOCATION=/u01/app/oraInventory \
SELECTED_LANGUAGES=en,en_GB \
ORACLE_HOME=${ORACLE_HOME} \
ORACLE_BASE=${ORACLE_BASE} \
oracle.install.db.InstallEdition=EE \
oracle.install.db.OSDBA_GROUP=dba \
oracle.install.db.OSBACKUPDBA_GROUP=dba \
oracle.install.db.OSDGDBA_GROUP=dba \
oracle.install.db.OSKMDBA_GROUP=dba \
oracle.install.db.OSRACDBA_GROUP=dba \
SECURITY_UPDATES_VIA_MYORACLESUPPORT=false \
DECLINE_SECURITY_UPDATES=true
 
>>> admin@observer
 
$ sudo /u01/app/oraInventory/orainstRoot.sh
 
$ sudo /u01/app/oracle/product/19/dbhome_1/root.sh
 
// Primary - Enable Flashback //
 
$ mkdir -p /u01/fra
 
SQL> alter system set db_recovery_file_dest_size=30G scope=both;
 
System altered.
 
SQL> alter system set db_recovery_file_dest='/u01/fra' scope=both;
 
System altered.
 
SQL> alter database flashback on;
 
Database altered.
 
SQL> select flashback_on from v$database;
 
FLASHBACK_ON
------------------
YES
 
// Standby - Enable Flashback //
 
$ mkdir -p /u01/fra
 
SQL> ALTER DATABASE RECOVER MANAGED STANDBY DATABASE CANCEL;
 
Database altered.
 
SQL> alter system set db_recovery_file_dest_size=30G scope=both;
 
System altered.
 
SQL> alter system set db_recovery_file_dest='/u01/fra' scope=both;
 
System altered.
 
SQL> alter database flashback on;
 
Database altered.
 
SQL> select flashback_on from v$database;
 
FLASHBACK_ON
------------------
YES
 
SQL> alter database recover managed standby database disconnect from session using current logfile;
 
Database altered.
 
// Primary/Standby - Update "db_lost_write_protect" //
 
SQL> alter system set db_lost_write_protect='TYPICAL' scope=both;
 
System altered.
 
// Adjust FastStartFailoverTarget between the Primary & the standby //
 
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - Physical standby database
 
Fast-Start Failover:  Disabled
 
Configuration Status:
SUCCESS   (status updated 51 seconds ago)
 
DGMGRL>
DGMGRL> edit database orcl set property FastStartFailoverTarget='orcl_stby';
Property "faststartfailovertarget" updated
DGMGRL>
DGMGRL> edit database orcl_stby set property FastStartFailoverTarget='orcl';
Property "faststartfailovertarget" updated
 
// Copy tnsnames.ora on Observer //
 
Already done during ORACLE_HOME copy.
 
// Enable FAST_START FAILOVER //
 
>>> oracle@Observer
 
$ dgmgrl sys/sysorcl@ORCL
 
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - Physical standby database
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '30'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover:  Disabled
 
Configuration Status:
SUCCESS
 
DGMGRL>
DGMGRL> SHOW FAST_START FAILOVER;
 
Fast-Start Failover:  Disabled
 
  Protection Mode:    MaxPerformance
  Lag Limit:          30 seconds
 
  Threshold:          30 seconds
  Active Target:      (none)
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-db1.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configurable Failover Conditions
  Health Conditions:
    Corrupted Controlfile          YES
    Corrupted Dictionary           YES
    Inaccessible Logfile            NO
    Stuck Archiver                  NO
    Datafile Write Errors          YES
 
  Oracle Error Conditions:
    (none)
 
DGMGRL>
DGMGRL> ENABLE FAST_START FAILOVER;
Enabled in Potential Data Loss Mode.
DGMGRL>
DGMGRL> SHOW FAST_START FAILOVER;
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
  Protection Mode:    MaxPerformance
  Lag Limit:          30 seconds
 
  Threshold:          30 seconds
  Active Target:      orcl_stby
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-db1.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configurable Failover Conditions
  Health Conditions:
    Corrupted Controlfile          YES
    Corrupted Dictionary           YES
    Inaccessible Logfile            NO
    Stuck Archiver                  NO
    Datafile Write Errors          YES
 
  Oracle Error Conditions:
    (none)
 
// Start Observer in background //
 
>>> oracle@Observer
 
$ mkdir -p /u01/observer
 
$ nohup dgmgrl -logfile /u01/observer/fsfo.log sys/sysorcl@ORCL "start observer file='/u01/observer/fsfo.dat'" &
 
DGMGRL> show fast_start failover;
 
Fast-Start Failover: Enabled in Potential Data Loss Mode    <<<<<<<<<< Because of "Max Performance" mode I suppose?
 
  Protection Mode:    MaxPerformance
  Lag Limit:          30 seconds
 
  Threshold:          30 seconds
  Active Target:      orcl_stby
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configurable Failover Conditions
  Health Conditions:
    Corrupted Controlfile          YES
    Corrupted Dictionary           YES
    Inaccessible Logfile            NO
    Stuck Archiver                  NO
    Datafile Write Errors          YES
 
  Oracle Error Conditions:
    (none)
```


## FSFO test

```
// Primary //
 
SQL> shu abort;
 
Observer Log File:
+++++++++++++++++++++++++++++++++++++++++++++
[W000 2022-04-18T11:22:18.103+03:00] Primary database cannot be reached.
[W000 2022-04-18T11:22:18.103+03:00] Fast-Start Failover threshold has not exceeded. Retry for the next 30 seconds
[W000 2022-04-18T11:22:19.103+03:00] Try to connect to the primary.
[W000 2022-04-18T11:22:20.205+03:00] Primary database cannot be reached.
[W000 2022-04-18T11:22:21.206+03:00] Try to connect to the primary.
[W000 2022-04-18T11:22:46.988+03:00] Primary database cannot be reached.
[W000 2022-04-18T11:22:46.988+03:00] Fast-Start Failover threshold has not exceeded. Retry for the next 2 seconds
[W000 2022-04-18T11:22:47.988+03:00] Try to connect to the primary.
[W000 2022-04-18T11:22:49.053+03:00] Primary database cannot be reached.
[W000 2022-04-18T11:22:49.053+03:00] Fast-Start Failover threshold has expired.
[W000 2022-04-18T11:22:49.053+03:00] Try to connect to the standby.
[W000 2022-04-18T11:22:49.053+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T11:22:49.053+03:00] Check if the standby is ready for failover.
[S002 2022-04-18T11:22:50.059+03:00] Fast-Start Failover started...
 
2022-04-18T11:22:50.059+03:00
Initiating Fast-Start Failover to database "orcl_stby"...
[S002 2022-04-18T11:22:50.059+03:00] Initiating Fast-start Failover.
Performing failover NOW, please wait...
Failover succeeded, new primary is "orcl_stby"
2022-04-18T11:23:05.403+03:00
[S002 2022-04-18T11:23:05.403+03:00] Fast-Start Failover finished...
[W000 2022-04-18T11:23:05.403+03:00] Failover succeeded. Restart pinging.
[W000 2022-04-18T11:23:05.409+03:00] Primary database has changed to orcl_stby.
[W000 2022-04-18T11:23:05.410+03:00] Try to connect to the primary orcl_stby.
[W000 2022-04-18T11:23:05.410+03:00] Try to connect to the primary orcl_stby.
[W000 2022-04-18T11:23:05.471+03:00] Connection to the primary restored!
[W000 2022-04-18T11:23:05.478+03:00] The standby orcl needs to be reinstated
[W000 2022-04-18T11:23:05.478+03:00] Try to connect to the new standby orcl.
[W000 2022-04-18T11:23:06.478+03:00] Disconnecting from database orcl_stby.
[W000 2022-04-18T11:23:07.480+03:00] Connection to the new standby restored!
[W000 2022-04-18T11:23:08.484+03:00] Failed to ping the new standby.
[W000 2022-04-18T11:23:09.484+03:00] Try to connect to the new standby orcl.
[W000 2022-04-18T11:23:11.484+03:00] Connection to the new standby restored!        <<<<<<<<<< it was not able to connect to old primary database (maybe something is wrong with my setup)
[W000 2022-04-18T11:23:11.488+03:00] Failed to ping the new standby.
...
...
...
2022-04-18T11:38:25.862+03:00           <<<<<<<<<< after manual "startup;" on the old primary database Observer automatically converted it to standby
Initiating reinstatement for database "orcl"...
Reinstating database "orcl", please wait...
[W000 2022-04-18T11:38:35.878+03:00] The standby orcl is ready to be a FSFO target
Reinstatement of database "orcl" succeeded
2022-04-18T11:39:20.417+03:00
[W000 2022-04-18T11:39:20.933+03:00] Successfully reinstated database orcl.
+++++++++++++++++++++++++++++++++++++++++++++
 
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl_stby - Primary database
    orcl      - (*) Physical standby database
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
Configuration Status:
SUCCESS   (status updated 54 seconds ago)
```


## Network Outage tests

### Commands

```
>>> admin@db1/db2/observer
 
$ sudo yum install -y firewalld
 
// Primary //
 
{
sudo systemctl start firewalld
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.16/32 -j DROP
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.32/32 -j DROP
}
 
// Standby //
 
{
sudo systemctl start firewalld
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.9/32 -j DROP
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.32/32 -j DROP
}
 
// Observer //
 
{
sudo systemctl start firewalld
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.9/32 -j DROP
sudo firewall-cmd --direct --add-rule ipv4 filter OUTPUT 1 -o eth0 -d 10.128.0.16/32 -j DROP
}
```


### Max Performance

> **NOTE:** 2385393.1 — "Either maximum availability mode or maximum performance mode can be used with fast-start failover."

#### Test 1: Primary network outage (Max Performance)

```
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - (*) Physical standby database
 
  (*) Fast-Start Failover target
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '30'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
  Lag Limit:          30 seconds
  Threshold:          30 seconds
  Active Target:      orcl_stby
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configuration Status:
SUCCESS
```

> **NOTE:** Observer almost instantly discovered Primary database is down.

```
[W000 2022-04-18T12:16:13.406+03:00] Primary database cannot be reached.
```

> **NOTE:** Observer wait for "FastStartFailoverThreshold" and started Failover process.

```
[W000 2022-04-18T12:16:13.406+03:00] Primary database cannot be reached.
[W000 2022-04-18T12:16:28.408+03:00] Primary database cannot be reached.
[W000 2022-04-18T12:16:28.408+03:00] Fast-Start Failover threshold has expired.
[W000 2022-04-18T12:16:28.408+03:00] Try to connect to the standby.
[W000 2022-04-18T12:16:28.408+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T12:16:28.408+03:00] Check if the standby is ready for failover.
[W000 2022-04-18T12:16:44.411+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T12:16:45.414+03:00]  Unable to check if standby is ready for failover.
[W000 2022-04-18T12:16:45.414+03:00] Try to connect to the standby.
[W000 2022-04-18T12:16:45.450+03:00] Check if the standby is ready for failover.
[W000 2022-04-18T12:17:00.452+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T12:17:02.454+03:00]  Unable to check if standby is ready for failover.
[W000 2022-04-18T12:17:02.454+03:00] Try to connect to the standby.
[W000 2022-04-18T12:17:02.496+03:00] Check if the standby is ready for failover.
[W000 2022-04-18T12:17:16.498+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T12:17:19.499+03:00]  Unable to check if standby is ready for failover.
[W000 2022-04-18T12:17:19.499+03:00] Try to connect to the standby.
[W000 2022-04-18T12:17:19.533+03:00] Check if the standby is ready for failover.
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl
[S017 2022-04-18T12:17:29.416+03:00] Fast-Start Failover started...
 
2022-04-18T12:17:29.416+03:00
Initiating Fast-Start Failover to database "orcl_stby"...
[S017 2022-04-18T12:17:29.416+03:00] Initiating Fast-start Failover.
Performing failover NOW, please wait...
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl
Failover succeeded, new primary is "orcl_stby"      <<<<<<<<<< Promoted Standby as new Primary
2022-04-18T12:17:47.145+03:00
```

> **NOTE:** old Primary wrote below info to alert.log and stopped itself.

```
2022-04-18T12:16:56.097097+03:00
Primary has heard from neither observer nor target standby within FastStartFailoverThreshold seconds.
It is likely an automatic failover has already occurred. Primary is shutting down.
2022-04-18T12:16:56.097420+03:00
Errors in file /u01/app/oracle/diag/rdbms/orcl/ORCL/trace/ORCL_lg00_18037.trc:
ORA-16830: primary isolated from fast-start failover partners longer than FastStartFailoverThreshold seconds: shutting down
USER (ospid: 18037): terminating the instance due to ORA error 16830
2022-04-18T12:16:56.174943+03:00
System state dump requested by (instance=1, osid=18037 (LG00)), summary=[abnormal instance termination].
System State dumped to trace file /u01/app/oracle/diag/rdbms/orcl/ORCL/trace/ORCL_diag_18016.trc
2022-04-18T12:16:56.712171+03:00
Dumping diagnostic data in directory=[cdmp_20220418121656], requested by (instance=1, osid=18037 (LG00)), summary=[abnormal instance termination].
2022-04-18T12:16:57.878625+03:00
Instance terminated by USER, pid = 18037
```

Status after failover:

```
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl_stby - Primary database
    Warning: ORA-16824: multiple warnings, including fast-start failover-related warnings, detected for the database
 
    orcl      - (*) Physical standby database (disabled)
      ORA-16661: the standby database needs to be reinstated
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
Configuration Status:
WARNING   (status updated 38 seconds ago)
```

Enable network back on Old Primary server and start up the database so Observer can automatically convert it to New Standby database. Here is Observer log after enabling the network and starting Old Primary database:

```
[W000 2022-04-18T12:28:25.085+03:00] Try to connect to the new standby orcl.
[W000 2022-04-18T12:28:26.085+03:00] Connection to the new standby restored!
[W000 2022-04-18T12:28:59.130+03:00] Try to connect to the primary orcl_stby.
[W000 2022-04-18T12:29:00.130+03:00] Connection to the primary restored!
[W000 2022-04-18T12:29:00.130+03:00] Wait for new primary to be ready to reinstate.
[W000 2022-04-18T12:29:00.130+03:00] New primary is now ready to reinstate.
[W000 2022-04-18T12:29:01.134+03:00] Issuing REINSTATE command.
 
2022-04-18T12:29:01.134+03:00
Initiating reinstatement for database "orcl"...
Reinstating database "orcl", please wait...
[W000 2022-04-18T12:29:21.161+03:00] The standby orcl is ready to be a FSFO target
Reinstatement of database "orcl" succeeded
2022-04-18T12:29:51.244+03:00
[W000 2022-04-18T12:29:52.200+03:00] Successfully reinstated database orcl.
```

> **Summary:**
> - Availability: there will be some downtime during failover process. Approximate downtime = FastStartFailoverThreshold + 60 sec (failover itself);
> - Data loss: according to Oracle Docs data loss is possible in Max Performance mode and can be "controlled" with parameter FastStartFailoverLagLimit.


#### Test 2: Standby network outage (Max Performance)

```
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - (*) Physical standby database
 
  (*) Fast-Start Failover target
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '30'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
  Lag Limit:          30 seconds
  Threshold:          30 seconds
  Active Target:      orcl_stby
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configuration Status:
SUCCESS
```

Observer log file after disabling network on Standby server:

```
[W000 2022-04-18T13:21:45.797+03:00] Failed to ping the standby.
[W000 2022-04-18T13:21:59.821+03:00] The primary database has requested a transition to the UNSYNC/LAGGING state with the standby database orcl_stby.
[W000 2022-04-18T13:21:59.825+03:00] Permission granted to the primary database to transition to LAGGING state with the standby database orcl_stby.
 
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl_stby
[W000 2022-04-18T13:23:02.923+03:00] The primary database has been in LAGGING state for 63 seconds.
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl_stby
ORA-12170: TNS:Connect timeout occurred
```

Status:

```
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    Warning: ORA-16829: fast-start failover configuration is lagging
 
    orcl_stby - (*) Physical standby database
      Error: ORA-16662: network timeout when contacting a member
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
Configuration Status:
ERROR   (status updated 263 seconds ago)
```

Enabled network back on Standby server:

```
Unable to connect to database using orcl_stby
[W000 2022-04-18T13:32:29.754+03:00] The primary database has been in LAGGING state for 630 seconds.
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl_stby
[W000 2022-04-18T13:32:59.797+03:00] The primary database returned to NOT LAGGING state with the standby database orcl_stby.
```

> **Summary:**
> - Availability: there is no effect on Primary database, but replication lag will grow so you have to monitor the archive log / flashback log mount point disk usage on Primary.
> - Data loss: no.

> **NOTE:** if something will happen with you Primary database during Standby outage – Observer will have no candidates for failover. For such cases you have to have at least two Standby databases.

#### Test 3: Observer network outage (Max Performance)

Observer log file after disabling network on its server:

```
[W000 2022-04-18T13:41:24.513+03:00] Failed to ping the standby.
[W000 2022-04-18T13:41:25.513+03:00] Primary database cannot be reached.
[W000 2022-04-18T13:41:40.517+03:00] Primary database cannot be reached.
[W000 2022-04-18T13:41:40.517+03:00] Fast-Start Failover threshold has expired.
[W000 2022-04-18T13:41:40.517+03:00] Try to connect to the standby.
[W000 2022-04-18T13:41:40.517+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T13:41:56.520+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T13:41:57.521+03:00] Try to connect to the standby.
[W000 2022-04-18T13:42:12.524+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T13:42:14.525+03:00] Try to connect to the standby.
ORA-12170: TNS:Connect timeout occurred
 
Unable to connect to database using orcl_stby
[W000 2022-04-18T13:42:28.528+03:00] Making a last connection attempt to primary database before proceeding with Fast-Start Failover.
[W000 2022-04-18T13:42:31.529+03:00] Try to connect to the standby.
```

Observer was not able to connect into Primary and Standby database instances. But it tried to perform Failover because he was not able to connect to Primary server – attempt failed because there is no connection to Standby server too.

Status:

```
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    Error: ORA-16820: fast-start failover observer is no longer observing this database
 
    orcl_stby - (*) Physical standby database
      Error: ORA-16820: fast-start failover observer is no longer observing this database
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
Configuration Status:
ERROR   (status updated 24 seconds ago)
```

Check if FastStartFailover (FSFO) functionality is not working anymore.

Stop Primary database with "shutdown abort;" and check if Standby database tries to promote:

```
2022-04-18T13:45:29.751845+03:00
 rfs (PID:24115): Possible network disconnect with primary database
2022-04-18T13:45:29.755651+03:00
 rfs (PID:22813): Possible network disconnect with primary database
2022-04-18T13:45:29.767534+03:00
 rfs (PID:24117): Possible network disconnect with primary database
```

Automatic Failover didn't happen. FSFO is not working without Observer.

Started Primary database back and ensure Primary and Standby databases are in sync.

Enable network back on Observer server:

```
[W000 2022-04-18T13:49:20.691+03:00] Check if the standby is ready for failover.
[W000 2022-04-18T13:49:20.695+03:00] Fast-Start Failover is not possible.
[W000 2022-04-18T13:49:23.695+03:00] Check if the standby is ready for failover.
[W000 2022-04-18T13:49:23.700+03:00] Fast-Start Failover is not possible.
[W000 2022-04-18T13:49:25.700+03:00] Pings of primary database have resumed.
[W000 2022-04-18T13:49:25.700+03:00] Try to connect to the primary.
ORA-12170: TNS:Connect timeout occurred
Unable to connect to database using orcl_stby
ORA-12170: TNS:Connect timeout occurred
Unable to connect to database using orcl
```

Status:

```
DGMGRL> show configuration;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl      - Primary database
    orcl_stby - (*) Physical standby database
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
 
Configuration Status:
SUCCESS   (status updated 36 seconds ago)
```

> **Summary:**
> - Availability: no.
> - Data loss: no.

> **NOTE:** FSFO functionality will not work without Observer.

#### Test 4: Data Loss (Max Performance)

Status:

```
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxPerformance
  Members:
  orcl_stby - Primary database
    orcl      - (*) Physical standby database
 
  (*) Fast-Start Failover target
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '30'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover: Enabled in Potential Data Loss Mode
  Lag Limit:          30 seconds
  Threshold:          30 seconds
  Active Target:      orcl
  Potential Targets:  "orcl"
    orcl       valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configuration Status:
SUCCESS
```

Scenario:

- Disable network on Primary database server;
- Quickly create some table while Primary database didn't stop itself;
- Observer performs Failover to Standby database;
- Here we should have New Primary database (running) and Old Primary database (stopped);
- Disable FSFO and manually check if Old Primary has a table from step 2, but New Primary doesn't:

```
dgmgrl> disable fast_start failover;
sqlplus-old-primary> startup nomount;
sqlplus-old-primary> alter system set dg_broker_start=FALSE scope=spfile;
sqlplus-old-primary> startup;
sqlplus-old-primary> select * from test;    <<<<<<<<<< test table was in place
```

- Enable FSFO back so Observer can convert Old Primary to New Standby database (test table will be completely lost because of flashback to sync Old Primary with New Primary):

```
sqlplus-old-primary> alter system set dg_broker_start=TRUE scope=spfile;
sqlplus-old-primary> shu immediate;
sqlplus-old-primary> startup mount;
----- Enabled network on Old Primary server -----
DGMGRL> reinstate database orcl_stby; <<<<<<<<<< add standby back
dgmgrl> enable fast_start failover; <<<<<<<<<< enable FSFO
```

> **Summary:**
> - Availability: there will be some downtime during failover process. Approximate downtime = FastStartFailoverThreshold + 60 sec (failover itself);
> - Data loss: Yes. According to Oracle Docs data loss is possible in Max Performance mode and can be "controlled" with parameter FastStartFailoverLagLimit. In my case test table created before Primary got network outage was lost after synching with New Primary.

> **NOTE:** you can still try to save your data from Old Primary database before synching it with New Primary.


### Max Availability

#### Switch to Max Availability mode

```
DGMGRL> DISABLE FAST_START FAILOVER;
Disabled.
 
DGMGRL> EDIT DATABASE ORCL SET PROPERTY 'LogXptMode'='SYNC';
Property "LogXptMode" updated
 
DGMGRL> EDIT DATABASE ORCL_STBY SET PROPERTY 'LogXptMode'='SYNC';
Property "LogXptMode" updated
 
DGMGRL> EDIT CONFIGURATION SET PROTECTION MODE AS MAXAVAILABILITY;
Succeeded.
 
DGMGRL> ENABLE FAST_START FAILOVER;
Enabled in Zero Data Loss Mode.
 
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxAvailability
  Members:
  orcl      - Primary database
    orcl_stby - (*) Physical standby database
 
  (*) Fast-Start Failover target
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '0'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover: Enabled in Zero Data Loss Mode
  Lag Limit:          0 seconds
  Threshold:          30 seconds
  Active Target:      orcl_stby
  Potential Targets:  "orcl_stby"
    orcl_stby  valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configuration Status:
SUCCESS
```

#### Test 1: Primary network outage (Max Availability)

Same results as in Max Performance Test 1.

#### Test 2: Standby network outage (Max Availability)

Same results as in Max Performance Test 2.

#### Test 3: Observer network outage (Max Availability)

Same results as in Max Performance Test 3.

#### Test 4: Data Loss (Max Availability)

Status:

```
DGMGRL> show configuration verbose;
 
Configuration - dg_config_test1
 
  Protection Mode: MaxAvailability
  Members:
  orcl_stby - Primary database
    orcl      - (*) Physical standby database
 
  (*) Fast-Start Failover target
 
  Properties:
    FastStartFailoverThreshold      = '30'
    OperationTimeout                = '30'
    TraceLevel                      = 'USER'
    FastStartFailoverLagLimit       = '0'
    CommunicationTimeout            = '180'
    ObserverReconnect               = '0'
    FastStartFailoverAutoReinstate  = 'TRUE'
    FastStartFailoverPmyShutdown    = 'TRUE'
    BystandersFollowRoleChange      = 'ALL'
    ObserverOverride                = 'FALSE'
    ExternalDestination1            = ''
    ExternalDestination2            = ''
    PrimaryLostWriteAction          = 'CONTINUE'
    ConfigurationWideServiceName    = 'ORCL_CFG'
 
Fast-Start Failover: Enabled in Zero Data Loss Mode
  Lag Limit:          0 seconds
  Threshold:          30 seconds
  Active Target:      orcl
  Potential Targets:  "orcl"
    orcl       valid
  Observer:           yc-oracle-observer.ru-central1.internal
  Shutdown Primary:   TRUE
  Auto-reinstate:     TRUE
  Observer Reconnect: (none)
  Observer Override:  FALSE
 
Configuration Status:
SUCCESS
```

Scenario is the same as from Max Performance Test 4, **BUT** I was not able to create test table on Primary database after network outage. Looks like in Max Availability mode everything is "freezing" immediately in case of any issues with access to Standby database because of SYNC mode.

> **Summary:**
> - Availability: there will be some downtime during failover process. Approximate downtime = FastStartFailoverThreshold + 60 sec (failover itself);
> - Data loss: there will NOT be any data loss in MaxAvailability mode. Ref. to docs for details 2385393.1 — Maximum availability mode provides an automatic failover environment guaranteed to lose no data.

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




