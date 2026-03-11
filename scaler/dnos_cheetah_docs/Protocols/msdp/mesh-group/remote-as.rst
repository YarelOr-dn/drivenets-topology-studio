protocols msdp mesh-group remote-as
-----------------------------------

**Minimum user role:** operator

You can use the following command to set the number of the MSDP mesh-group remote-as. The remote-as is only used as a reference number.

**Command syntax: remote-as [remote-as]**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group

**Note**
- The remote-as parameter is only used for presentation and is not used for any practical purpose.

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
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# remote-as 5000


**Removing Configuration**

To remove the remote-as number:
::

    dnRouter(cfg-protocols-msdp-group)# no remote-as

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
