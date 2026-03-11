routing-options load-balancing mpls-speculative-parsing post-stack-first-nibble-of-zero
---------------------------------------------------------------------------------------

**Minimum user role:** operator

At P Routers, when a Control-Word is sent on the packet only the label stack is used to create the load balancing keys and therefore in the absence of a FAT or Entropy Label, load balancing is not achieved. 
Configure mpls-speculative-parsing behavior for case of post-stack-first-nibble is value of 0x0 in order to speculate mpls payload as control-word with ethernet frame
As a result flow parameters from ethernet frame will be taken for load-balancing consideration
To configure post-stack-first-nibble-of-zero:

**Command syntax: post-stack-first-nibble-of-zero [post-stack-first-nibble-of-zero]**

**Command mode:** config

**Hierarchies**

- routing-options load-balancing mpls-speculative-parsing

**Note**
- The configuration is relevant for BRCM based platforms only
- Behavior applies on all NCPs in the cluster (and all units per NCP). Including new enabled NCPs
- Reconfiguration under traffic may lead to  temporary traffic corruption. Operator is advised to reconfigure only when cluster is not forwarding in-band traffic

**Parameter table**

+---------------------------------+----------------------------------------------------------------+--------------------+----------------+
| Parameter                       | Description                                                    | Range              | Default        |
+=================================+================================================================+====================+================+
| post-stack-first-nibble-of-zero | Define how to inyterpret the first nibble after the mpls stack | | no-speculation   | no-speculation |
|                                 |                                                                | | speculate-cw     |                |
+---------------------------------+----------------------------------------------------------------+--------------------+----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# load-balancing
    dnRouter(cfg-routing-options-lb)# mpls-speculative-parsing
    dnRouter(cfg-routing-options-lb-msp)# post-stack-first-nibble-of-zero speculate-cw


**Removing Configuration**

To revert all post-stack-first-nibble-of-zero configuration to default value:
::

    dnRouter(cfg-routing-options-lb-msp)# no post-stack-first-nibble-of-zero

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
