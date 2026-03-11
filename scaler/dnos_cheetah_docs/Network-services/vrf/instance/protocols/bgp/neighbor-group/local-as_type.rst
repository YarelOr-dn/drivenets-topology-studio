network-services vrf instance protocols bgp neighbor-group local-as
-------------------------------------------------------------------

**Minimum user role:** operator

If, for whatever reason, you need to change the AS number of your network, you will need to reconfigure the AS number on all the BGP peers. By specifying an alternate AS for this BGP process when interacting with the specified peer, you allow the peer to appear to simultaneously belong to both the former AS and the new AS, without changing the peering arrangements.

To configure a local AS number for the neighbor:

**Command syntax: local-as [local-as-number]** type [as-path-prepend-type]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor

**Note**

- This command is relevant to BGP peers only.

- The configuration will reset the BGP session.

- The local-as-number must be different from the router AS.

- When changing the local-as-number, the as-path-prepend-type will return to the default value.

- When the local-as-number is identical to the neighbor AS, you cannot configure the as-path-prepend-type

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| Parameter            | Description                                                                      | Range                     | Default |
+======================+==================================================================================+===========================+=========+
| local-as-number      | as-number for peer session, must be different from local-AS and peer-AS          | 1-4294967295              | \-      |
+----------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| as-path-prepend-type | prepend type for as-path when adding local-as perpend - default config. prepend  | | prepend                 | prepend |
|                      | the local-as as well as the bgp as-n no-perpend - the supplied local-as is not   | | no-prepend              |         |
|                      | prepended to the received as-path no-prepend-replace-as - only the supplied      | | no-prepend-replace-as   |         |
|                      | local-as is prepended to the as-path when transmitting local-route updates to    |                           |         |
|                      | this peer                                                                        |                           |         |
+----------------------+----------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# local-as 1000

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# local-as 1000 type no-prepend

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# local-as 1000 type no-prepend-replace-as

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# remote-as 8000
    dnRouter(cfg-protocols-bgp-neighbor)# local-as 8000

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 65001
    dnRouter(cfg-protocols-bgp-group)# local-as 65001


**Removing Configuration**

To delete the local AS configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no local-as

::

    dnRouter(cfg-protocols-bgp-group)# no local-as

**Command History**

+---------+---------------------------------+
| Release | Modification                    |
+=========+=================================+
| 6.0     | Command introduced              |
+---------+---------------------------------+
| 11.0    | Removed "type" from the syntax. |
+---------+---------------------------------+
