protocols vrrp interface address-family ipv4 vrid accept-mode admin-state
-------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable accept mode for the VRRP group:

**Command syntax: accept-mode admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv4 vrid
- network-services vrf instance protocols vrrp interface address-family ipv4 vrid

**Note**
Enables a backup VRRP device to respond to ping, traceroute, and Telnet packets if the backup device becomes the master VRRP router.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Controls whether a virtual router in master state will accept packets addressed  | | enabled    | disabled |
|             | to the address owner's IPvX address as its own if it is not the IPvX address     | | disabled   |          |
|             | owner.  The default is 'false'.  Deployments that rely on, for example, pinging  |              |          |
|             | the address owner's IPvX address may wish to configure accept-mode to 'true'.    |              |          |
|             | Note: IPv6 Neighbor Solicitations and Neighbor Advertisements MUST NOT be        |              |          |
|             | dropped when accept-mode is 'false'.                                             |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# accept-mode admin-state enabled


**Removing Configuration**

To return the accept-mode admin-state to its default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no accept-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
