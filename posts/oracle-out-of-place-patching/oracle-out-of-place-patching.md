<!--
---
title: "Oracle Out of Place patching"
slug: oracle-out-of-place-patching
created: 2026-07-14
updated: 2026-07-14
author: admin
categories: [oracle, archive]
tags: [oracle, patching]
pinned: false
description: "Step-by-step guide to perform Oracle Out of Place patching to minimize DB downtime."
---
-->

# Oracle Out of Place patching

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Useful Commands](#useful-commands)
- [Clone your current Oracle Home](#clone-your-current-oracle-home)
- [Patch New (cloned) Oracle Home](#patch-new-cloned-oracle-home)
- [Stop Oracle services (database, listener, etc) running from Old Oracle Home](#stop-oracle-services-database-listener-etc-running-from-old-oracle-home)
- [Update your environment files (if any) and /etc/oratab](#update-your-environment-files-if-any-and-etcoratab)
- [Start Oracle Database (do not start listener) from New Oracle Home](#start-oracle-database-do-not-start-listener-from-new-oracle-home)
- [Perform database post-patching steps](#perform-database-post-patching-steps)
- [Healthcheck and Oracle Listener start](#healthcheck-and-oracle-listener-start)
- [Patch Old Oracle Home to same patch level](#patch-old-oracle-home-to-same-patch-level)

## Docs

- How to Perform out of Place Patching to Minimize DB Downtime (Doc ID 1389364.1)
- A Technique To Minimize Database Downtime When Patching (Doc ID 1390066.1)
- [RAC Example by unknowndba](https://unknowndba.blogspot.com/2019/09/out-of-place-rolling-patching-aka.html)
- [About OJVM STARTUP UPGRADE requirements](https://mikedietrichde.com/2020/01/23/do-you-need-startup-upgrade-for-ojvm/)


## Useful Commands

List of installed patches:

```
$ opatch lspatches
$ opatch lsinventory | grep -i <patch_number_or_name>
```

Check for possible conflicts:

```
$ cd patch_directory
$ opatch prereq CheckConflictAgainstOHWithDetail -ph ./
```

SQL query from DB registry to get list of installed patches:

```
SQL> set lines 222 pages 999;
col COMMENTS format a60;
col ACTION format a11;
col VERSION format a15;
col NAMESPACE format a10;
col BUNDLE_SERIES format a10;
col ACTION_TIME format a35;
select * from registry$history
order by ACTION_TIME;
```

Get errors/failers from patch log:

```
$ egrep -i "error|fail|ora-|ac-|rc-" /u01/app/oracle/product/19.0.0/dbhome_1/cfgtoollogs/opatch/patchXXX.log
```


## Clone your current Oracle Home

```
>>> oracle
 
$ cp -rp /u01/app/oracle/product/19.0.0/dbhome_1 /u01/app/oracle/product/19.0.0/dbhome_2
 
$ cd /u01/app/oracle/product/19.0.0/dbhome_2
 
$ ./runInstaller -ignorePrereq -waitforcompletion -silent \
-responseFile /u01/app/oracle/product/19.0.0/dbhome_2/install/response/db_install.rsp \
oracle.install.option=INSTALL_DB_SWONLY \
ORACLE_HOSTNAME=${ORACLE_HOSTNAME} \
UNIX_GROUP_NAME=oinstall \
INVENTORY_LOCATION=/u01/app/oraInventory \
SELECTED_LANGUAGES=en,en_GB \
ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_2 \
ORACLE_BASE=/u01/app/oracle \
oracle.install.db.InstallEdition=EE \
oracle.install.db.OSDBA_GROUP=dba \
oracle.install.db.OSBACKUPDBA_GROUP=dba \
oracle.install.db.OSDGDBA_GROUP=dba \
oracle.install.db.OSKMDBA_GROUP=dba \
oracle.install.db.OSRACDBA_GROUP=dba \
SECURITY_UPDATES_VIA_MYORACLESUPPORT=false \
DECLINE_SECURITY_UPDATES=true
 
>>> root
 
$ /u01/app/oracle/product/19.0.0/dbhome_2/root.sh
 
$ cat /u01/app/oraInventory/ContentsXML/inventory.xml
++++++++++
<?xml version="1.0" standalone="yes" ?>
<!-- Copyright (c) 1999, 2020, Oracle and/or its affiliates.
All rights reserved. -->
<!-- Do not modify the contents of this file by hand. -->
<INVENTORY>
<VERSION_INFO>
   <SAVED_WITH>12.2.0.7.0</SAVED_WITH>
   <MINIMUM_VER>2.1.0.6.0</MINIMUM_VER>
</VERSION_INFO>
<HOME_LIST>
<HOME NAME="OraDB19Home1" LOC="/u01/app/oracle/product/19.0.0/dbhome_1" TYPE="O" IDX="1"/>
<HOME NAME="OraDB19Home2" LOC="/u01/app/oracle/product/19.0.0/dbhome_2" TYPE="O" IDX="2"/>
</HOME_LIST>
<COMPOSITEHOME_LIST>
</COMPOSITEHOME_LIST>
</INVENTORY>
++++++++++
```


## Patch New (cloned) Oracle Home

```
>>> oracle
 
$ cat .bash_profile
++++++++++
# .bash_profile
# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi
 
home1() {
# User specific environment and startup programs
export ORACLE_SID=ORCL
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=$ORACLE_BASE/product/19.0.0/dbhome_1
export ORACLE_HOSTNAME=srv-example-db.oracle.com
export TMP=/tmp
export TMPDIR=$TMP
export PATH=/usr/sbin:$PATH
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:/usr/sbin:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
export PS1='\[\033[0;32m\]$ORACLE_SID> \[\033[0;33m\]\u@\h\[\033[00m\] [\t] \w]\$ '
##
## Tools
##
alias rman="rlwrap ${ORACLE_HOME}/bin/rman"
alias sp="rlwrap ${ORACLE_HOME}/bin/sqlplus / as sysdba"
}
 
home2() {
# User specific environment and startup programs
export ORACLE_SID=ORCL
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=$ORACLE_BASE/product/19.0.0/dbhome_2
export ORACLE_HOSTNAME=srv-example-db.oracle.com
export TMP=/tmp
export TMPDIR=$TMP
export PATH=/usr/sbin:$PATH
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:/usr/sbin:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
export PS1='\[\033[0;32m\]$ORACLE_SID> \[\033[0;33m\]\u@\h\[\033[00m\] [\t] \w]\$ '
##
## Tools
##
alias rman="rlwrap ${ORACLE_HOME}/bin/rman"
alias sp="rlwrap ${ORACLE_HOME}/bin/sqlplus / as sysdba"
}
++++++++++
 
$ home2
$ opatch lspatches
+++++
29585399;OCW RELEASE UPDATE 19.3.0.0.0 (29585399)
29517242;Database Release Update : 19.3.0.0.190416 (29517242)
 
OPatch succeeded.
+++++
 
*** Upgrade OPatch ***
 
$ opatch version
+++++
OPatch Version: 12.2.0.1.17
 
OPatch succeeded.
+++++
 
$ mv $ORACLE_HOME/OPatch $ORACLE_HOME/OPatch_bkp_`date +%F`
$ unzip /u01/soft/p6880880_190000_Linux-x86-64.zip -d $ORACLE_HOME/
$ ls -ld $ORACLE_HOME/OPatch*
$ opatch version
+++++
OPatch Version: 12.2.0.1.19
 
OPatch succeeded.
+++++
 
*** Patch 30557433: DATABASE RELEASE UPDATE 19.6.0.0.0 ***
 
$ {
cd /u01/soft
unzip p30557433_190000_Linux-x86-64.zip
cd 30557433
}
 
$ opatch prereq CheckConflictAgainstOHWithDetail -ph ./
+++++
Oracle Interim Patch Installer version 12.2.0.1.19
Copyright (c) 2020, Oracle Corporation.  All rights reserved.
 
PREREQ session
 
Oracle Home       : /u01/app/oracle/product/19.0.0/dbhome_2
Central Inventory : /u01/app/oraInventory
   from           : /u01/app/oracle/product/19.0.0/dbhome_2/oraInst.loc
OPatch version    : 12.2.0.1.19
OUI version       : 12.2.0.7.0
Log file location : /u01/app/oracle/product/19.0.0/dbhome_2/cfgtoollogs/opatch/opatch.log
 
Invoking prereq "checkconflictagainstohwithdetail"
 
Prereq "checkConflictAgainstOHWithDetail" passed.
 
OPatch succeeded.
+++++
 
$ opatch apply
+++++
Patch 30557433 successfully applied.
Sub-set patch [29517242] has become inactive due to the application of a super-set patch [30557433].
Please refer to Doc ID 2161861.1 for any possible further required actions.
Log file location: /u01/app/oracle/product/19.0.0/dbhome_2/cfgtoollogs/opatch/opatch.log
 
OPatch succeeded.
+++++
 
$ egrep -i "error|fail|ora-|ac-|rc-" /u01/app/oracle/product/19.0.0/dbhome_2/cfgtoollogs/opatch/opatch.log
 
*** Patch 30484981: OJVM RELEASE UPDATE 19.6.0.0.0 ***
 
$ {
cd /u01/soft
unzip p30484981_190000_Linux-x86-64.zip
cd 30484981
}
 
$ opatch prereq CheckConflictAgainstOHWithDetail -ph ./
+++++
Oracle Interim Patch Installer version 12.2.0.1.19
Copyright (c) 2020, Oracle Corporation.  All rights reserved.
 
PREREQ session
 
Oracle Home       : /u01/app/oracle/product/19.0.0/dbhome_2
Central Inventory : /u01/app/oraInventory
   from           : /u01/app/oracle/product/19.0.0/dbhome_2/oraInst.loc
OPatch version    : 12.2.0.1.19
OUI version       : 12.2.0.7.0
Log file location : /u01/app/oracle/product/19.0.0/dbhome_2/cfgtoollogs/opatch/opatch.log
 
Invoking prereq "checkconflictagainstohwithdetail"
 
Prereq "checkConflictAgainstOHWithDetail" passed.
 
OPatch succeeded.
+++++
 
$ opatch apply
+++++
Patch 30484981 successfully applied.
Log file location: /u01/app/oracle/product/19.0.0/dbhome_2/cfgtoollogs/opatch/opatch.log
 
OPatch succeeded.
+++++
```


## Stop Oracle services (database, listener, etc) running from Old Oracle Home

```
>>> oracle
 
$ home1
 
$ lsnrctl stop LISTENER
 
$ sqlplus / as sysdba
 
SQL> alter system checkpoint;
 
SQL> shu immediate;
```


## Update your environment files (if any) and /etc/oratab

```
>>> oracle
 
$ cat /etc/oratab | grep -i orcl
+++++
##ORCL:/u01/app/oracle/product/19.0.0/dbhome_1:N
ORCL:/u01/app/oracle/product/19.0.0/dbhome_2:N
+++++
 
$ vi ~/.bash_profile
```


## Start Oracle Database (do not start listener) from New Oracle Home

```
>>> oracle
 
$ home2
 
$ sqlplus / as sysdba
 
SQL> startup;
```


## Perform database post-patching steps

> **NOTE:** only if required according to patch README file.

```
$ sqlplus / as sysdba
 
SQL> set lines 222 pages 999;
col COMMENTS format a60;
col ACTION format a11;
col VERSION format a15;
col NAMESPACE format a10;
col BUNDLE_SERIES format a10;
col ACTION_TIME format a35;
select * from registry$history
order by ACTION_TIME;
++++++++++
ACTION_TIME                         ACTION      NAMESPACE  VERSION                 ID COMMENTS                                                     BUNDLE_SER
----------------------------------- ----------- ---------- --------------- ---------- ------------------------------------------------------------ ----------
05-JAN-21 09.35.10.332371 AM        RU_APPLY    SERVER     19.0.0.0.0                 Patch applied on 19.3.0.0.0: Release_Update - 190410122720
                                    BOOTSTRAP   DATAPATCH  19                         RDBMS_19.3.0.0.0DBRU_LINUX.X64_190417
 
++++++++++
 
$ cd $ORACLE_HOME/OPatch
$ ./datapatch -verbose
$ sqlplus / as sysdba
 
SQL> set lines 222 pages 999;
col COMMENTS format a75;
col ACTION format a11;
col VERSION format a22;
col NAMESPACE format a10;
col BUNDLE_SERIES format a5;
col ACTION_TIME format a35;
select * from registry$history
order by ACTION_TIME;
++++++++++
ACTION_TIME                         ACTION      NAMESPACE  VERSION                        ID COMMENTS                                                                    BUNDL
----------------------------------- ----------- ---------- ---------------------- ---------- --------------------------------------------------------------------------- -----
05-JAN-21 09.35.10.332371 AM        RU_APPLY    SERVER     19.0.0.0.0                        Patch applied on 19.3.0.0.0: Release_Update - 190410122720
05-JAN-21 09.31.04.535922 AM        jvmpsu.sql  SERVER     19.6.0.0.200114OJVMRU           0 RAN jvmpsu.sql
05-JAN-21 09.31.04.578736 AM        APPLY       SERVER     19.6.0.0.200114OJVMRU           0 OJVM RU post-install
05-JAN-21 09.35.53.850255 AM        RU_APPLY    SERVER     19.0.0.0.0                        Patch applied from 19.3.0.0.0 to 19.6.0.0.0: Release_Update - 191217155004
                                    BOOTSTRAP   DATAPATCH  19                                RDBMS_19.6.0.0.0DBRU_LINUX.X64_191217
++++++++++
```


## Healthcheck and Oracle Listener start

Check database alert log file for any errors and start listener:

```
>>> oracle
 
$ lsnrclt start LISTENER
```


## Patch Old Oracle Home to same patch level

Same patching steps.

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
