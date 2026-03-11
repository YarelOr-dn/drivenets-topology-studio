protocols rsvp auto-mesh tunnel-template
----------------------------------------

**Minimum user role:** operator

To create a new auto-mesh tunnel template and enter the template's configuration mode:

**Command syntax: tunnel-template [tunnel-template]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh

**Note**
- Removing a tunnel-template will remove all tunnels that were created according to that template.

.. - default system behavior is auto-mesh disabled

**Parameter table**

+-----------------+---------------+------------------+---------+
| Parameter       | Description   | Range            | Default |
+=================+===============+==================+=========+
| tunnel-template | template name | | string         | \-      |
|                 |               | | length 1-255   |         |
+-----------------+---------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# description "auto tunnel test template"
    dnRouter(cfg-rsvp-auto-mesh-temp)# destination-address prefix-list IPv4_CORE
    dnRouter(cfg-rsvp-auto-mesh-temp)# primary
    dnRouter(cfg-auto-mesh-temp-primary)# bandwidth 900 mbps
    dnRouter(cfg-auto-mesh-temp-primary)# admin-group include-any RED, GREEN
    dnRouter(cfg-auto-mesh-temp-primary)# priority setup 5 hold 5


**Removing Configuration**

To remove a specific template:
::

    dnRouter(cfg-protocols-rsvp-auto-mesh)# no tunnel-template TEMP_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
