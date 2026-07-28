<!--
---
title: "OCFS2: Setup Oracle Cluster Filesystem"
slug: ocfs2-setup
created: 2026-07-12
updated: 2026-07-12
author: admin
categories: [oracle, archive, miscellaneous]
tags: [oracle, ocfs2, filesystem, cluster]
pinned: false
description: "How to set up OCFS2 (Oracle Cluster Filesystem) on Oracle Linux: install packages, prepare storage, configure cluster, start services and mount."
---
-->

# OCFS2: Setup Oracle Cluster Filesystem

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Linux Version](#linux-version)
- [Install OCFS2 packages](#install-ocfs2-packages)
- [Prepare Storage](#prepare-storage)
- [Prepare OCFS2 configuration files](#prepare-ocfs2-configuration-files)
- [Setup OCFS2 cluster](#setup-ocfs2-cluster)
- [Start Cluster](#start-cluster)
- [Mount and update /etc/fstab](#mount-and-update-etcfstab)
- [Additional commands](#additional-commands)
- [Additional sources](#additional-sources)

## Docs

- OCFS2 Master Note (Doc ID 1546224.1)
- How to Install or Update OCFS2 on Oracle Enterprise Linux (Doc ID 438029.1)
- How to Add a New OCFS2 Node to an Online Cluster (Doc ID 761020.1)
- How to Change and Check Number of Slots for OCFS2 (Doc ID 602861.1)
- modprobe: FATAL: Module ocfs2_dlmfs not found (Doc ID 2354666.1)
- OCFS2 1.2 - FREQUENTLY ASKED QUESTIONS (Doc ID 391771.1)
- [Инсталляция Oracle RAC: OCFS2](https://oracle-dba.ru/database/installation/distributed/rac/linux/6.7/ocfs/)


## Linux Version

```
$ cat /etc/os-release
++++++++++
NAME="Oracle Linux Server"
VERSION="6.10"
ID="ol"
VERSION_ID="6.10"
PRETTY_NAME="Oracle Linux Server 6.10"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:oracle:linux:6:10:server"
HOME_URL="https://linux.oracle.com/"
BUG_REPORT_URL="https://bugzilla.oracle.com/"
 
ORACLE_BUGZILLA_PRODUCT="Oracle Linux 6"
ORACLE_BUGZILLA_PRODUCT_VERSION=6.10
ORACLE_SUPPORT_PRODUCT="Oracle Linux"
ORACLE_SUPPORT_PRODUCT_VERSION=6.10
++++++++++
 
$ uname -a
++++++++++
Linux srv-ocfs2-node1.oracle.com 4.1.12-124.34.1.el6uek.x86_64 #2 SMP  x86_64 GNU/Linux
++++++++++
```


## Install OCFS2 packages

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ yum install -y ocfs2*
$ yum list installed | grep -i ocfs2
++++++++++
ocfs2-tools.x86_64                 1.8.6-11.el6               @public_ol6_latest
ocfs2-tools-devel.x86_64           1.8.6-11.el6               @public_ol6_latest
++++++++++
 
$ uname -r
++++++++++
4.1.12-124.34.1.el6uek.x86_64
++++++++++
 
$ chkconfig ocfs2 on
```


## Prepare Storage

> **NOTE:** test lab for this paper is placed on my laptop. Both VM's are on VM Ware Workstation, so I have to perform some modifications with virtual machine config files to simulate shared device, otherwise it will not work (disk device will be visible only from one VM).

Files to modify:

```
D:\VM\srv-ocfs2-node1\srv-ocfs2-node1.vmx
D:\VM\srv-ocfs2-node2\srv-ocfs2-node2.vmx
D:\VM\srv-ocfs2-node3\srv-ocfs2-node3.vmx
```

Add below to the end of each file:

```
disk.locking = "FALSE"
diskLib.dataCacheMaxSize = "0"
diskLib.dataCacheMaxReadAheadSize = "0" 
diskLib.dataCacheMinReadAheadSize = "0" 
diskLib.dataCachePageSize = "4096" 
diskLib.maxUnsyncedWrites = "0" 
scsi1.sharedBus = "virtual"
```

Add virtual disk 10 GB in size into "srv-ocfs2-node1" server:

```
>>> root@srv-ocfs2-node1
 
$ ls -ltr /sys/class/scsi_host/host*/scan
++++++++++
--w-------. 1 root root 4096 Jan  5 14:39 /sys/class/scsi_host/host2/scan
--w-------. 1 root root 4096 Jan  5 14:39 /sys/class/scsi_host/host1/scan
--w-------. 1 root root 4096 Jan  5 14:39 /sys/class/scsi_host/host0/scan
++++++++++
 
$ {
echo "- - -" > /sys/class/scsi_host/host0/scan
echo "- - -" > /sys/class/scsi_host/host1/scan
echo "- - -" > /sys/class/scsi_host/host2/scan
}
$ lsblk
++++++++++
...
...
sdb                                   8:16   0   10G  0 disk
++++++++++
 
$ fdisk /dev/sdb
n
p
1
enter
enter
p
w
 
$ lsblk /dev/sdb
++++++++++
NAME   MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
sdb      8:16   0  10G  0 disk
  sdb1   8:17   0  10G  0 part
++++++++++
 
$ mkfs.ocfs2 /dev/sdb1
++++++++++
mkfs.ocfs2 1.8.6
Cluster stack: classic o2cb
Label:
Features: sparse extended-slotmap backup-super unwritten inline-data strict-journal-super xattr indexed-dirs refcount discontig-bg
Block size: 4096 (12 bits)
Cluster size: 4096 (12 bits)
Volume size: 10733957120 (2620595 clusters) (2620595 blocks)
Cluster groups: 82 (tail covers 7859 clusters, rest cover 32256 clusters)
Extent allocator size: 4194304 (1 groups)
Journal size: 67108864
Node slots: 4
Creating bitmaps: done
Initializing superblock: done
Writing system files: done
Writing superblock: done
Writing backup superblock: 2 block(s)
Formatting Journals: done
Growing extent allocator: done
Formatting slot map: done
Formatting quota files: done
Writing lost+found: done
mkfs.ocfs2 successful
++++++++++
 
$ mkdir -p /u01
```

Add new virtual disk to second VM "srv-ocfs2-node2" as already existing disk using VM Ware Console. Scan it with "fdisk" later:

```
$ {
echo "- - -" > /sys/class/scsi_host/host0/scan
echo "- - -" > /sys/class/scsi_host/host1/scan
echo "- - -" > /sys/class/scsi_host/host2/scan
}
 
$ mkdir -p /u01
$ fdisk /dev/sdb
p
w
```


## Prepare OCFS2 configuration files

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ mkdir -p /etc/ocfs2/
$ cat /etc/ocfs2/cluster.conf
++++++++++
cluster:
        node_count = 2
        name = testCluster
 
node:
        ip_port = 7777
        ip_address = 192.168.197.165
        number = 1
        name = srv-ocfs2-node1.oracle.com
        cluster = testCluster
 
node:
        ip_port = 7777
        ip_address = 192.168.197.166
        number = 2
        name = srv-ocfs2-node2.oracle.com
        cluster = testCluster
++++++++++
```


## Setup OCFS2 cluster

> **NOTE:** o2cb means Cluster state Backing.

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ /etc/init.d/o2cb offline testCluster
++++++++++
stat: cannot read file system information for `/dlm': No such file or directory
Unloading module "ocfs2": OK
++++++++++
```

Unload the modules used by o2cb:

```
$ /etc/init.d/o2cb unload
++++++++++
stat: cannot read file system information for `/dlm': No such file or directory
Unloading module "ocfs2_stack_o2cb": OK
/etc/init.d/o2cb: line 1151: read: read error: 0: No such device
++++++++++
```

Configure o2cb to load on boot, if you have configured the cluster to load on boot, then run start command, else run stop command:

```
$ /etc/init.d/o2cb configure
++++++++++
Load O2CB driver on boot (y/n) [n]: y
Cluster stack backing O2CB [o2cb]:
Cluster to start on boot (Enter "none" to clear) [ocfs2]: testCluster
Specify heartbeat dead threshold (>=7) [31]:
Specify network idle timeout in ms (>=5000) [30000]:
Specify network keepalive delay in ms (>=1000) [2000]:
Specify network reconnect delay in ms (>=2000) [2000]:
Writing O2CB configuration: OK
checking debugfs...
Loading stack plugin "o2cb": OK
Loading filesystem "ocfs2_dlmfs": OK
Creating directory '/dlm': OK
Mounting ocfs2_dlmfs filesystem at /dlm: OK
Setting cluster stack "o2cb": OK
Registering O2CB cluster "testCluster": OK
Setting O2CB cluster timeouts : OK
++++++++++
```

> **NOTE:** it's important to check that after above command ocfs2 kernel modules are successfully loaded, otherwise you will get error described here: *modprobe: FATAL: Module ocfs2_dlmfs not found (Doc ID 2354666.1)*.

```
$ lsmod | grep -i ocfs2
++++++++++
ocfs2_dlmfs            28672  1
ocfs2_stack_o2cb       16384  0
ocfs2_dlm             241664  1 ocfs2_stack_o2cb
ocfs2_nodemanager     245760  9 ocfs2_dlmfs,ocfs2_stack_o2cb,ocfs2_dlm
ocfs2_stackglue        20480  2 ocfs2_dlmfs,ocfs2_stack_o2cb
configfs               36864  3 ocfs2_nodemanager,target_core_mod
++++++++++
```


## Start Cluster

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ /etc/init.d/o2cb online testCluster
++++++++++
checking debugfs...
Setting cluster stack "o2cb": OK
Cluster testCluster already online
++++++++++
```

Enable o2cb service autostart after server reboot:

```
$ /etc/init.d/o2cb enable
```

Load the modules used by o2cb:

```
$ /etc/init.d/o2cb load
```

Check status:

```
$ /etc/init.d/o2cb status
++++++++++
Driver for "configfs": Loaded
Filesystem "configfs": Mounted
Stack glue driver: Loaded
Stack plugin "o2cb": Loaded
Driver for "ocfs2_dlmfs": Loaded
Filesystem "ocfs2_dlmfs": Mounted
Checking O2CB cluster "testCluster": Online
  Heartbeat dead threshold: 31
  Network idle timeout: 30000
  Network keepalive delay: 2000
  Network reconnect delay: 2000
  Heartbeat mode: Local
Checking O2CB heartbeat: Not active
Debug file system at /sys/kernel/debug: mounted
++++++++++
```


## Mount and update /etc/fstab

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ mount -t ocfs2 /dev/sdb1 /u01
$ cat /etc/fstab
++++++++++
/dev/sdb1 /u01 ocfs2 _netdev,defaults 0 0
++++++++++
```


## Additional commands

```
$ /etc/init.d/ocfs2 restart
$ /etc/init.d/o2cb force-reload
```


## Additional sources

```
>>> Installation & Upgrading:
Document 434723.1 - How to install OCFS2 on OEL via ULN
Document 438029.1 - How to Install or Update OCFS2 on Oracle Enterprise Linux
Document 603246.1 - A Reference Guide for Upgrading OCFS2
Document 975913.1 - Upgrade of OCFS2 on EL4/5 by example
Document 1084597.1 - Rolling Upgrade OCFS2 From 1.2.X To 1.4.X Fails On RHEL5/OEL5
 
>>> OCFS2 Configuration Documents:
Document 1123048.1 - Do I Have The Right OCFS2 Kernel Component (Driver) RPM?
Document 1129113.1 - How To Ensure You Have The Correct OCFS2 Driver RPM Package For Your System
Document 1204453.1 - How to reconfigure OCFS2 to use cluster private interconnect
Document 603080.1 - Linux OCFS2 - Best Practices
Document 395878.1 -  Heartbeat/Voting/Quorum Related Timeout Configuration for Linux, OCFS2, RAC Stack to Avoid Unnecessary Node Fencing, Panic and Reboot
Document 457423.1 - OCFS2 Fencing, Network, and Disk Heartbeat Timeout Configuration
Document 551286.1 - Linux OS Service 'ocfs2'
Document 835839.1 - Recommended Ocfs2 1.4.1 mount options with DB volumes
Document 603038.1 - OCFS2 and SAN Interactions
 
>>> Popular How-To's:
Document 1207078.1 - How to determine OCFS2 Filesystem Block and Cluster sizes on Linux
Document 1264409.1 -  Migrating from OCFS to OCFS2 on Enterprise Linux using fscat(8)
Document 852002.1  -  How to remove a ocfs2 node from a cluster
Document 567604.1 -  OCFS2: Considerations for Cloning OCFS2 Volumes
Document 1382196.1 - How to Enable Discontiguous Block Group Feature (discontig-bg) on OCFS2 1.4
Document 1506507.1 - How To Extract Contents of an OCFS2 Volume That Cannot Be Mounted
Document 730332.1 -  How to Backup and Restore OCFS2 File Permissions
Document 469404.1 -  How to Query the blocksize of OCFS or OCFS2 Filesystem
Document 550461.1 -  HOW TO USE OCFS2 "local" MOUNT OPTION
Document 1256604.1 - HOWTO Disable OCFS2 Sparse Files
Document 602861.1 -  How to Change and Check Number of Slots for OCFS2
Document 730332.1 -  How to Backup and Restore OCFS2 File Permissions
Document 1256604.1 - HOWTO Disable OCFS2 Sparse Files
Document 789010.1 -  How to Use "tcpdump" to Log OCFS2 Interconnect (o2net) Messages
Document 1129113.1 - How To Ensure You Have The Correct OCFS2 Driver RPM Package For Your System
Document 761020.1 -  How to Add a New OCFS2 Node to an Online Cluster
Document 1204453.1 - How to reconfigure OCFS2 to use cluster private interconnect
Document 1537596.1 - Steps to determine file and free space fragmentation of OCFS2
Document 1365443.1 - Oracle Vm - How To Update Iscsi Lun And Online Resize Ocfs2 Repository
Document 1313871.1 - Tuning OCFS2 1.6 To Hold Virtual Machine Image Files (-T vmstore)
Document 1352663.1 - How to dynamically resize a SAN disk and OCFS2 volume
Document 445082.1 - How to resize an OCFS2 filesystem
Document 1553162.1 - How to create an OCFS2 Cluster with the Global Heartbeat Feature
Document 1533533.1 - How to create an OCFS22 volume with the global heartbeat feature
Document 413612.1 - How to Change OCFS2 Node Numbers
 
>>> OCFS2 Release Notes:
Document 1223003.1 -  Oracle Cluster File System 2 (OCFS2) 1.6 Release Notes
Document 1222934.1 -  OCFS2 Version 1.6 New Features
Document 742496.1  -  Oracle Cluster File System 2 (OCFS2) 1.4 Release Notes
Document 736230.1 -  OCFS2 Version 1.4 New Features
Document 944816.1   -  Oracle Cluster File System 2 (OCFS2) 1.4.4-1 Release Notes
Document 844277.1   -  Oracle Cluster File System 2 (OCFS2) 1.4.2-1 Release Notes
Document 1086231.1 -  Oracle Cluster File System 2 (OCFS2) 1.4.7-1 Release Notes
Document 567296.1-  Bugs Fixes in OCFS2 1.2.8-2 since 1.2.5-6
 
>>> Support & Certification:
Document 1094223.1 - Does OCFS2 Support Software Raid Devices?
Document 1129890.1 - Support and Software Update Policy for OCFS2 Running on Oracle Linux
Document 1253272.1 - Oracle Cluster File System (OCFS2) Software Support and Update Policy for Red Hat Enterprise Linux Supported by Red Hat
Document 452745.1 - Is OCFS2 Supported For Shared Storage Of The OCAS/OCAD Session Files?
Document 413195.1 - Host-Based Mirroring and OCFS2
Document 421640.1 - OCFS2: Supportability as a general purpose filesystem
Document 1094223.1 - Does OCFS2 Support Software Raid Devices?
Document 432854.1 -  Asynchronous I/O Support on OCFS/OCFS2 and Related Settings: filesystemio_options, disk_asynch_io
Document 797597.1 -  Is the Oracle Cluster File System (OCFS2 for Linux) Certified Against Content Server
Document 566819.1  - Supportability of OCFS2 on Non-certified Linux Distributions
Document  1552510.1 - The OCFS2 Global Heartbeat feature
 
>>> Known Problems:
Document 1084693.1 - OCFS2 Fencing With "Kernel BUG at dlmmaster:2300" In 1.2.9 Or "dlm_drop_lockres_ref:2216 ERROR: while dropping ref" in 1.4
Document 1129192.1 -  rror "__ocfs2_file_aio_write:2251 EXIT: -5" in Syslog
Document 1144404.1 - Systems Crash (OOPS) With 'exception RIP: ocfs2_locking_ast' In "/var/log/messages"
Document 1172943.1 - OCFS2 Does Not Reboot the Node at Network Failure
Document 1223164.1 - OCFS2 Error "ocfs2_orphan_del" "ocfs2_remove_inode" In /var/log/messages
Document 1232702.1 - Write To Ocfs2 Volume gets No Space Error Despite Large Free Space Available
Document 1271517.1 - Ocfs2_initialize_super:1455 Error: Couldn't Mount Because Of Unsupported Optional Features (50)
Document 1274105.1 - Filesystem Lockups / Hangs on OCFS2 Mounts Exported and Mounted via NFS
Document 1275440.1 - Untrustable Inode Usage with "df -i" on OCFS2 File System
Document 1368000.1 - OCFS2: ocfs2_hb_ctl: Could not access heartbeat region semaphore set while starting heartbeat
Document 399931.1 - ocfs2cdsl fails with "is not on an ocfs2 filesystem
Document 406136.1 - Why does message "Kernel: (24556,1):Ocfs2_cdsl_follow_link:372" appear in /var/log/messages ?
Document 734085.1 - Common reasons for OCFS2 o2net Idle Timeout
Document 434255.1 - Common reasons for OCFS2 Kernel Panic or Reboot Issues
Document 461565.1 - OCFS2 (O2CB) fails to loading module "configfs" / ocfs2_nodemanager
Document 428523.1 - "ocfs2console" Works Abnormally on Multipathed Physical Devices
Document 553600.1 - OCFS2 1.2.7-1 Filesystem May Become Unavailable after Node Panic or Eviction
Document 404554.1 - Mounting OCFS2 File System Getting Limited to 4 Nodes
Document 558824.1 - OCFS2: df and du commands display different results
Document 789946.1 - Nodes get rebooted without obvious reason in RAC environment with OCFS2 filesystem
Document 377616.1 - OCFS2 Kernel Panics on SAN Failover
Document 376921.1 - System Crash On Ocfs2_extend_file error causes kernel panic
Document 394827.1 - OCFS2: Network service restart / interconnect down causes panic / reboot of other node
Document 405766.1 - OCFS2: Cluster Node Gets OOPS (NULL pointer dereference) with OCFS2 Unmount
Document 419125.1 - Cleaning heartbeat on ocfs2: Failed At least one heartbeat region still active
Document 431556.1 - OCFS2 mounted.ocfs2 returns 'Unknown: Bad magic number in inode'
Document 470888.1 - ocfs2 fails with "O2CB_CTL: INTERNAL LOGIC FAILURE WHILE ADDING NODE"
Document 472640.1 - Unexpected "df -i" Results On OCFS2 Filesystems
Document 470630.1 - Starting OCFS2 cluster gets segfault in o2cb_ctl application
Document 471814.1 - A Disconnection of Disk Containing OCFS2 Volume Will Restart all OCFS2 Cluster Nodes
Document 469761.1 - OCFS2 errors in message log when deleting files
Document 468923.1 - OCFS2: Disk Space is not Released After Deleting Many Files
Document 565574.1 - How to Fix the IO Errors Reading an Oracle Datafile On an OCFS2 Filesystem.
Document 566353.1 - OCFS2 Fileystem Switches To Readly-Only Mode
Document 844449.1 - Un-mounting OCFS2 1.4.1 File System Generates Ocfs2_hb_ctl Segfault
Document 843479.1 - Error 'o2cb_ctl: Unable to load cluster configuration file /etc/ocfs2/cluster.conf' When Starting OCFS2 Cluster Service by 'o2cb online'
Document 578036.1 - Error 'o2net_check_handshake ...' When Using Public Network Interface for OCFS2
Document 579153.1 - Problem Using Labels On OCFS2
Document 1371783.1 - Data Pump Export (EXPDP) Hangs On OCFS2 Creating A 4 KB Dump File
Document 967423.1 - OCFS2 GET "NO SPACE LEFT ON DEVICE" WHEN CREATING FILE
Document 602546.1 - mount.ocfs2 Fails with "Unknown code B 0"
Document 603310.1 - Latency Issues With CFQ I/O Scheduler Resulting In OCFS2 Node Evictions
Document 727543.1 - ocfs2 subdir limit - ocfs2_mknod:315 ERROR: inode has i_nlink of 32000
Document 604958.1 - OCFS2 Node Fence Caused by Removing the External Network Cable
Document 728268.1 - Message "Mount.ocfs2: Device Name Specified Was Not Found"
Document 605188.1 - Time-Date Stamps Being Reported by 'ls -l' is Inconsistent Across Nodes on OCFS2 File System
Document 730527.1 - OCFS2: ocfs2console fails to add node: "o2cb_ctl: Unable to access cluster service while creating node"
Document 747362.1 - OCFS2 Link Failure With DLM Status DLM_IVLOCKID On InfiniBand Private Interconnect
Document 751762.1 - Cannot Specify OCR Location on OCFS2 During CRS Installation
Document 763869.1 - Agent On Ocfs2 Triggers The Healthcheck Metric With Error: Gim-00090
Document 785470.1 - NFS Write-share on OCFS2-1.2.x Can Cause "Kernel Panic EIP is at ocfs2_meta_lock_update"
Document 781502.1 - Error "mount.ocfs2: Device or resource busy while mounting ..."
Document 785112.1 - mkfs.ocfs2 Fails with Error 'Invalid block number while formatting the slot map'
Document 787682.1 - mount.ocfs2: Unable to access cluster service while trying to join the group In OCFS2 1.4.1
Document 803300.1 - DataPump Export To OCFS2 Volume Fails With Errors ORA-31693 ORA-19502 And ORA-27061
Document 806554.1 - OCFS2 1.4.1 not removing orphaned files after deletion
Document 864928.1 - ocfs2_stackglue not found
Document 864753.1 - File /etc/ocfs2/cluster.conf incorrectly contains localhost entry when Oracle VM HA is enabled
Document 1112326.1 - RMAN Backup / CROSSCHECK to OCFS2 intermittently Fails with Ora-19501, Ora-27072. What are the correct mount options for RMAN backups on OCFS2 ?
Document 1244434.1 - Starting the Database Using srvctl Fails When ORACLE_HOME is Mounted on OCFS2
Document 1264418.1 - Running Script Apreconb.pls Fails With Error 'O/S Message: Invalid argument' On OCFS2 File System
Document 1103305.1 - Guests With Images On OCFS2 Do Not Auto Start At Reboot
Document 1321757.1 - 11gR2 Grid Infrastructure Fails to Start After OS Upgrade or root.sh or rootupgrade.sh Hangs if Voting Disk is on OCFS2
Document 1356906.1 - Database Startup Hangs After OS Upgrades if Files are on OCFS2
Document 1377083.1 - DataPump Export To OCFS2 Fails With ORA-31693 ORA-19502 ORA-27072 File I/O Error
Document 1494300.1 - Creating New Repository fails with error ''Unable to create ocfs2 filesystem '
Document 1485541.1 - Linux: INS-41321 - Invalid oracle cluster register [OCR] Location - if OCFS2 is Selected for OCR
Document 369196.1 - Ocfs2 Causes A Kernel Panic Because Of A Write Timeout On The Shared Storage.
Document 381553.1 - ocfs2 fails with "__ocfs2_downconvert_lock:2328 Error"
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
