show config | flatten
---------------------

**Minimum user role:** viewer

To view an output of all the user configuration that is currently in use in one-line:



**Command syntax: show config <hierarchy> | flatten**

**Command mode:** operational



**Note**

- The output of this command displays commands in one-line, with all the hierarchy.

- The output of commands that aren't displayed will be indicated with " ^" that acts like the ``top`` command.

- * The configuration output is wrapped with **start** and **end** clauses as follows:

::

	# <system-name> config-start [%d-%b-%Y %H:%M:%S <timezone>]

	...

	# <system-name> config-end

..
	**Internal Note**

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

        - nacm

		- debug

	- * If there are space characters inside text fields the value should be wrapped with
	  double-quotes.

	- * Output of ``show config | flatten`` shouldn't support copy-pasting on DNOS's CLI.

    - * Output of ``show config | flatten`` should be exactly as ``show config`` output, just in one-line with hierarchies.


The following are the features on which you can view the configuration:

+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| Feature     | Description                                                                                  | Reference                                      |
+=============+==============================================================================================+================================================+
| level       | Level 1 - The main menu hierarchy level (e.g. interfaces)                                    | See examples below                             |
|             | Level 2 - main menu sub-menu hierarchy (e.g. protocols ospf)                                 |                                                |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| | flatten   | Display all configuration in the system.                                                     | See first example below                        |
|             | A command that dosen't have a leaf will shown with " ^" that acts like the ``top`` command.  |                                                |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| interfaces  | Display interface configuration                                                              | show config interfaces/                        |
|             |                                                                                              | show config interfaces | flatten               |
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+
| system      | Display system configuration                                                                 | show config system/show config system | flatten|
+-------------+----------------------------------------------------------------------------------------------+------------------------------------------------+



**Example**
::

	dnRouter# show config

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    system
        name dnRouter
        login
            ncm
            user dnroot
                password enc-gAAAAABgUIs_1U7_1nOEseJ75fkb7UVQSFOD5hi_wyLlHHb41toEsyUgw15QaCqpU2RYwe0CDuNkp_oLw27NNTC1oOk9jWRJXQ==
                role admin
            !
        !
        user RootUser
            description MyrootUser
        !
        user dnroot
            password $6$m7b5lYW.PtBTZ0lr$ibN6YvwGYpPauDUIbNu7XMYRkKOnG3H.gyCQVweYv/lgsXMj65ClO8yeGTYX/Rmy80Bx23AeXOWM47nDXr9sN.
        !
        snmp
            community 5566 vrf mgmt0
            !
        !
    !
    interfaces
        mgmt0
        !
    !

	#dnRouter config-end

	dnRouter# show config | flatten

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    system name dnRouter
    system login ncm user dnroot password enc-gAAAAABgUIs_1U7_1nOEseJ75fkb7UVQSFOD5hi_wyLlHHb41toEsyUgw15QaCqpU2RYwe0CDuNkp_oLw27NNTC1oOk9jWRJXQ==
    system login ncm user dnroot role admin
    system login user RootUser description MyrootUser
    system login user dnroot password $6$m7b5lYW.PtBTZ0lr$ibN6YvwGYpPauDUIbNu7XMYRkKOnG3H.gyCQVweYv/lgsXMj65ClO8yeGTYX/Rmy80Bx23AeXOWM47nDXr9sN.
    system snmp community 5566 vrf mgmt0 ^
    interfaces mgmt0 ^

	#dnRouter config-end

    dnRouter# show config system

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    system
        name dnRouter
        login
            ncm
            user dnroot
                password enc-gAAAAABgUIs_1U7_1nOEseJ75fkb7UVQSFOD5hi_wyLlHHb41toEsyUgw15QaCqpU2RYwe0CDuNkp_oLw27NNTC1oOk9jWRJXQ==
                role admin
            !
        !
        user RootUser
            description MyrootUser
        !
        user dnroot
            password $6$m7b5lYW.PtBTZ0lr$ibN6YvwGYpPauDUIbNu7XMYRkKOnG3H.gyCQVweYv/lgsXMj65ClO8yeGTYX/Rmy80Bx23AeXOWM47nDXr9sN.
        !
        snmp
            community 5566 vrf mgmt0
            !
        !
    !

	#dnRouter config-end

	dnRouter# show config system | flatten

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    system name dnRouter
    system login ncm user dnroot password enc-gAAAAABgUIs_1U7_1nOEseJ75fkb7UVQSFOD5hi_wyLlHHb41toEsyUgw15QaCqpU2RYwe0CDuNkp_oLw27NNTC1oOk9jWRJXQ==
    system login ncm user dnroot role admin
    system login user RootUser description MyrootUser
    system login user dnroot password $6$m7b5lYW.PtBTZ0lr$ibN6YvwGYpPauDUIbNu7XMYRkKOnG3H.gyCQVweYv/lgsXMj65ClO8yeGTYX/Rmy80Bx23AeXOWM47nDXr9sN.
    system snmp community 5566 vrf mgmt0 ^

    #dnRouter config-end

	dnRouter# show config interfaces

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    interfaces
        mgmt0
        !
    !

    dnRouter# show config interfaces | flatten

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    interfaces mgmt0 ^

	#dnRouter config-end

    dnRouter# show config protocols ospf

	# dnRouter config-start [30-Nov-2020 10:10:30 UTC]

    protocols
        ospf
            area 0
                mpls traffic-engineering admin-state enabled
                authentication md5
                interface ge100-0/0/0
                    authentication clear-text
                !
            !
        !
    !

	#dnRouter config-end

    dev-dnRouter(cfg)# show config protocols ospf | flatten

    # dnRouter config-start [22-Nov-2022 12:37:29 UTC]

    protocols ospf area 0 mpls traffic-engineering admin-state enabled
    protocols ospf area 0 authentication md5
    protocols ospf area 0 interface ge100-0/0/0 authentication clear-text

    # dnRouter config-end


.. **Help line:** show configuration

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 18.0    | Command introduced                                       |
+---------+----------------------------------------------------------+
