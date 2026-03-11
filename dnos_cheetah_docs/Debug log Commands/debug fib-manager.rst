debug fib-manager
------------------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug fib-manager events:

**Command syntax: fib-manager** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all fib-manager events will be debugged.

- Each command can be negated using the no or unset command prefix.

- The debug information is written in the fib-managerd log file.

-  When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

**Parameter table**

+---------------------------+--------------------------------------------------+
| Argument                  | Description                                      |
+===========================+==================================================+
| cli                       | debug fib-manager cli interface                  |
+---------------------------+--------------------------------------------------+
| events                    | debug fib-manager events                         |
+---------------------------+--------------------------------------------------+
| evpn-ctrl-learn           | debug fib-manager evpn ctrl learn (MAC)          |
+---------------------------+--------------------------------------------------+
| evpn-ctrl-learn-detail    | debug fib-manager evpn ctrl learn detail (MAC)   |
+---------------------------+--------------------------------------------------+
| init                      | debug fib-manager init stage                     |
+---------------------------+--------------------------------------------------+
| packets                   | debug fib-manager packets sent and received      |
+---------------------------+--------------------------------------------------+
| database                  | debug fib-manager database                       |
+---------------------------+--------------------------------------------------+
| fpm                       | debug fib-manager forwarding plane manager (FPM) |
+---------------------------+--------------------------------------------------+
| fpm-detail                | debug fib-manager FPM extended information       |
+---------------------------+--------------------------------------------------+
| rib-manager               | debug fib-manager and rib connections            |
+---------------------------+--------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# fib-manager events
	dnRouter(cfg-debug)# fib-manager init
	dnRouter(cfg-debug)# fib-manager packets
	dnRouter(cfg-debug)# fib-manager


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no fib-manager events
	dnRouter(cfg-debug)# no fib-manager init
	dnRouter(cfg-debug)# no fib-manager


.. **Help line:** Debug fib-manager events

**Command History**

+---------+----------------------------+
| Release | Modification               |
+=========+============================+
| 11.0    | Command introduced         |
+---------+----------------------------+
| 11.5    | Applied new hierarchy      |
+---------+----------------------------+
| 16.2    | Removed set-debug command  |
+---------+----------------------------+