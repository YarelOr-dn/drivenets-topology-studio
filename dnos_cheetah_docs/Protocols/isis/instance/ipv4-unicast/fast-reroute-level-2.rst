protocols isis instance address-family ipv4-unicast fast-reroute level level-2
------------------------------------------------------------------------------

**Minimum user role:** operator

The command is responsible for inserting a backup route per IS-IS prefix in the RIB and FIB. Therefore, if a primary path fails, the pre-installed backup path will be used to forward traffic. The backup path will be used as follows (by priority):

#.	Default node protection is preferred over link protection, thus skipping a potential damaged node and forwarding the traffic to the next-hop rather than skipping a potential damaged link.

#.	The path with the lowest metric.

#.	The path with the lowest hop count.

To define the administrative state of fast reroute per IS-IS instance:


**Command syntax: fast-reroute level level-2 [admin-state]** remote-lfa

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**
- Inheritance logic:
.. - If level not specified, configure for level-1-2 and apply as default behavior for any specific level
.. - If level specified, apply configuration for that level only


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state for including or excluding the interface from being     | | enabled    | \-      |
|             | used for repair paths see "Inheritance logic" under notes                        | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+
| remote-lfa  | When specified, support remote lfa protection using LDP lsp.                     | boolean      | \-      |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute enabled
    dnRouter(cfg-isis-inst-afi)# exit
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute level level-1 enabled

    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute enabled remote-lfa


**Removing Configuration**

To revert to the default admin-state and level:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute

To revert to the default fast-reroute admin-state for a specific level:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute level level-1

To revert to usage of remote lfa:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute remote-lfa

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 13.0    | Command introduced          |
+---------+-----------------------------+
| 14.0    | Added support for level-1-2 |
+---------+-----------------------------+
| 15.0    | Updated command syntax      |
+---------+-----------------------------+
| 17.1    | Add remote LFA option       |
+---------+-----------------------------+
