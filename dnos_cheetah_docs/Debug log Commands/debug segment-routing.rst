debug segment-routing
---------------------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug segment-routing events:

**Command syntax: segment-routing** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all segment-routing events will be debugged.

- Each command can be negated using the no command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the ospfd log file for ospf segment-routing and in isisd for isis segment-routing.

**Parameter table**

+------------------------+-----------------------------------------------------+
| Parameter              | Description                                         |
+========================+=====================================================+
| policy-fsm             | Debug SR-TE policy setup FSM                        |
+------------------------+-----------------------------------------------------+
| policy-installation    | Debug SR-TE policy installation to RIB              |
+------------------------+-----------------------------------------------------+
| path-validation        | Debug SR-TE path validation tests                   |
+------------------------+-----------------------------------------------------+
| path-validation-detail | Debug SR-TE path validation verbose tests (per hop) |
+------------------------+-----------------------------------------------------+
| path-fsm               | Debug SR-TE path FSM                                |
+------------------------+-----------------------------------------------------+
| path-events            | Debug SR-TE path events                             |
+------------------------+-----------------------------------------------------+
| pcep                   | Debug SR-TE PCEP events                             |
+------------------------+-----------------------------------------------------+

**Example**
::

	dnRouter# configure

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# segment-routing policy-fsm
	dnRouter(cfg-debug)# segment-routing policy-installation
	dnRouter(cfg-debug)# segment-routing path-validation
	dnRouter(cfg-debug)# segment-routing path-validation-detail
	dnRouter(cfg-debug)# segment-routing path-fsm
	dnRouter(cfg-debug)# segment-routing path-events
	dnRouter(cfg-debug)# segment-routing


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no segment-routing policy-fsm
	dnRouter(cfg-debug)# no segment-routing policy-installation
	dnRouter(cfg-debug)# no segment-routing path-validation
	dnRouter(cfg-debug)# no segment-routing path-validation-detail
	dnRouter(cfg-debug)# no segment-routing path-fsm
	dnRouter(cfg-debug)# no segment-routing path-events
	dnRouter(cfg-debug)# no segment-routing



.. **Help line:** Debug log segment-routing events

**Command History**

+-------------+-----------------------------------------------+
|             |                                               |
| Release     | Modification                                  |
+=============+===============================================+
|             |                                               |
| 15.0        | Command introduced                            |
+-------------+-----------------------------------------------+
| 16.2        | Removed set-debug command                     |
+-------------+-----------------------------------------------+
| 18.3        | Added path-fsm and path-events debug commands |
+-------------+-----------------------------------------------+
| 19.0        | Added pcep debug command                      |
+-------------+-----------------------------------------------+