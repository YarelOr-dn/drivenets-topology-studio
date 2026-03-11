debug mpls-oam
---------------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug LDP events:

**Command syntax: mpls-oam** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all mpls-oam events will be debugged.

- Each command can be negated using the no or unset command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the oamd log file.


**Parameter table**

+-----------------+------------------------------------------+
| Argument        | Description                              |
+=================+==========================================+
| cli             | debug mpls-oam cli interface             |
+-----------------+------------------------------------------+
| events          | debug mpls-oam events                    |
+-----------------+------------------------------------------+
| init            | debug mpls-oam init stage                |
+-----------------+------------------------------------------+
| packets         | debug mpls-oam packets sent and received |
+-----------------+------------------------------------------+
| states          | debug mpls-oam state                     |
+-----------------+------------------------------------------+
| timers          | debug mpls-oam timers                    |
+-----------------+------------------------------------------+
| rib-manager     | debug mpls-oam and rib connections       |
+-----------------+------------------------------------------+
| ip-sla          | debug mpls-oam ip sla                    |
+-----------------+------------------------------------------+
| ip-sla-extrended| debug mpls-oam ip sla extended           |
+-----------------+------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# debug mpls-oam cli
	dnRouter(cfg-debug)# mpls-oam events
	dnRouter(cfg-debug)# mpls-oam init
	dnRouter(cfg-debug)# mpls-oam states
	dnRouter(cfg-debug)# mpls-oam rib-manager


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no mpls-oam init
	dnRouter(cfg-debug)# no mpls-oam rib-manager


.. **Help line:** Debug LDP events

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 11.0    | Command introduced          |
+---------+-----------------------------+
| 11.4    | Removed profile option      |
+---------+-----------------------------+
| 11.5    | Applied new debug hierarchy |
+---------+-----------------------------+
| 16.2    | Removed set-debug command   |
+---------+-----------------------------+
| 19.2    | Added IP-SLA support        |
+---------+-----------------------------+