protocols isis instance address-family ipv6-unicast fast-reroute backup-candidate
---------------------------------------------------------------------------------

**Minimum user role:** operator

By default, all IS-IS enabled interfaces are valid candidates for IS-IS LFA. The command allows you to include or exclude an interface from being used as a candidate for repair path calculation. When set to be included, the interface will be used for loop-free alternate calculations (when isis fast-reroute is globally enabled. See "isis instance address-family fast-reroute"). If the interface is set to be excluded, it will not be used for repair paths:


**Command syntax: fast-reroute backup-candidate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**
- The configuration is only valid for the following interface types:
.. - ge{/10/25/40/100}-X/Y/Z,
.. - geX-<f>/<n>/<p>.<sub-interface id>
.. - bundle-<bundle-id>,
.. - bundle-<bundle-id.sub-bundle-id>
- for other interfaces type require commit validation and that cli will not support such command for these interfaces
- The default behavior is per 'isis instance address-family fast-reroute backup-candidate' configuration
- Inheritance logic:
.. - Interface per level config - inherit the interface level-1-2 config (i.e when level isn't specified)
.. - Interface level-1-2 config - inherits the global fast-reroute backup-candidate (which always exists, can be default)
.. - 'backup-candidate' applies per IS-IS interface address-family topology. For example, when operating in a single topology, if you disable the backup-candidate on an ipv4-unicast interface, the LFA to the interface's neighbor will not be valid for both IPv4 & IPv6 prefixes.


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state for including or excluding the interface from being     | | enabled    | enabled |
|             | used for repair paths see "Inheritance logic" under notes                        | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# fast-reroute backup-candidate disabled

    dnRouter(cfg-protocols-isis-inst)# interface bundle-3
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# fast-reroute backup-candidate level level-2 enabled


**Removing Configuration**

To revert to the default admin-state and to the default level:
::

    dnRouter(cfg-inst-if-afi)# no fast-reroute backup-candidate

To revert only to the default level:
::

    dnRouter(cfg-inst-if-afi)# no fast-reroute backup-candidate level level-2 enabled
    dnRouter(cfg-inst-if-afi)# no fast-reroute backup-candidate enabled
    dnRouter(cfg-inst-if-afi)# no fast-reroute backup-candidate level level-2

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
