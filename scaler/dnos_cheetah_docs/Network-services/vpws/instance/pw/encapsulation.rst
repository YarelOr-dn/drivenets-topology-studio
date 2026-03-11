network-services vpws instance pw encapsulation
-----------------------------------------------

**Minimum user role:** operator

The Pseudowire encapsulation type by default matches the VPWS interface. The encapsulation type must be equal between neighbors for the Pseudowire to be established, if the ignore-encapsulation-mismatch parameter is disabled. The encapsulation types are:
- Type 5 - Ethernet (Raw) encapsulation
- Type 4 - Vlan (Raw) encapsulation

Default values for VPWS interface:
- For physical interfaces (either GE or bundle) the encapsulation type is Ethernet, and you cannot change the encapsulation type.
- For sub-interfaces the encapsulation type is VLAN.

To configure the Pseudowire encapsulation type:

**Command syntax: encapsulation [encapsulation]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+---------------+---------------------------+--------------+---------+
| Parameter     | Description               | Range        | Default |
+===============+===========================+==============+=========+
| encapsulation | Set PW encapsulation type | | ethernet   | \-      |
|               |                           | | vlan       |         |
+---------------+---------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# interface bundle-1.1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# encapsulation ethernet


**Removing Configuration**

To revert encapsulation to default:
::

    dnRouter(cfg-vpws-inst-pw)# no encapsulation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
