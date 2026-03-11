network-services evpn instance interface df-invert-preference
-------------------------------------------------------------

**Minimum user role:** operator

While the Designated Forwarder Election Algorithm is defined under multihoming, and the Prefernce Algorithm (Highest or Lowest) is defined, this knob allows that per EVI this can be inverted to allow the DF role to be shared between two PE devices for the different service instances.

**Command syntax: df-invert-preference [invert-preference-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance interface

**Parameter table**

+-----------------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter                   | Description                                                                      | Range        | Default  |
+=============================+==================================================================================+==============+==========+
| invert-preference-algorithm | When the AC interface is connected to a multihomed Ethernet Segment and the DF   | | enabled    | disabled |
|                             | Election algorithm is the preference algorithm (highest or lowest) then enabling | | disabled   |          |
|                             | this knob will invert the algorithm for this EVPN instance, example instead of   |              |          |
|                             | highest election it will elect the lowest preference as the DF                   |              |          |
+-----------------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-evpn-inst-ge100-0/0/0)# df-invert-preference enabled
    dnRouter(cfg-evpn-inst-ge100-0/0/0)#


**Removing Configuration**

To revert df-invert-preference to disabled.
::

    dnRouter(cfg-evpn-inst-ge100-0/0/0)# no df-invert-preference

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
