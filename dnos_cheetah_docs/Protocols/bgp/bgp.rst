protocols bgp
-------------

**Minimum user role:** operator

To start the BGP process:

**Command syntax: bgp [as-number]**

**Command mode:** config

**Hierarchies**

- protocols
- network-services vrf instance protocols

**Note**

- The AS-number cannot be changed. To change it, you need to delete the BGP protocol configuration and configure a new process with a different AS-number.

- Notice the change in prompt.

**Parameter table**

+-----------+------------------------+--------------+---------+
| Parameter | Description            | Range        | Default |
+===========+========================+==============+=========+
| as-number | peer-group unique name | 1-4294967295 | \-      |
+-----------+------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)#


**Removing Configuration**

To disable the BGP process:
::

    dnRouter(cfg-protocols)# no bgp

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 6.0     | Command introduced                   |
+---------+--------------------------------------+
| 9.0     | Changed AS-number range to minimum 1 |
+---------+--------------------------------------+
