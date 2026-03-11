protocols msdp default-peer remote-as
-------------------------------------

**Minimum user role:** operator

You can use the following command to set the number of the MSDP default-peer remote-as. The remote-as is only used as a reference number.

**Command syntax: remote-as [remote-as]**

**Command mode:** config

**Hierarchies**

- protocols msdp default-peer

**Note**
- The remote-as parameter is only used for presentation and not for any practical purpose.

- There is no default value for remote-as.

**Parameter table**

+-----------+------------------------+--------------+---------+
| Parameter | Description            | Range        | Default |
+===========+========================+==============+=========+
| remote-as | AS number of the peer. | 1-4294967295 | \-      |
+-----------+------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# remote-as 5000


**Removing Configuration**

To remove the remote-as number:
::

    dnRouter(cfg-protocols-msdp-default-peer)# no remote-as

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
