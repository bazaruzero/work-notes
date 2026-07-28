<!--
---
title: "OCFS2 Maintenance"
slug: ocfs2-maintenance
created: 2026-07-13
updated: 2026-07-13
author: admin
categories: [oracle, archive, miscellaneous]
tags: [oracle, ocfs2, filesystem, cluster]
pinned: false
description: "How to add and remove OCFS2 cluster nodes: checkup, prepare new node, add to online cluster, correct cluster.conf, umount and stop o2cb, start and mount."
---
-->

# OCFS2 Maintenance

> **ARCHIVED CONTENT**
> The information in this post may no longer be accurate. Always refer to the latest official documentation for current best practices and features.

## Table of Contents

- [Docs](#docs)
- [Add Node](#add-node)
    - [Checkup](#checkup)
    - [Prepare new node](#prepare-new-node)
    - [Add the new node to the online ocfs2 cluster](#add-the-new-node-to-the-online-ocfs2-cluster)
- [Remove Node](#remove-node)
    - [Correct /etc/ocfs2/cluster.conf](#correct-etcocfs2clusterconf)
    - [Umount ocfs2 device and stop o2cb on all nodes](#umount-ocfs2-device-and-stop-o2cb-on-all-nodes)
    - [Start o2cb and mount ocfs2 on all nodes (except removing node)](#start-o2cb-and-mount-ocfs2-on-all-nodes-except-removing-node)

## Docs

- How to Add a New OCFS2 Node to an Online Cluster (Doc ID 761020.1)
- How to Change and Check Number of Slots for OCFS2 (Doc ID 602861.1)
- How to remove an ocfs2 node from a cluster (Doc ID 852002.1)


## Add Node

### Checkup

Check cluster status:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
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
Checking O2CB heartbeat: Active
Debug file system at /sys/kernel/debug: mounted
++++++++++
```

Get the ocfs2 volume partitions:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ mounted.ocfs2 -d
++++++++++
Device     Stack  Cluster  F  UUID                              Label
/dev/sdb1  o2cb               4DFB615236DC45DD8E52B2395DC7C110
++++++++++
```

Check "Max Node Slots" of the current ocfs2 volume:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ echo 'stats -h' | debugfs.ocfs2 /dev/sdb1
++++++++++
debugfs.ocfs2 1.8.6
debugfs: stats -h
        Revision: 0.90
        Mount Count: 0   Max Mount Count: 20
        State: 0   Errors: 0
        Check Interval: 0   Last Check:
        Creator OS: 0
        Feature Compat: 3 backup-super strict-journal-super
        Feature Incompat: 14160 sparse extended-slotmap inline-data xattr indexed-dirs refcount discontig-bg
        Tunefs Incomplete: 0
        Feature RO compat: 1 unwritten
        Root Blknum: 5   System Dir Blknum: 6
        First Cluster Group Blknum: 3
        Block Size Bits: 12   Cluster Size Bits: 12
        Max Node Slots: 4 <<<<<<<<<<<<<<<<<<<<<<<<<<<<< Okay
        Extended Attributes Inline Size: 256
        Label:
        UUID: 4DFB615236DC45DD8E52B2395DC7C110
        Hash: 3754404690 (0xdfc7ab52)
        DX Seeds: 2330031485 1113073678 3429088798 (0x8ae1757d 0x4258280e 0xcc63be1e)
        Cluster stack: classic o2cb
        Cluster flags: 0
debugfs:
++++++++++
```

> **NOTE:** The number of max node slots specifies the number of nodes that can concurrently mount the volume. This number is specified during format and can be increased using tunefs.ocfs2. If "Max Node Slots" should be corrected you can refer to note: *How to Change and Check Number of Slots for OCFS2 (Doc ID 602861.1)*.

Check /etc/ocfs2/cluster.conf on the online nodes:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
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

> **NOTE:** Make sure that only the online nodes are in the configuration file /etc/ocfs2/cluster.conf. Please notice that the new added node "srv-ocfs2-node3" should not be in the configuration file /etc/ocfs2/cluster.conf. This is because the o2cb_ctl utility will add, but does not check if it is already present.

Check the in-memory filesystems configfs:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ ls -l /sys/kernel/config/cluster/*/node
++++++++++
drwxr-xr-x. 2 root root 0 Jan  7 13:14 srv-ocfs2-node1.oracle.com
drwxr-xr-x. 2 root root 0 Jan  7 13:14 srv-ocfs2-node2.oracle.com
++++++++++
```

> **NOTE:** configfs is mounted at /sys/kernel/config, instead of /config on EL5.

### Prepare new node

OCFS2 packages check/install:

```
>>> root@srv-ocfs2-node3
 
$ yum install -y ocfs2*
$ yum list installed | grep -i ocfs2
++++++++++
ocfs2-tools.x86_64                 1.8.6-11.el6               @public_ol6_latest
ocfs2-tools-devel.x86_64           1.8.6-11.el6               @public_ol6_latest
++++++++++
 
$ chkconfig ocfs2 on
```

Modify VM config file:

```
D:\VM\srv-ocfs2-node3\srv-ocfs2-node3.vmx
```

Add to the end of config file:

```
disk.locking = "FALSE"
diskLib.dataCacheMaxSize = "0"
diskLib.dataCacheMaxReadAheadSize = "0" 
diskLib.dataCacheMinReadAheadSize = "0" 
diskLib.dataCachePageSize = "4096" 
diskLib.maxUnsyncedWrites = "0" 
scsi1.sharedBus = "virtual"
```

Add disk to VM as already existing disk and "scan" with fdisk:

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
$ lsblk
```

Create OCFS2 directory:

```
$ mkdir -p /etc/ocfs2
```

### Add the new node to the online ocfs2 cluster

Run command o2cb_ctl to add the node "srv-ocfs2-node3" to the online ocfs2 cluster:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ o2cb_ctl -C -i -n srv-ocfs2-node3.oracle.com -t node -a number=3 -a ip_address=192.168.197.167 -a ip_port=7777 -a cluster=testCluster
++++++++++
Node srv-ocfs2-node3 created
++++++++++
```

Check the in-memory filesystems configfs to see if new node has been added:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ ls -l /sys/kernel/config/cluster/*/node
++++++++++
drwxr-xr-x. 2 root root 0 Jan  7 13:13 srv-ocfs2-node1.oracle.com
drwxr-xr-x. 2 root root 0 Jan  7 13:04 srv-ocfs2-node2.oracle.com
drwxr-xr-x. 2 root root 0 Jan  7 13:20 srv-ocfs2-node3
++++++++++
```

Copy config files to new node:

```
>>> root@srv-ocfs2-node1
 
$ scp /etc/ocfs2/cluster.conf root@srv-ocfs2-node3:/root/cluster.conf
$ scp /etc/sysconfig/o2cb root@srv-ocfs2-node3:/root/o2cb
 
>>> root@srv-ocfs2-node3
 
$ cp /etc/ocfs2/cluster.conf /etc/ocfs2/cluster.conf.back
$ cp /root/cluster.conf /etc/ocfs2/cluster.conf
$ cp /etc/sysconfig/o2cb /etc/sysconfig/o2cb.conf.back
$ cp /root/o2cb /etc/sysconfig/o2cb
```

Start o2cb service on new node:

```
>>> root@srv-ocfs2-node3
 
$ /etc/init.d/o2cb start
++++++++++
checking debugfs...
Loading stack plugin "o2cb": OK
Loading filesystem "ocfs2_dlmfs": OK
Creating directory '/dlm': OK
Mounting ocfs2_dlmfs filesystem at /dlm: OK
Setting cluster stack "o2cb": OK
Registering O2CB cluster "testCluster": OK
Setting O2CB cluster timeouts : OK
++++++++++
 
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
 
$ lsmod | grep -i ocfs2
++++++++++
ocfs2_dlmfs            28672  1
ocfs2_stack_o2cb       16384  0
ocfs2_dlm             241664  1 ocfs2_stack_o2cb
ocfs2_nodemanager     245760  11 ocfs2_dlmfs,ocfs2_stack_o2cb,ocfs2_dlm
ocfs2_stackglue        20480  2 ocfs2_dlmfs,ocfs2_stack_o2cb
configfs               36864  3 ocfs2_nodemanager,target_core_mod
++++++++++
```

Mount and update "/etc/fstab":

```
>>> root@srv-ocfs2-node3
 
$ mkdir -p /u01
$ mount -t ocfs2 /dev/sdb1 /u01
$ cat /etc/fstab
++++++++++
/dev/sdb1 /u01 ocfs2 _netdev,defaults 0 0
++++++++++
```


## Remove Node

Try to remove online:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ o2cb_ctl -D -n srv-ocfs2-node3 -u
++++++++++
o2cb_ctl: Not yet supported
++++++++++
```

> **NOTE:** it is impossible to remove an ocfs2 nodes from an on-line ocfs2 cluster with current version of ocfs2 and o2cb_ctl included in ocfs2-tools. **Stop all applications which use OCFS2 volume on all ocfs2 nodes**.

### Correct /etc/ocfs2/cluster.conf

Delete the description of the removing node from /etc/ocfs2/cluster.conf of all ocfs2 nodes:

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ cat /etc/ocfs2/cluster.conf
++++++++++
cluster:
        heartbeat_mode = local
        node_count = 2      <<<<<<<<<<<<<<<<<<<< Don't forget to correct it too
        name = testCluster
  
node:
        number = 1
        cluster = testCluster
        ip_port = 7777
        ip_address = 192.168.197.165
        name = srv-ocfs2-node1.oracle.com
  
node:
        number = 2
        cluster = testCluster
        ip_port = 7777
        ip_address = 192.168.197.166
        name = srv-ocfs2-node2.oracle.com
++++++++++
```

> **NOTE:** You also need to configure "number =" for other nodes, and "node_count =" in cluster section appropriately. /etc/ocfs2/cluster.conf on all ocfs2 nodes must be same, no differences are allowed.

### Umount ocfs2 device and stop o2cb on all nodes

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2 / srv-ocfs2-node3
 
$ umount /u01
$ /etc/init.d/o2cb offline testCluster
++++++++++
Clean userdlm domains: OK
Stopping O2CB cluster testCluster: Unregistering O2CB cluster "testCluster": OK
Unloading module "ocfs2": OK
++++++++++
 
$ /etc/init.d/o2cb unload
++++++++++
Clean userdlm domains: OK
Unmounting ocfs2_dlmfs filesystem: OK
Unloading module "ocfs2_dlmfs": OK
Unloading module "ocfs2_stack_o2cb": OK
/etc/init.d/o2cb: line 1151: read: read error: 0: No such device
++++++++++
```

### Start o2cb and mount ocfs2 on all nodes (except removing node)

```
>>> root@srv-ocfs2-node1 / srv-ocfs2-node2
 
$ /etc/init.d/o2cb load
++++++++++
checking debugfs...
Loading stack plugin "o2cb": OK
Loading filesystem "ocfs2_dlmfs": OK
Mounting ocfs2_dlmfs filesystem at /dlm: OK
++++++++++
 
$ /etc/init.d/o2cb online testCluster
++++++++++
checking debugfs...
Setting cluster stack "o2cb": OK
Registering O2CB cluster "testCluster": OK
Setting O2CB cluster timeouts : OK
++++++++++
 
$ mount /u01
$ ls -l /sys/kernel/config/cluster/*/node
++++++++++
drwxr-xr-x. 2 root root 0 Jan  8 18:16 srv-ocfs2-node1.oracle.com
drwxr-xr-x. 2 root root 0 Jan  8 18:16 srv-ocfs2-node2.oracle.com
++++++++++
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
