protocols bgp confederation identifier
--------------------------------------

**Minimum user role:** operator

Because iBGP updates are not passed to other iBGP neighbors, every router within the BGP AS must be fully meshed. In large ASs, the number of iBGP peering sessions required can potentially be enormous. The use of confederations reduces the number of iBGP sessions by allowing to split the AS into smaller sub-ASs.

The AS_PATH attribute within routing updates includes the confederation information. To the outside world (i.e. to BGP peers external to the confederation), your network confederation identified by the AS Confederation Identifier appears as a single AS.

On each router in the AS, you define the confederation identifier and its confederation sub-AS. This breaks up the larger AS into smaller sub-ASs. To enable the confederation sub-ASs to communicate, you need to define the confederation neighbors on each sub-AS border router (see "bgp confederation neighbors").

**Command syntax: confederation identifier [identifier]**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- This command is available to the default VRF instance only.

**Parameter table**

+------------+------------------------------+--------------+---------+
| Parameter  | Description                  | Range        | Default |
+============+==============================+==============+=========+
| identifier | bgp confederation identifier | 1-4294967295 | \-      |
+------------+------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# confederation identifier 8000


**Removing Configuration**

To remove the confederation configuration:
::

    dnRouter(cfg-protocols-bgp)# no confederation identifier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
