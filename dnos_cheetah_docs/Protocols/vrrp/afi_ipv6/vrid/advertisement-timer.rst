protocols vrrp interface address-family ipv6 vrid advertisement-timer
---------------------------------------------------------------------

**Minimum user role:** operator

To set the VRRP announcemenets advertiseement timer value for the VRRP group:

**Command syntax: advertisement-timer [advertisement-interval] [units]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv6 vrid
- network-services vrf instance protocols vrrp interface address-family ipv6 vrid

**Parameter table**

+------------------------+----------------------------------------------------------+------------------+--------------+
| Parameter              | Description                                              | Range            | Default      |
+========================+==========================================================+==================+==============+
| advertisement-interval | Sets the interval between successive VRRP advertisements | 10-40950         | 1000         |
+------------------------+----------------------------------------------------------+------------------+--------------+
| units                  |                                                          | | milliseconds   | milliseconds |
|                        |                                                          | | centiseconds   |              |
|                        |                                                          | | seconds        |              |
+------------------------+----------------------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# advertisement-timer 5 seconds


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no advertisement-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
