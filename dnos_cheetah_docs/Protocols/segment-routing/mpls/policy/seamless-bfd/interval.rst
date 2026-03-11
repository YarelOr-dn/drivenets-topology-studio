protocols segment-routing mpls policy seamless-bfd interval
-----------------------------------------------------------

**Minimum user role:** operator

Configure the interval value for the S-BFD session.

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy seamless-bfd

**Parameter table**

+-----------+---------------------------------------------------+--------+---------+
| Parameter | Description                                       | Range  | Default |
+===========+===================================================+========+=========+
| interval  | set desired interval (msec) for the S-BFD session | 5-1700 | 300     |
+-----------+---------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# interval 6
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To remove the interval and return to its default value:
::

    dnRouter(cfg-mpls-policy-sbfd) no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
