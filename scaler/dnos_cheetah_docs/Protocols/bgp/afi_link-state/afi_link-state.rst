protocols bgp address-family link-state
---------------------------------------

**Minimum user role:** operator

To enter global BGP link-state address-family configuration:

**Command syntax: address-family link-state**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family link-state
    dnRouter(cfg-protocols-bgp-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp)# no address-family link-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
