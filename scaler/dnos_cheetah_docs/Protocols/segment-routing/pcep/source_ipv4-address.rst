protocols segment-routing pcep source ipv4-address
--------------------------------------------------

**Minimum user role:** operator

To configure the PCEP source (either an IPv4 address or an interface):

**Command syntax: source ipv4-address [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Parameter table**

+--------------+---------------------+---------+---------+
| Parameter    | Description         | Range   | Default |
+==============+=====================+=========+=========+
| ipv4-address | ipv4 source address | A.B.C.D | \-      |
+--------------+---------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# source ipv4-address 2.2.2.2


**Removing Configuration**

To revert to the default source address (the MPLS TE router-id):
::

    dnRouter(cfg-protocols-sr-pcep)# no source

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
