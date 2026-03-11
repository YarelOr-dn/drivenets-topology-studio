protocols mpls traffic-engineering ipv6-router-id
-------------------------------------------------

**Minimum user role:** operator

Set the desired lo interface from which the global ipv6 address will be used as an ipv6-te-router-id.

**Command syntax: ipv6-router-id [ipv6-router-id]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- If not set, the default ipv6-router-id will be per the highest IPv6 address from any active loopback interface in the default VRF.

**Parameter table**

+----------------+----------------------------------------------------------------------+----------+---------+
| Parameter      | Description                                                          | Range    | Default |
+================+======================================================================+==========+=========+
| ipv6-router-id | IPv6 Router id of the router to be used for IPv6 traffic engineering | X:X::X:X | \-      |
+----------------+----------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# ipv6-router-id 1717:1717::1


**Removing Configuration**

To revert ipv6-router-id to default value:
::

    dnRouter(cfg-protocols-mpls-te)# no ipv6-router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
