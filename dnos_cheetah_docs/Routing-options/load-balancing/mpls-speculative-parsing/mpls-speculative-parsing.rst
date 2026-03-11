routing-options load-balancing mpls-speculative-parsing
-------------------------------------------------------

**Minimum user role:** operator

Enter the mpls-speculative-parsing configuration:

**Command syntax: mpls-speculative-parsing**

**Command mode:** config

**Hierarchies**

- routing-options load-balancing

**Note**

- The configuration is relevant for BRCM based platforms only

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# load-balancing
    dnRouter(cfg-routing-options-lb)# mpls-speculative-parsing
    dnRouter(cfg-routing-options-lb-msp)#


**Removing Configuration**

To revert all mpls-speculative-parsing configuration to its default value:
::

    dnRouter(cfg-routing-options-lb)# no mpls-speculative-parsing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
