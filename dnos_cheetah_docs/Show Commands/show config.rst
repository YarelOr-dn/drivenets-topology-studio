show config
-----------

**Minimum user role:** viewer

To view an output of all the user configuration that is currently in use:



**Command syntax: show config** defaults [level-1] [level-2]

**Command mode:** operational



**Note**

- The output of this command displays only commands that have been explicitly configured (i.e. changed from the default).

- Notice the square brackets, for example in: interfaces ge100-1/1/1 mpls enabled [disabled]. The default admin-value of mpls under interface is "disabled", however, for this interface MPLS is enabled.

- * The configuration output is wrapped with **start** and **end** clauses as follows:

::

	# <system-name> config-start [%d-%b-%Y %H:%M:%S <timezone>]

	...

	# <system-name> config-end

..
	**Internal Note**

	- if user configured value which is default, it will be shown in ``show config``.

	- The order of show config hierarchies output shall be:

		- system

		- services

		- interfaces

		- routing-options

		- protocols

		- multicast

		- routing-policy

		- access-lists

		- qos

		- debug

	- * In case of space characters inside text field the value should be wrapped with
	  double-quotes.

	- * Output of ``show config defaults`` shouldn't support copy-pasting on DNOS's CLI.

	- * In ``show config defaults`` command output default value will be printed also when user configuration is the same as the yang defaults. E.g. ``mtu 1514 [1514]``.


The following are the features on which you can view the configuration:

+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| Feature     | Description                                                                                  | Reference                                      |
+=============+==============================================================================================+================================================+
| level       | Level 1 - The main menu hierarchy level (e.g. interfaces)                                    | See examples below                             |
|             | Level 2 - main menu sub-menu hierarchy (e.g. protocols ospf)                                 |                                                |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| access-list | Display access-list configuration                                                            | show config access-lists                       |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| defaults    | Display all configuration in the system, including ones with default values.                 | See Example 3 below                            |
|             | The default value of a changed parameter appears in square brackets alongside the new value. |                                                |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| interfaces  | Display interface configuration                                                              | show config interfaces                         |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| system      | Display system configuration                                                                 | show config system/show config defaults system |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+



**Example**
::

	dnRouter# show config

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	system
	  name dnRouter
	  login
	    user RootUser
	      description MyrootUser
	    !
	  !
	!

	#dnRouter config-end

	dnRouter# show config defaults

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	system
	  name dnRouter
	  login
	    user RootUser
	      description MyrootUser
	    !
	  !
	  logging
	    syslog
	      event-group all severity alert [warning]
	      facility local7
	    !
	  !
	!
	...
	interfaces
	  ge100-1/1/1
	    mtu 9200 [1514]
	    mpls enabled [disabled]
	  !
	!

	#dnRouter config-end

	dnRouter# show config system

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	system
	  name dnRouter
	  login
	    user RootUser
	      description MyrootUser
	    !
	  !
	!

	#dnRouter config-end

	dnRouter# show config interfaces

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	interfaces
	  ge100-1/1/1
	    mtu 9200
	    mpls enabled
	  !
	  bundle-2
	    mtu 9200
	    mpls enabled
	  !
	!

	#dnRouter config-end

	dnRouter# show config qos

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	qos
	  policy MyQoSPolicy2
	    rule 5
	      description "real time service"
	    !
	    rule default
	    !
	  !
	  policy myPolicy1
	    rule 1
	      match traffic-class myTrafficClassMap1
	      action
	        police tr3cm rate 50 percent excess-rate 40 percent burst 70 milliseconds
	      !
	    !
	    rule default
	    !
	  !
	!

	#dnRouter config-end

	dnRouter# show config protocols ospf

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

	protocols
	  ospf
	    router-id 1.1.1.1
	    mpls ldp-sync enabled
	    graceful-restart enabled grace-interval 50
	    redistribute bgp
	    area 0
	      interface bundle-2
	      !
	    !
	  !
	!

	#dnRouter config-end

.. **Help line:** show configuration

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 5.1.0   | Command introduced                                       |
+---------+----------------------------------------------------------+
| 6.0     | Removed control terminal example                         |
|         | Repositioned "defaults" attribute in the command syntax. |
+---------+----------------------------------------------------------+
| 15.0    | Updated command syntax                                   |
+---------+----------------------------------------------------------+
