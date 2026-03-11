services port-mirroring session source-interface
------------------------------------------------

**Minimum user role:** operator

You can configure the source interfaces for a specific port-mirroring session. There are some limitations to the configuration.

-	When a session is not designated as a mirror-on-drop session.

-	Up to 10 source interfaces can be monitored in a given session.

To configure a source interface for a port-mirroring session:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- services port-mirroring session

**Note**
- The source interfaces that are supported for a port-mirroring session are:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan


- When a physical or bundle interface is selected for the session, then all of the sub-interfaces or bundle members of that interface will be automatically selected for that session as well. 

- Physical or bundle interfaces cannot be specified as source interfaces more than once per session (ingress, egress, or both), nor can their sub-interfaces or bundle members be specified at the same time in a given session. Each may be configured up to twice by two different sessions (ingress by one and egress by another), as long as the physical and bundle interfaces are not configured at the same time.

**Parameter table**

+------------------+---------------------------------------------------------+------------------+---------+
| Parameter        | Description                                             | Range            | Default |
+==================+=========================================================+==================+=========+
| source-interface | source interfaces for a specific port mirroring session | | string         | \-      |
|                  |                                                         | | length 1-255   |         |
+------------------+---------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug
    dnRouter(cfg-srv-port-mirroring-session)# source-interface ge100-1/0/1 direction ingress


**Removing Configuration**

To remove the specified source-interface from the list of monitored interfaces:
::

    dnRouter(cfg-srv-port-mirroring-session)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
