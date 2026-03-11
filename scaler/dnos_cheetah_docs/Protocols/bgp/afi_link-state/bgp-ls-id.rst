protocols bgp address-family link-state bgp-ls-id
-------------------------------------------------

**Minimum user role:** operator

Set the desired BGP-ls identifier to be sent for NODE/LINK/PREFIX link-state updates under sub-tlv 513 (per RFC 7752).
By default, BGP will set its own router-id.

**Command syntax: bgp-ls-id [bgp-ls-id]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family link-state

**Note**

- Expectation that all BGP speakers advertising the same IGP TE topology will be configured with the same bgp-ls-id

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| bgp-ls-id | bgp link-state identifier. Together with bgp as-number , define the link-state   | A.B.C.D | \-      |
|           | IGP domain. Per RFC7752                                                          |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family link-state
    dnRouter(cfg-protocols-bgp-afi)# bgp-ls-id 65000


**Removing Configuration**

To revert bgp-ls-id to default behavior:
::

    dnRouter(cfg-protocols-bgp-afi)# no bgp-ls-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
