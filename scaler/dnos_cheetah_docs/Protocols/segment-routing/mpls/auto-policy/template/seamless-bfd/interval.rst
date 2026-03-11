protocols segment-routing mpls auto-policy template color seamless-bfd interval
-------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the interval value for the S-BFD session.

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color seamless-bfd

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# seamless-bfd
    dnRouter(cfg-auto-policy-color-3-sbfd)# interval 6


**Removing Configuration**

To remove the interval and return to its default value:
::

    dnRouter(cfg-auto-policy-color-3-sbfd) no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
