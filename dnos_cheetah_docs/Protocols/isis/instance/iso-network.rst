protocols isis instance iso-network
-----------------------------------

**Minimum user role:** operator

In an IS-IS network topology, the routing domain may be divided into multiple subdomains referred to as areas. Each area is assigned an area address. The network entity title (NET) serves as the area address and must be configured in order for IS-IS to work. The ISO-network address is composed of three primary parts:
  - **Area**: the area ID field of variable length from minimum 1 byte to maximum 13 bytes. It may comprise the following sub-parts:
  - Authority and Format Identifier (AFI): identifies the authority which dictates the format of the address.
  - Initial Domain Identifier (IDI): identifies the organization belonging to the AFI.
  - High Order Domain-Specific Part (HODSP): the IS-IS area number within the AS.
  - **System ID**: 6 bytes identifying the node (i.e. router) on the network. Must be identical for all IS-IS instances.
  - **Network Selector** (NSEL): a 1 byte field identifying the network layer service to which a packet should be sent. This field must always be set to 00, indicating that no transport information is carried.

To configure the NET address for an IS-IS instance:


**Command syntax: iso-network [network]** [, network, network]

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- An IS-IS instance may be assigned up to 3 NET addresses. This is useful when merging or splitting areas in the domain. Once the merge or split is complete, there is no need for multiple NET addresses.

- Network must be configured for IS-IS.

- You can configure up to 3 different networks under a single IS-IS instance.

- System-id must be identical for all networks in the same IS-IS instance and for all IS-IS instances.

- The network entity title used for the IS-IS   instance in hexadecimal, as described above. When configuring multiple NETs,   the system ID must be identical in all**Parameter table**

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| network   | The network entity title used for the IS-IS instance in hexadecimal, as          | \-    | \-      |
|           | described above. When configuring multiple NETs, the system ID must be identical |       |         |
|           | in all NETs.                                                                     |       |         |
|           | You must configure a network for IS-IS.                                          |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# iso-network 50.0001.0100.0070.1A45.00

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# iso-network 50.0001.F100.0070.1A45.00, 50.0002.F100.0070.1A45.00


**Removing Configuration**

To remove all NET values:
::

    dnRouter(cfg-protocols-isis-inst)# no iso-network

To remove a specific NET value:
::

    dnRouter(cfg-protocols-isis-inst)# no iso-network 50.0001.F100.0070.1A45.00

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 6.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 9.0     | Changed "net" argument to "iso-network" in syntax   |
+---------+-----------------------------------------------------+
| 10.0    | System ID must be identical for all IS-IS instances |
+---------+-----------------------------------------------------+
