protocols bgp neighbor bfd admin-state
--------------------------------------

**Minimum user role:** operator

Enable BFD session for BGP session protection and enter BFD configuration level to configure BFD session settings.

To change the BFD administrative state for a specific BGP neighbor:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor bfd
- protocols bgp neighbor-group bfd
- protocols bgp neighbor-group neighbor bfd
- network-services vrf instance protocols bgp neighbor bfd
- network-services vrf instance protocols bgp neighbor-group bfd
- network-services vrf instance protocols bgp neighbor-group neighbor bfd

**Note**

- In the event that there are multiple BFD clients registered to the same BFD session, a single BFD session is established with the strictest session parameters between all clients.

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | set whether bfd protection is in use | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)# admin-state enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# admin-state enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# admin-state enabled
    dnRouter(cfg-bgp-group-bfd)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)# admin-state enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-bgp-neighbor-bfd)# no admin-state

::

    dnRouter(cfg-bgp-group-bfd)# no admin-state

::

    dnRouter(cfg-bgp-neighbor-bfd)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
