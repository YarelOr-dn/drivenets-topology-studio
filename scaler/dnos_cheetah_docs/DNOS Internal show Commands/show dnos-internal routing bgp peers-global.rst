show dnos-internal routing bgp peers-global
-------------------------------------------

**Minimum user role:** viewer

Displays a list of peers with their bgp instance number and vrf name.
In the event that the bgp instance they belong to is being deleted, the peer will be marked as deleting.


**Command syntax: show dnos-internal routing bgp peers-global**

**Command mode:** operational



.. **Note**


**Parameter table**


**Example**
::

	dnRouter# show dnos-internal routing bgp peers-global
    neighbor Static announcement: BGP default inst-id 1
    neighbor 9.9.9.4: BGP default inst-id 1
    neighbor Static announcement: BGP vpn_a inst-id 2
    neighbor 173.0.1.1: BGP vpn_a inst-id 2
    neighbor Static announcement: BGP vpn_c inst-id 3
    neighbor 173.0.5.1: BGP vpn_c inst-id 3
    neighbor Static announcement: BGP vpn_aa inst-id 4
    neighbor 1741::1: BGP vpn_aa inst-id 4
    neighbor Static announcement: BGP vpn_cc inst-id 5 (deleting)
    neighbor 1745::1: BGP vpn_cc inst-id 5 (deleting)


.. **Help line:** Displays internal bgp peers-global information

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
