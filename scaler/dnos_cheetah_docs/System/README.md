# DNOS System Configuration Reference

This document contains the complete DNOS CLI system configuration syntax:
- System Profile (l3_pe, scale settings)
- SSH/Telnet/GRPC/NETCONF management
- Login/Users/Authentication
- SNMP configuration
- NTP/DNS/Logging
- Management VRF

---

## grub-timeout
```rst
system grub-timeout
-------------------

**Minimum user role:** operator

The GRUB timeout value determines the amount of time that the OS GRUB bootloader waits before automatically booting into the default operating system or kernel selection.

The timeout is specified in seconds.

To configure the system's GRUB timeout value:

**Command syntax: grub-timeout [grub-timeout]**

**Command mode:** config

**Hierarchies**

- system

**Note**

A timeout of '0' means to boot the default entry immediately without displaying the GRUB menu.

**Parameter table**

+--------------+------------------------+-------+---------+
| Parameter    | Description            | Range | Default |
+==============+========================+=======+=========+
| grub-timeout | OS GRUB timeout value. | 0-30  | 5       |
+--------------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grub-timeout 0
    Notice: Continuing with the commit will cause the following:
    The following commit will change the system grub timeout time. When set to zero or a very short period, system boot failure may require physical access to the platform for recovery."
    Enter yes to continue with commit, no to abort commit (yes/no) [no]


**Removing Configuration**

To revert the system grub-timeout to its default value:
::

    dnRouter(cfg-system)# no grub-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.1    | Command introduced |
+---------+--------------------+
```

## in-band-management access-list ipv4
```rst
system in-band-management access-list ipv4
------------------------------------------

**Minimum user role:** operator

The control-plane access-list is supported only on in-band traffic and is hardware-configured to
allow or block different IPv4/IPv6 traffic destined to the NCC (i.e. to any local address,
including multicast packets).

To apply an access-list to the control plane traffic designated to a local address:

**Command syntax: in-band-management access-list ipv4 [access-list-name]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- The access-list will not affect transit traffic.

.. - no command removes a specific access-list, or all access-lists in a specific type

**Parameter table**

+------------------+------------------------------------------------------------+-------------------------------------+---------+
| Parameter        | Description                                                | Range                               | Default |
+==================+============================================================+=====================================+=========+
| access-list-name | Filter the displayed information to a specific access-list | The name of an existing access-list | \-      |
+------------------+------------------------------------------------------------+-------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# in-band-management access-list ipv4 IPv4_CP_ACL


**Removing Configuration**

To remove in-band management access-list configuration:
::

    dnRouter(cfg-system)# no in-band-management access-list

dnRouter(cfg-system)# no in-band-management access-list ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
```

## in-band-management access-list ipv6
```rst
system in-band-management access-list ipv6
------------------------------------------

**Minimum user role:** operator

The control-plane access-list is supported only on in-band traffic and is hardware-configured to
allow or block different IPv4/IPv6 traffic destined to the NCC (i.e. to any local address,
including multicast packets).

To apply an access-list to the control plane traffic designated to a local address:

**Command syntax: in-band-management access-list ipv6 [access-list-name]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- The access-list will not affect transit traffic.

.. - no command removes a specific access-list, or all access-lists in a specific type

**Parameter table**

+------------------+------------------------------------------------------------+-------------------------------------+---------+
| Parameter        | Description                                                | Range                               | Default |
+==================+============================================================+=====================================+=========+
| access-list-name | Filter the displayed information to a specific access-list | The name of an existing access-list | \-      |
+------------------+------------------------------------------------------------+-------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# in-band-management access-list ipv6 IPv6_CP_ACL


**Removing Configuration**

To remove in-band management access-list configuration:
::

    dnRouter(cfg-system)# no in-band-management access-list

dnRouter(cfg-system)# no in-band-management access-list ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
```

## in-band-management dnor-server-vrf
```rst
system in-band-management dnor-server-vrf
-----------------------------------------

**Minimum user role:** operator

Configures the VRF over which the communication towards DNOR servers will go through.

**Command syntax: in-band-management dnor-server-vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system

**Note**
-  mgmt0 and default VRFs are the default config, mgmt0 is not configurable and enabled by default. default VRF is configurble and can be updated using this command.
-  The destination as were configured by set mgmt dnor-server command.
-  Validation: the source-interface shall be configured under the VRF, as part of network-services vrf instance in-band-management source-interface CLI command.

**Parameter table**

+-----------+-------------------------------------------------------------------------+--------------------------------+---------+
| Parameter | Description                                                             | Range                          | Default |
+===========+=========================================================================+================================+=========+
| vrf-name  | The name of the dnor server vrf to be used for communication with dnor. | | default          (in-band)   | default |
|           |                                                                         | | non-default-vrf  (in-band)   |         |
+-----------+-------------------------------------------------------------------------+--------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# in-band-management dnor-server-vrf non-default-vrf


**Removing Configuration**

To remove in-band management dnor-server-vrf configuration:
::

    dnRouter(cfg-system)# no in-band-management dnor-server-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## in-band-management source-interface
```rst
system in-band-management source-interface
------------------------------------------

**Minimum user role:** operator

The configuration relates to both IPv4 and IPv6 address families. If IPv4 or IPv6 address is not
configured for the source interface, the client management applications will not work for the
appropriate address-family. Changing the IPv4 or IPv6 address on the selected interface requires
that the source-IP address of the client protocol packets be updated immediately.

Set the source interface for all in-band default VRF (VRF-0) management applications (for
example, NTP, SNMP, Syslog, and TACACS), using the following command:

**Command syntax: in-band-management source-interface [interface-name]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- If system in-band management interface is not defined (or if it doesn't have an IP address), and the source-interface is not defined for a specific protocol, no packets will be generated for this protocol.

  - As an exception, if the source-interface is defined for specific per-protocol server then the packets will be generated for it.

  - As an exception, if the in-band-management source-interface is defined for specific non-default VRF then the packets will be generated for it.

- The following client management applications are supported:

  - TACACS

  - SNMP trap

  - Syslog

  - IPFIX/Netflow

  - DNS

  - NTP

.. - Any interface in the default VRF with an IPv4/IPv6 address including loopback and irb, except GRE tunnel interfaces

  - In v11.1 and earlier, only Lo-0 interface is supported
  - In v18, support for IRB interface was added
  - In v19.1.1 support for any in-band interface was added

  - Selected interface must include both IPv4 and IPv6 addresses

    - "no interface ipv4-address / ipv6-address command can be applied to the selected interface

  - Interface cannot be removed if it is selected as source interface for in-band management

  - If selected interface has more than one IP address, default IP address will be used as a a source interface

  - The selected interface refers both to IPv4 and IPv6 addresses

  - If ipv4/ipv6 address is changed on the selected interface, the source-IP address of the client protocol packets must be updated immediately

  - If "system in-band-management interface is not set and source-interface is not set for a specific protocol, no packets will be generated for this protocol"

**Parameter table**

+----------------+---------------------------------------------------+----------------------------------------------------------------------------------+---------+
| Parameter      | Description                                       | Range                                                                            | Default |
+================+===================================================+==================================================================================+=========+
| interface-name | The name of the interface for in-band management. | Any interface in the default VRF with an IPv4/IPv6 address including loopback    | \-      |
|                |                                                   | and irb, except GRE tunnel interfaces                                            |         |
+----------------+---------------------------------------------------+----------------------------------------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# in-band-management source-interface lo0


**Removing Configuration**

To remove in-band management source-interface configuration:
::

    dnRouter(cfg-system)# no in-band-management source-interface

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 6.0     | Changed ip-version syntax                                      |
|         | Applied new hierarchy                                          |
+---------+----------------------------------------------------------------+
| 11.0    | Added IPv6 support, removed ip-version from the command syntax |
+---------+----------------------------------------------------------------+
| 13.0    | Updated range of interface-name                                |
+---------+----------------------------------------------------------------+
| 19.1.1  | Support any in-band interface as source-interface              |
+---------+----------------------------------------------------------------+
```

## name
```rst
system name
-----------

**Minimum user role:** operator

The system name identifies the server in the CLI prompt and elsewhere. The system name is provided automatically during deployment, but you can change the default name, as follows:

**Command syntax: name [name]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- The new name will appear in the prompt after commit. See Transaction Commands.
- Support the following characters: 0-9 a-z A-Z - _ .

**Parameter table**

+-----------+-------------------------+-----------------+----------+
| Parameter | Description             | Range           | Default  |
+===========+=========================+=================+==========+
| name      | The name of the system. | | string        | dnRouter |
|           |                         | | length 1-48   |          |
+-----------+-------------------------+-----------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# name my-system-name


**Removing Configuration**

To revert the configured system name to default
::

    dnRouter(cfg-system)# no name

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy               |
+---------+-------------------------------------+
| 9.0     | Name size limited to 255 characters |
+---------+-------------------------------------+
| 16.2    | Name size limited to 24 characters  |
+---------+-------------------------------------+
| 18.0    | Name size limited to 48 characters  |
+---------+-------------------------------------+
```

## preferred-ncc
```rst
system preferred-ncc
--------------------

**Minimum user role:** operator

Up to two NCCs can be set per cluster for redundancy; one active (the preferred NCC) and the other in stand-by. The NCC identification is managed by DNOR. The first NCC that DNOR configures is by default the preferred NCC and receives the ID 0. The other NCC is allocated the ID 1.

During system boot, if both NCCs are available, the preferred NCC is the one that will be selected as the active NCC.

You can manually configure the preferred designation of an NCC.

To set the preferred NCC:

**Command syntax: preferred-ncc [ncc-id]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- This command is not applicable to a standalone NCP. The NCC in a standalone NCP is automatically configured as primary and receives the ID 0. You cannot change this setting.

- Only one NCC per cluster can serve as the preferred NCC. When you configure an NCC as preferred, the other NCC will automatically be stripped of its preferred status.

.. - The factory default preferred NCC number is ncc-id=0. 'no preferred-ncc' command returns the preferred-ncc parameter to the default.

  - For **standalone cluster**, NCC 0 is configured as primary. User cannot change this configuration.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| ncc-id    | The identifier of the preferred NCC. If the NCC with the specified ID is not     | 0-1   | 0       |
|           | currently the preferred one, it will become the preferred one and it will become |       |         |
|           | the active NCC on the next system boot.                                          |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# preferred-ncc 1


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-system)# no preferred-ncc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## profile
```rst
system profile
--------------

**Minimum user role:** operator

The system profile dictates the set of features that can be supported simultaneously in the system.

To configure the global profile, that shall be applied for all NCPs in the cluster:

**Command syntax: profile [system-profile]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- DNOS configuration cannot conflict with the configured system profile. A validation will enforce that the configuration is valid.

- Profile reconfiguration is traffic affecting, will require the user to confirm the change and shall cause the WB Agent process on each NCP to restart.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| system-profile | The name of the profile applied to the system. The profile is applied to all     | | default   | default |
|                | NCPs in the cluster.                                                             | | l3-pe     |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# profile profile_a
    Notice: Continuing with the commit will cause the following:
    The following commit will change the system profile. WB Agent process on all NCPs shall restart, traffic loss will occur and some features may not be available after this change takes effect.
    Enter yes to continue with commit, no to abort commit (yes/no) [no]


**Removing Configuration**

To revert the global system profile to its default value:
::

    dnRouter(cfg-system)# no profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## system cli-alias
```rst
system cli-alias
----------------

**Minimum user role:** operator

Entering the same commands repeatedly is sometimes a redundant task. The DNOS CLI allows you to define command shortcuts that can be used for the most common commands. You can configure up to 1024 aliases.

After setting up the various shortcuts, you can integrate them in the CLI.

To configure aliases for commands:

**Command syntax: cli-alias [cli-alias] [cli-alias-command]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- When introducing alias keys with two or more words separated by a space, only the first word will be saved.

- When upgrading to version 17.2, any alias key with two or more words separated by a space, will be deleted.

- when executing the alias it will be replaced with the configured value (including all spaces)

- alias value maximum length of 255 chars, alias name max length of 255 chars

- up to 1024 configurable aliases shall be supported

- alias will be supported at under any CLI level (main, config, interfaces, protocols, system, etc.)

- There will no validation for the value of the alias, thus is it can contain an unknown command, running the alias will return the relevant error

System will prevent recursive aliasing, for example, the following configuration will fail:

- cli-alias a b

- cli-alias b a

aliases work in exact match - when executing it, the CLI process will look for the exact alias.

- aliases are case sensitive

- security - user using the alias will not be able to run commands not in the permission level (the checks will be done on the alias value)

- alias will support concatenation of one alias to another aliases or to regular CLI commands

- no command without alias-key removes all alias configuration.

- no command with specific alias-key removes specific alias configuration.

Not supported:

- auto complete (tab) of alias commands

- present optional completion when using ?

- short commands for alias-value like "sh bg sum"

- single alias running two commands (separated with ; )

**Parameter table**

+-------------------+---------------------------------------------------+------------------+---------+
| Parameter         | Description                                       | Range            | Default |
+===================+===================================================+==================+=========+
| cli-alias         | Configured name of the cli alias command          | | string         | \-      |
|                   |                                                   | | length 1-255   |         |
+-------------------+---------------------------------------------------+------------------+---------+
| cli-alias-command | Configured command line (string) of the cli alias | | string         | \-      |
|                   |                                                   | | length 1-255   |         |
+-------------------+---------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cli-alias sbs "show bgp summary"
    dnRouter(cfg-system)# cli-alias sr0 "show route 0.0.0.0"
    dnRouter(cfg-system)# cli-alias sint "show interfaces"
    dnRouter(cfg-system)# cli-alias incbun "| include bundle"
    dnRouter(cfg-system)# cli-alias confip "interfaces lo0 ipv4-address 1.2.3.4/32"

    dnRouter# sbs
    dnRouter# sint incbun
    dnRouter# show interfaces counters incbun
    dnRouter(cfg)# confip


**Removing Configuration**

To delete cli-alias configuration:
::

    dnRouter(cfg-system)# no cli-alias

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 13.1    | Command introduced                     |
+---------+----------------------------------------+
| 17.2    | Added note about spaces in alias names |
+---------+----------------------------------------+
```

## system cli-timestamp
```rst
system cli-timestamp
--------------------

**Minimum user role:** operator

By default, commands displayed in the CLI do not show a timestamp. To turn on timestamp so that each entered command will be displayed with a timestamp:

**Command syntax: cli-timestamp [admin-state]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- In the same way as debug set commands, the command "set cli-timestamp" overrides this configuration during the session.

- no command returns to default configuration.

**Parameter table**

+-------------+---------------------------------------------------+--------------+----------+
| Parameter   | Description                                       | Range        | Default  |
+=============+===================================================+==============+==========+
| admin-state | The desired configuration of cli-timestamp option | | enabled    | disabled |
|             |                                                   | | disabled   |          |
+-------------+---------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cli-timestamp enabled
    dnRouter(cfg-system)# cli-timestamp disabled


**Removing Configuration**

To revert the system cli-timestamp to its default value:
::

    dnRouter(cfg-system)# no cli-timestamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
```

## system debug file files
```rst
system debug file files
-------------------------

**Minimum user role:** operator

By default, the system saves 10 debug messages local log files. You can change this limit, depending on the space that you can allocate to logging.

To set the number of log files:

**Command syntax: files [files]**

**Command mode:** config

**Hierarchies**

- system debug


.. **Note**

	- "no debug" command reverts the whole debug paramets to its default value

	- "no debug file" command reverts the debug file parameter to its default value

	- "no debug file <file-name>" reverts the debug file parameter to its default value

	- "no debug file <file-name> files" reverts configuration of number of rotated files per specific debug file to its default.

	- After maximum number of files is reached, the oldest file is overwritten


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                                         | Range | Default |
+===========+=====================================================================================================================================================+=======+=========+
| Files     | The maximum number of log files that the system will create. When the number is reached and the last file is full, the oldest file will be deleted. | 1..20 | 10      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp 
	dnRouter(system-debug-file-bgp)# files 20
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-debug-file-bgp)# no files 

.. **Help line:** configure number of rotated files for debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


```

## system debug file
```rst
system debug file
-----------------

**Minimum user role:** operator

Configure debug messages logging to local files. Debug messages are generated for debugging purposes and are stored in local files.

To configure logging of debug messages to local files:

**Command syntax: system debug file [file-name]**

**Command mode:** config

**Hierarchies**

- system debug


**Note**

- Debug messages are much more volume intensive than system events.

- Notice the change in prompt.

- If a newly configured debug file already exists in the file system, the debug data will be appended to the existing file.

.. - "no debug" command reverts the whole debug paramets to its default value

	- "no debug file <file-name>" command reverts the debug file parameter to its default value

**Parameter table**

+-----------+-----------------------------+--------------------+---------+
| Parameter | Description                 | Range              | Default |
+===========+=============================+====================+=========+
| file-name | The debug file to configure | Any system process | \-      |
+-----------+-----------------------------+--------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp
	dnRouter(system-debug-file-bgp)#




**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-debug)# no file bgp
	dnRouter(cfg-system)# no debug

.. **Help line:** configure debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


```

## system debug file size
```rst
system debug file size
------------------------

**Minimum user role:** operator

**Description:** 


**Command syntax: size [size]**

**Command mode:** config

**Hierarchies**

- system debug


.. **Note**

	- "no debug" command reverts the whole debug paramets to its default value

	- "no debug file <file-name>" reverts the debug file parameter to its default value

	- "no debug file <file-name> size" removes configuration of rotated files size per specific debug file to default.

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                                   | Range      | Default |
+===========+===============================================================================================+============+=========+
| Size      | The maximum size of the file. When the size is reached, new logs will be saved in a new file. | 1..1024 MB | 10 MB   |
+-----------+-----------------------------------------------------------------------------------------------+------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp
	dnRouter(system-debug-file-bgp)# size 3

	dnRouter(cfg-system-debug)# file ospf
	dnRouter(system-debug-file-ospf)# size 5


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-debug-file-bgp)# no size
	dnRouter(cfg-system-debug)# no file bgp


.. **Help line:** configure maximum number of the logging file for debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy event
```rst
system event-manager event-policy event
---------------------------------------

**Minimum user role:** admin

Use this command to configure the attributes and conditions which triggers the policy. Up to five scripts can run simultaneously.

**Command syntax: event [event-name]** {attribute [event-attribute] \| trigger-condition [condition] \| time-interval [interval]}

**Command mode:** config

**Hierarchies**

- system event-manager event-policy event

**Note**

- A policy script can be used by several named policies as long as the system-events are different.

- Notice the change in prompt.

.. - *trigger-condition -* ON, once the event received and the event-count reached.

    - *time-interval -* the duration of time the event-count needs to be reached in order to execute the policy. "0" is used as infinite value.

    - no command removes a specific event entry, upon removal all running policies will continue to run until termination.

    Validation:

    - Policy-script can be used by several policy-names as long as the system-events are different.

    - Only up to 5 policies can be in admin-state "enabled" in the same time.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| Parameter       | Description                                                                                                        | Range                     | Default |
+=================+====================================================================================================================+===========================+=========+
| event-name      | The system event name the script needs to register                                                                 | string (lower case only)  | \-      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| event-attribute | A variable name to match in the system event                                                                       | string                    | \-      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| condition       | Once the event-count has been reached, the condition when the policy is triggered                                  | \-                        | On      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| interval        | The duration of time the event-count must be reached for the policy to be executed. "0" is used as infinite value. | 0 | 60.. 604800 (seconds) | 0       |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# attribute new-state
    dnRouter(cfg-policy-test-event)#
    dnRouter(cfg-policy-test-event)# trigger-condition on
    dnRouter(cfg-policy-test-event)#
    dnRouter(cfg-policy-test-event)# time-interval 300
    dnRouter(cfg-policy-test-event)#



**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no event if_link_state_change_down

.. **Help line:** configure the event-policy parameters.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

```

## system event-manager event-policy event time-interval
```rst
system event-manager event-policy event time-interval
-----------------------------------------------------

**Minimum user role:** admin

Use this command to configure the time frame within which the registered system-events must get to the triggered condition.

**Command syntax: time-interval [interval]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt.

.. - *time-interval -* the duration of time the event-count needs to be reached in order to execute the policy. "0" is used as infinite value.

    - no command returns to default value.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
| Parameter | Description                                                                                                        | Range                    | Default |
+===========+====================================================================================================================+==========================+=========+
| interval  | The duration of time the event-count must be reached for the policy to be executed. "0" is used as infinite value. | 0 | 60..604800 (seconds) | 0       |
+-----------+--------------------------------------------------------------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# time-interval 300
    dnRouter(cfg-policy-test-event)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-policy-test-event)# no time-interval

.. **Help line:** configure the time interval in seconds.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy event trigger-condition
```rst
system event-manager event-policy event trigger-condition
---------------------------------------------------------

**Minimum user role:** admin

Use this to configure the event attributes and conditions that will trigger the policy.

**Command syntax: trigger-condition [condition]** [event-count]

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- notice the change in prompt

.. - *trigger-condition -* ON, once the event received and the event-count reached.

    - no command returns to default value.

**Parameter table**

+-------------+-----------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                       | Range  | Default |
+=============+===================================================================================+========+=========+
| condition   | The policy is executed when the number of matching                                |        |         | 
|             | events received equals event-count                                                | \-     | On      |
+-------------+-----------------------------------------------------------------------------------+--------+---------+
| event-count | The number of matching system events that must be received to trigger the policy  | 1..100 | 1       |
+-------------+-----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# trigger-condition on 10
    dnRouter(cfg-policy-test-event)#

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-policy-test-event)# no trigger-condition

.. **Help line:** configures when the event-policy will be executed.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy policy-iteration
```rst
system event-manager event-policy policy-iteration
--------------------------------------------------

**Minimum user role:** admin

Use this command to configure the number of times the policy will be executed.

**Command syntax: policy-iteration [iteration]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy 


**Note**

- Notice the change in prompt.

.. - Once the policy executed the policy-iteration number of times the policy will appear in operational-state "inactive".

    - a change in the policy-iteration configuration during policy execution will take effect on the next policy execution.

    - "0" is used as infinite value.

    - no command resets policy-iteration to default, will take effect on next policy execution.

**Parameter table**

+-----------+--------------------------------------------------+-------------+---------+
| Parameter | Description                                      | Range       | Default |
+===========+==================================================+=============+=========+
| iteration | The number of times the policy will be executed. | 0 | 1..1000 | 0       |
|           | "0" is an infinite value                         |             |         |
+-----------+--------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-event-policy-test)# policy-iteration 0
    dnRouter(cfg-event-policy-test)#
    dnRouter(cfg-event-policy-test)# policy-iteration 20
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no policy-iteration

.. **Help line:** configure the number of policy iterations.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy
```rst
system event-manager event-policy
---------------------------------

**Minimum user role:** admin

The event-policy monitors specific system events and performs configuration changes and operational request commands when the monitored system event is generated. For example, when a specific event is triggered, the device is rebooted. Once an event policy has completed, it cannot be triggered again for 30 seconds. This policy is executed based on a matching trigger of a registered system event.

The configure the event-policy name:

**Command syntax: event-policy [policy-name]**

**Command mode:** config

**Hierarchies**

- system event-manager


**Note**

- Notice the change in prompt

.. - event-policy - is a policy that will be executed upon matching trigger of registered system event.

    - policy-name must be unique per policy type.

    - no command deletes the policy configuration and the log files generated by the policy.

**Parameter table**

+-------------+-------------------------------------------------+--------+---------+
| Parameter   | Description                                     | Range  | Default |
+=============+=================================================+========+=========+
| policy-name | The name of the policy                          | String | \-      |
|             | The policy-name must be unique per policy type. |        |         |
+-------------+-------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-system-event-manager)# no event-policy test

.. **Help line:** configures the name given by the user to the policy.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy script-maxruntime
```rst
system event-manager event-policy script-maxruntime
---------------------------------------------------

**Minimum user role:** admin

Use this command to configure the maximum time can run. Once the maximum time is reached the policy is terminated. During policy execution the same policy cannot be run.

**Command syntax: script-maxruntime [runtime]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt

.. - a change in the script-maxruntume configuration during policy execution will take effect on the next policy execution.

    - once script-maxruntime reached, the policy will be terminated even if it still in the middle of the execution.

    - during policy execution no another execution will be initiated of the same policy rule (policy-name)

    - no command resets script-maxruntime to default, will take effect on next policy execution.

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                                                            | Range            | Default |
+===========+========================================================================================================================+==================+=========+
| runtime   | The maximum time a policy can run before it is terminated.                                                             | 5..600 (seconds) | 30      |
|           | Any change in the script-maxruntume configuration whilst a policy is running take effect on the next policy execution. |                  |         |
+-----------+------------------------------------------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# script-maxruntime 300
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no script-maxruntime

.. **Help line:** configure the runtime duration of the policy in seconds.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager event-policy script-name
```rst
system event-manager event-policy script-name
---------------------------------------------

**Minimum user role:** admin

Use this command to configure the name of the script-name to be executed. If the script is deleted, the policy operational state becomes "inactive". Once an event policy has completed, it cannot be triggered again for 30 seconds.

**Command syntax: script-name [script-name]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt

.. - event-policy scripts shall be located under /event-manager/event-policy/scripts dir.

    - Once policy terminated a 30 seconds suspension will be issued before next policy execution.

    - there is no "no command", policy-script can't be removed.

    - "script-name" is a mandatory parameter and commit will fail if no script-name was configured for policy.

    - In case of script-name file deletion, policy operational-state will become inactive.

    Validation:

    - script-name can be used by several policy-names as long as the system-events are different.

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                                             | Range  | Default |
+=============+=========================================================================================================+========+=========+
| script-name | The name of the script-file which must be located in the /event-manager/event-policy/scripts directory. | string | \-      |
|             | This is a mandatory parameter. The commit will fail if no script name has been configured.              |        |         |
+-------------+---------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)#
    dnRouter(cfg-event-policy-test)# script-name event_policy_example.py
    dnRouter(cfg-event-policy-test)#


.. **Help line:** configure the script-name name that will be executed.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system event-manager
```rst
system event-manager
--------------------

**Minimum user role:** admin

To enter the event-manager configuration level:

**Command syntax: event-manager**

**Command mode:** config

**Hierarchies**

- system event-manager


**Note**

- Up to five policies, from all types, can be in admin-state "enabled" simultaneously

- Notice the change in prompt

 .. - event-policy - policy that will be executed upon matching trigger of registered system event.

     - periodic-policy - a recurrent policy according to the scheduled configuration, with limited execution time.

     - generic-policy - policy that will be executed only once and unlimited in execution time.

     - up-to 5 policies can be in admin-state "enabled" at the same time, from all policy types.

    -  there is no "no command".


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)#


.. **Help line:** configure the event-manager functionality.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

```

## system fabric-min-links
```rst
system fabric-min-links
-----------------------

**Minimum user role:** operator

Each NCP in the cluster is connected to the NCF using up to 40 links depending on the NCP model and cluster type. You can configure the minimum number of NCP fabric member interfaces that must be active for the NCP to be available. The configuration is global for all NCPs in the cluster.

For non-blocking traffic, we recommend configuring a minimum of 11 fabric links for small clusters, 10 fabric links for medium and large clusters (the number of physical fabric interface connections minus 1), and 32 fabric links for clusters using NCP-36CD-S model types, which is the minimum number of NCP fabric member interfaces that must be active for the NCP-36CD-S model type to be available.

If you receive the system event IF_LINK_STATE_CHANGE_MIN_LINKS_REACHED, the link state has moved to a 'down' state because the configured min-links limit has been reached. To correct this, check the faulty links and the NCF or use the system fabric-min-links configuration command to reconfigure the minimum number of required NCF links.

To configure the number of fabric links that must be active:

**Command syntax: fabric-min-links [fabric-min-links]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- This command is not applicable to a standalone NCP.

- Validation – number of fabric-min-links cannot be higher than supported fabric interfaces per ncp in cluster (per cluster type)

- no command restores the fabric min-links value to default value

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| fabric-min-links | The number of links below which the NCP will become unavailable. The value       | 0-40  | 1       |
|                  | cannot be higher than supported fabric interfaces per cluster NCP.               |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# fabric-min-links 11
    dnRouter(cfg-system)#


**Removing Configuration**

To revert the system fabric-min-links to its default value:
::

    dnRouter(cfg-system)# no fabric-min-links

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 11.5    | Changed the default value to 10  |
+---------+----------------------------------+
| 13.3    | Changed the default from 10 to 1 |
+---------+----------------------------------+
| 16.1    | Extended upper bound to 40 links |
+---------+----------------------------------+
| 19.10   | Added setting of 0 for AI nodes  |
+---------+----------------------------------+
```

## system fabric-min-ncf
```rst
system fabric-min-ncf
---------------------

**Minimum user role:** operator

Every cluster has a recommended number of cluster NCFs that takes into consideration N+1 redundancy:

- Small cluster: 1 NCF (no redundancy)

- Medium cluster: 6 NCFs (5+1)

- Large cluster: 11 NCFs (10+1)

For non-blocking traffic, we recommend configuring the following number of minimum NCFs:

- 1 - for CL-32 using NCP-40C model types. Available range 1-2.

- 2 - for CL-48 using NCP-40C model types. Available range 1-3.

- 3 - for CL-49 using NCP-64X12C-S and NCP-40C and NCP-10CD model types. Available range 1-3.

- 3 - for CL-51 using NCP-36CD-S model types. Available range 1-3.

- 3 - for CL-64 using NCP-40C model types. Available range 1-4.

- 4 - for CL-76 using NCP-36CD-S model types. Available range 1-5.

- 5 - for CL-86 using NCP-64X12C-S and NCP-40C and NCP-10CD model types. Available range 1-6.

- 5 - for CL-96 using NCP-40C model types. Available range 1-7.

- 8 - for CL-153 using NCP-36CD-S model types. Available range 1-10.

- 10 - for CL-192 using NCP-40C model types. Available range 1-13.

- 32 - for CL-409 using NCP-36CD-S model types. Available range 1-36.

- 18 - for AI-768-400G-1 using NCP-36CD-S model types. Available range 0-20.

- 2  - for AI-216-800G-2 using NCP-38E model types. Available range 0-2.

- 32 - for AI-8192-400G-2 using NCP-38E model types. Available range 0-36.

- 1  - for AI-72-800G-2 using NCP-38E model types. Available range 0-1.

- 18 - for AI-2304-800G-2 and AI-2016-800G-2 using NCP-38E model types. Available range 0-20.

- 5 - for AI-576-800G-2 using NCP-38E model types. Available range 0-5.

- 9 - for AI-1152-800G-2 using NCP-38E model types. Available range 0-10.

To configure the minimum number of NCF nodes that must be active for all the NCPs in the cluster to be active:

**Command syntax: fabric-min-ncf [fabric-min-ncf]**

**Command mode:** config

**Hierarchies**

- system

**Note**
- This command is not applicable to a standalone NCP.

- This configuration applies to system cluster types, for standalone, configuration is not available.

- Validation – number of fabric-min-ncf cannot be higher than supported ncfs in cluster (per cluster type)

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| fabric-min-ncf | The number of active NCF nodes below which the cluster NCPs will become          | 0-36  | 1       |
|                | unavailable. The value cannot be higher than the number of supported NCFs in the |       |         |
|                | cluster.                                                                         |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# fabric-min-ncf 10
    dnRouter(cfg-system)#


**Removing Configuration**

To revert the system fabric-min-ncf to its default value:
::

    dnRouter(cfg-system)# no fabric-min-ncf

**Command History**

+---------+------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                         |
+=========+======================================================================================================+
| 11.2    | Command introduced                                                                                   |
+---------+------------------------------------------------------------------------------------------------------+
| 13.3    | Changed the defaults from 6 for medium cluster and 11 for large clusters to 1 for both cluster types |
+---------+------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for CL-32, CL-48, and CL-64                                                            |
+---------+------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for CL-51 and CL-76                                                                    |
+---------+------------------------------------------------------------------------------------------------------+
| 18.1    | Added support for CL-153                                                                             |
+---------+------------------------------------------------------------------------------------------------------+
| 19.10   | Added support for AI cluster formations                                                              |
+---------+------------------------------------------------------------------------------------------------------+
```

## system ipv4-fragmentation-in-transit admin-state
```rst
system ipv4-fragmentation-in-transit admin-state
------------------------------------------------

**Minimum user role:** operator

Use this command to fragment transit data packets when the MTU on the ingress L3 interface is larger than the MTU on the egress L3 interface.

Enables/disables IPv4 packet fragmentation:

**Command syntax: ipv4-fragmentation-in-transit admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ipv4


.. **Note**

	- No command reverts the ipv4 fragmentation admin-state to default.

**Parameter table**

+-------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                                                                                                                    | Range    | Default  |
+=============+================================================================================================================================================================================================================================+==========+==========+
| admin-state | The administrative state of the IPv4 fragmentation feature. When enabled, data packets larger than the size allowed by the egress port will be fragmented. When disabled, packets larger than the allowed MTU will be dropped. | Enabled  | Disabled |
|             |                                                                                                                                                                                                                                | Disabled |          |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ipv4-fragmentation-in-transit admin-state enabled

	dnRouter(cfg-system)# ipv4-fragmentation-in-transit admin-state disabled


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no ipv4-fragmentation-in-transit admin-state

.. **Help line:** Enable/disable IPv4 packet fragmentation in transit.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

```

## system login banner
```rst
system login banner 
--------------------

**Minimum user role:** operator

You can define a customized banner to be displayed before the username and password login prompts.

To define a login banner:

**Command syntax: banner [banner-message]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command removes the login banner

**Parameter table**

+----------------+--------------------------------------------------------------------------------+
| Parameter      | Description                                                                    |
+================+================================================================================+
| banner-message | Enter text that will appear before the login prompt. Start a new line with \n. |
+----------------+--------------------------------------------------------------------------------+

The banner is displayed when connecting to the NCP using:

- Console

- Telnet

- SSH

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# banner "This is My banner"
	dnRouter(cfg-system-login)# banner "This is My banner '@#$!<>"
	dnRouter(cfg-system-login)# banner "This is My \\ \" banner"

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no banner

.. **Help line:** Configure system login banner

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 5.1.0   | Command introduced                                        |
+---------+-----------------------------------------------------------+
| 6.0     | Applied new hierarchy                                     |
+---------+-----------------------------------------------------------+
| 13.1    | Added banner display when connected via the console port. |
+---------+-----------------------------------------------------------+


```

## system login ipmi
```rst
system login ipmi
-----------------

**Minimum user role:** operator

To configure login parameters (user and password) for DNOS ipmi interfaces:

**Command syntax: ipmi**

**Command mode:** config

**Hierarchies**

- system login


**Note**

- Notice the change in prompt

.. - no command sets the values to default


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no ipmi

.. **Help line:** configure login parameters for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


```

## system login ipmi user password
```rst
system login ipmi user password
-------------------------------

**Minimum user role:** operator

To configure an encrypted password for DNOS ipmi interfaces.

**Command syntax: password** [password]

**Command mode:** config

**Hierarchies**

- system login ipmi


**Note**

- This command may also be used to change the password for existing users. Typically, when you want to create a new user with a new password, you would use the clear password option.

- You need an admin or techsupport role to change the password for dnroot.

.. - One line command allows to enter password in encrypted format only.

	- It is not possible to remove password

	- If password with no value is entered, clear text password is requested with double confirmation. Clear password size is limited by 16 characters

	**Validation:**

	- Only user with admin/techsupport role can edit passwords for users with privilege administrator

	- Clear passwords must be at least eight (8) and maximum sixteen (16) characters in length.

	- Clear passwords must include at least one alpha character.

	- Clear passwords must include at least one numeric character.

	- User should not be able to type a special characters that may have command function.

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                  | Range                                                                                                             |
+===========+==============================================================================================+===================================================================================================================+
| password  | Enter a clear text password for accessing DNOS IPMI.                                         | Clear passwords must include the following:                                                                       |
|           | If you do not enter a password, you will be prompted to enter a clear password for the user. | Minimum 8 characters, maximum 16.                                                                                 |
|           |                                                                                              | Must include at least one alpha character.                                                                        |
|           |                                                                                              | Must include at least one numeric character.                                                                      |
|           |                                                                                              | Special characters that have a command function (' ', '\n') are not allowed.                                      |
+-----------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)# password enc-!@#$%

	dnRouter(system-login-ipmi-user1)# password
	Enter password:
	Enter password for verification:




.. **Help line:** configure password for DNOS ipmi user.

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 10.0    | Command introduced                                      |
+---------+---------------------------------------------------------+
| 13.0    | Replaced hashed password with encrypted password        |
+---------+---------------------------------------------------------+
| 15.0    | Updated minimum length of password to six characters    |
+---------+---------------------------------------------------------+
| 19.3    | Updated minimum length of password to eight characters  |
+---------+---------------------------------------------------------+


```

## system login ipmi user privilege
```rst
system login ipmi user privilege 
--------------------------------

**Minimum user role:** operator

To configure the privilege level for an IPMI user:

**Command syntax: privilege [level]**

**Command mode:** config

**Hierarchies**

- system login ipmi user


**Note**

- To change the privilege level of an administrator, you need an admin or a techsupport role.

- You cannot change the privilege level for "dnroot".

.. - The full list of IPMI commands and the minimum privilege level per each command are specified by Appendix G in IPMIv2.0 specifciation document.

	**Validation:**

	- only user with admin/techsupport role can edit privilege for users with privilege administrator

	- privilege level for "dnroot" user cannot be changed

	- privilege level is a mandatory parameter, commit will fail if user will be created without setting privilege level

**Parameter table**

+-----------+--------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                    | Range         | Default |
+===========+================================================================================+===============+=========+
| level     | The privilege level for the IPMI user, as defined by the ipmiv2 specification. | callback      | \-      |
|           |                                                                                | user          |         |
|           |                                                                                | operator      |         |
|           |                                                                                | administrator |         |
+-----------+--------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)# privilege USER

	


.. **Help line:** configure privilege level for ipmi user.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


```

## system login ipmi user
```rst
system login ipmi user 
-----------------------

**Minimum user role:** operator

To configure credentials for DNOS ipmi interfaces.

**Command syntax: ipmi user [user-name]**

**Command mode:** config

**Hierarchies**

- system login ipmi


**Note**

- Notice the change in prompt

- If the user-name does not exist, a new user will be created.

.. - If user name does not exist, new user is created

	- The following default users should exist:

	   - dnroot - privilege administrator

	- "no ipmi" command sets the values to default

	- "no users" removes all user-names for IPMI except "dnroot"

	- "no user <user-name> remove specific user-name for IPMI

	- typed password is not presented to the user


	**Validation:**

	- default local user cannot be deleted

	- default local user privilege cannot be changed

	- administrator users IPMI users can only be created/changed deleted by admin/techsupport users

	- default local users password can ONLY be changed according to the following-rules

	   - dnroot - can be changed by admin/techsupport

	- User must configured with a password, if user has been configured without password, commit will fail

**Parameter table**

+-----------+---------------------------------------------------------+--------+
| Parameter | Description                                             | Range  |
+===========+=========================================================+========+
| user-name | Enter a user-name for accessing the DNOS IPMI interface | String |
+-----------+---------------------------------------------------------+--------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)#
	

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-ipmi)# no user user1
	dnRouter(cfg-system-login-ipmi)# no user
	dnRouter(cfg-system-login)# no ipmi

.. **Help line:** configure credentials for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


```

## system login ncm user password
```rst
system login ncm user password 
------------------------------

**Minimum user role:** operator

The password is a mandatory parameter for authentication. When creating new users, you must configure them with a password, otherwise the commit will fail. Once a password is configured, it cannot be deleted, only changed.

To set up a password or change an existing password for a user:

**Command syntax: password** {[encrypted-password] \| [password]}

**Command mode:** config

**Hierarchies**

- system login ncm user


**Note**

- Only users with an admin or techsupport role can edit passwords for users. Admins cannot edit the password for users with a techsupport role.

- Special characters that have a command function (; & | ' ") are not allowed.

- Clear passwords must include the following:

- Minimum 6 characters, maximum 16.

- Must include a combination of at least 2 of the following groups: letters, numbers, special characters (e.g.@#$!)

- Must not contain a sequence of three or more characters from the previous password.

- The password must be different from the user-id (except for the default local user passwords)

.. - One line command allows to enter password in encrypted format only.

	- It is not possible to remove password

	- If password with no value is entered, clear text password is requested with double confirmation

	**Validation:**

	- only DNOS user with admin/techsupport role can edit passwords for users

	- passwords length will be between 8-16 characters. operator which will insert other length will get an error message "passwords length should be between 8-16 characters"

	- clear passwords validations:

	   - clear passwords must include characters from at least two (2) of these groupings: alpha, numeric, and special characters. operator which will insert other length will get an error message "passwords must include characters from at least 2 of these groupings: alpha, numeric, and special characters"

	   - User should not be able to type a special characters that may have command function.

	   - clear passwords must not be the same as the user name with which they are associated.

**Parameter table**

+--------------------+--------------------------------+--------+---------+
| Parameter          | Description                    | Range  | Default |
+====================+================================+========+=========+
| encrypted-password | The new password for the user. | String | \-      |
+--------------------+--------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1	
	dnRouter(system-login-ncm-user1)# password $6$qOB4/fW9kH0
	
	dnRouter(system-login-ncm-user1)# password
	Enter password:
	Enter password for verification:
	
	


.. **Help line:** configure password for NCM user.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+


```

## system login ncm user role
```rst
system login ncm user role
--------------------------

**Minimum user role:** operator

To configure the user's role:

**Command syntax: role [role]**

**Command mode:** config

**Hierarchies**

- system login ncm user


.. **Note**

	The following roles exist by default:

	-  admin - has full control

	-  viewer - able to use "show" commands only

	**Validation:**

	- only DNOS admin and techsupport role users can define roles of ncm users

	- It is not possible to configure new ncm roles

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                                                                                                       | Range       | Default |
+===========+===================================================================================================================================================+=============+=========+
| role      | Enter admin/operator/viewer (lowercase). The default is "viewer". If you do not assign a role, the user will be assigned the default viewer role. | techsupport | viewer  |
|           |                                                                                                                                                   | admin       |         |
|           |                                                                                                                                                   | operator    |         |
|           |                                                                                                                                                   | viewer      |         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+-------------+---------+

Roles are used for authorization. After a user is authenticated, the user is granted access depending on his/her assigned role.

The available roles are:

- Techsupport - has full control

- Admin - has full control

- Operator - has full control, except request system restart commands

- Viewer - can execute show commands only

The minimum user role required for each command is specified for every command in this manual, as follows:

The minimum user role required for this command:

+--------------+----------------------------------------------------------------------+
| User Role    | Description                                                          |
+==============+======================================================================+
| Techsupport  | Only Techsupport can execute the command.                            |
+--------------+----------------------------------------------------------------------+
| Admin        | Administrators and Techsupport can execute the command.              |
+--------------+----------------------------------------------------------------------+
| Operator     | Operators, Administrators, and Techsupport can execute the command.  |
+--------------+----------------------------------------------------------------------+
| Viewer       | Viewers, Operators, and Administrators can execute the command.      |
+--------------+----------------------------------------------------------------------+

- Only DNOS techsupport users can create an NCM techsupport user

- Only users with admin or techsupport roles can change roles of existing users

- A user with an admin role cannot change the role of a user with a techsupport role

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1
	dnRouter(system-login-ncm-user1)# role admin



.. **Help line:** Configure ncm user role

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+


```

## system login ncm user
```rst
system login ncm user 
---------------------

**Minimum user role:** operator

You need a user name and a password to access the NCM. Using this command, you can configure users and passwords directly from the DNOS CLI. When the NCM connects to the cluster, it will synchronize with the allowed users.

You need an admin/techsupport privileges to create or change a user with an admin role.

You need an techsupport privileges to create or change a user with a techsupport role.

To configure a user:

**Command syntax: ncm user [user-name]**

**Command mode:** config

**Hierarchies**

- system login

**Note**

- Notice the change in prompt

.. - If user name does not exist, new user is created

	- The following default users should exist:

	- dnrootncm - privilege administrator

	- "no user <user-name> remove specific user-name from NCM

	- typed password is not presented to the user


	**Validation:**

	- default user cannot be deleted

	- default user privilege cannot be changed

	- "admin" will not be an available user-name - operator which will type "admin" will get an error message "unsupported user name"

	- admin/viewer role users can only be created/changed deleted by DNOS admin/techsupport users

	- default users password can ONLY be changed according to the following-rules

	- dnrootncm - can be changed by DNOS admin/techsupport user

	- User must configured with a password, if user has been configured without password, commit will fail

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                                                                       | Range  | Default |
+===========+===================================================================================================================================================+========+=========+
| user-name | Enter a user-name for accessing the NCM console. If the name doesn't already exist, it will be created and you will enter its configuration mode. | String | \-      |
|           | You cannot configure a user named "admin".                                                                                                        |        |         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1
	dnRouter(system-login-ncm-user1)#
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-ncm)# no user user1

.. **Help line:** configure credentials for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+

```

## system login
```rst
system login 
-------------

**Minimum user role:** operator

From the system login hierarchy you can configure new users and login parameters.

To enter system login configuration mode:

**Command syntax: login [parameters]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- You may only create/update parameters of users with an equivalent or lower role level. For example, users with a "techsupport" role can only be created or changed by users with a "techsupport" role; users with an "operator" role can only create or change users with "viewer" or "operator" roles; etc.

- Notice the change in prompt

.. - Validation: user must be configured with a password

	- It is not possible to remove password configuration

	- no command removes the user configuration


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# banner This is My banner
	dnRouter(cfg-system-login)# user MyUserName 
	dnRouter(cfg-system-login-MyUserName)#
	

	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no user MyUserName
	dnRouter(cfg-system-login)# no banner

.. **Help line:** Configure system login users

**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 6.0     | Command introduced as part of new hierarchy |
+---------+---------------------------------------------+


```

## system login session-holdoff
```rst
system login session-holdoff
----------------------------

**Minimum user role:** operator

To configure the amount of time that the system will block login attempts after the maximum number of allowed failed attempts is reached:

**Command syntax: session-holdoff [session-holdoff]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command sets the values to default

	- in case maximum number of attempts was tried, the connection should be silently rejected.

**Parameter table**

+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                                                                                                   | Range | Default |
+=================+===============================================================================================================================================================+=======+=========+
| session-holdoff | The amount of time (in minutes) to wait after the maximum number of failed login attempts is reached, before the system will allow to attempt to login again. | 3..15 | 10      |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-holdoff 5
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-holdoff

.. **Help line:** configure holdoff time in case the maximum number of failed login retries has been reached.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

```

## system login session-retry
```rst
system login session-retry
--------------------------

**Minimum user role:** operator

To configure the number of allowed failed login attempts:

**Command syntax: session-retry [session-retry]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command sets the values to default

	- in case maximum number of attempts was tried, the connection should be silently rejected

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                                                                                                                                                                      | Range | Default |
+===============+==================================================================================================================================================================================================================================+=======+=========+
| session-retry | The number of consecutive login failed attempts allowed. If the maximum number of failed login attempts has been reached, the system will block further attempts for a configured time period. See system login session-holdoff. | 1..10 | 8       |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-retry 10 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-retry

.. **Help line:** configure maximum number of failed login retries.

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 6.0     | Command introduced    |
+---------+-----------------------+
| 13.0    | Changed default value |
+---------+-----------------------+

```

## system login session-timeout
```rst
system login session-timeout
----------------------------

**Minimum user role:** operator

CLI sessions are terminated when no activity is done for a predefined amount of time. If you start a prolonged action in the CLI foreground, the idle timer stops, and will restart when the foreground process ends and control is returned to the shell prompt.

The actions that cause the idle timer to stop are:

- All transaction commands (e.g. commit, rollback)

- Load

- Save

- All request commands

- All run commands, except run shell, for which a fixed timeout is set to 15 minutes.

To configure the maximum allowed idle-time before the CLI session is disconnected:

**Command syntax: session-timeout [interval]**

**Command mode:** config

**Hierarchies**

- system login

.. **Note**

	- no command sets the values to default

	- interval=0 means no timeout (inifinite session)

	- if user start another program to run in the foreground of the CLI, the idle timer control is stopped from being computed. The calculation of idle time of the CLI session is restarted only after the foreground process exits and the control is returned to the shell prompt.

	Relevant commands are:

	- All transactions commands (commit, rollback)

	- Load

	- Save

	- All request commands

	- All run commands except "run shell"

	- For run shell commands, timeout is fixed for 15 minutes for idle session

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                | Range | Default |
+===========+============================================================================================================================+=======+=========+
| interval  | The amount of time (in minutes) allowed for a CLI session to be idle (no keyboard input) before disconnecting the session. | 0..90 | 30      |
|           | An interval with value 0 means no timeout. The session will continue indefinitely.                                         |       |         |
+-----------+----------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-timeout 30
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-timeout

.. **Help line:** configure maximum time allowed for CLI session to be idle before it is disconnected. Idle is a session with no input from user via keyboard.

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 6.0     | Command introduced                      |
+---------+-----------------------------------------+
| 10.0    | Range changed from minimum 15 min to 0. |
+---------+-----------------------------------------+


```

## system login shell-timeout
```rst
system login shell-timeout
----------------------------

**Minimum user role:** operator

The shell-timeout command sets the maximum time that a connection with the HostOS shell is allowed to be idle before it is disconnected. "Idle" refers to a session with no keyboard input from the user. The HostOS shell of the NCC/NCP/NCF may be accessed via Console port, IPMI SoL, or using the SSH protocol.

To configure a timeout for idle connections with the hostOS:

**Command syntax: shell-timeout [interval]**

**Command mode:** config

**Hierarchies**

- system 

.. **Note**

	- no command sets the values to default

	- interval=0 means no timeout (inifinite session)

	- access to the HostOS shell of NCC/NCP/NCF node can be acheived via console port, IPMI SoL or via SSH protocol. 

	- this command has no effect on the timeout for NCM sessions

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                          | Range | Default |
+===========+======================================================================================================================================+=======+=========+
| interval  | The maximum amount of time (in minutes) in which a session with the HostOS of the NCC/NCP/NCF can be idle before it is disconnected. | 0..90 | 30      |
|           | A value of 0 means no timeout (the session can be idle indefinitely).                                                                |       |         |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# shell-timeout 30
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no shell-timeout

.. **Help line:** configure maximum time allowed for connection to HostOS shell to be idle before it is disconnected. Idle is a session with no input from user via keyboard. Access to HostOS shell of NCC/NCP/NCF may be done either via SoL/Console or via SSH. 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+


```

## system login techsupport-login
```rst
system login techsupport-login
------------------------------

**Minimum user role:** operator

To allow or deny login access to users with a techsupport role:

**Command syntax: techsupport-login admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system login 


.. **Note**

	- no command sets the values to default

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                                                         | Range    | Default  |
+=============+=====================================================================================================================================================================+==========+==========+
| admin-state | The administrative state of the techsupport login. When enabled, login access will be granted to users with a "techsupport" role. Otherwise, access will be denied. | Enabled  | Disabled |
|             |                                                                                                                                                                     | Disabled |          |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# techsupport-login admin-state enabled
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no techsupport-login

.. **Help line:** allow or deny login for users with techsupport role.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


```

## system login user description
```rst
system login user description
-----------------------------

**Minimum user role:** operator

To set an optional description for the user:

**Command syntax: user [user-name]** description [description]

**Command mode:** config

**Hierarchies**

- system login


**Note**

- A techsupport role cannot change the description of a user with an admin role.

.. - no command removes the user description

	- If user name does not exist, new user is created

	**Validation:**

	- only users with role admin/techsupport, can edit other local users

	- user with role admin, cannot edited by user with techsupport role

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Parameter   | Description                                                                                                                            |
+=============+========================================================================================================================================+
| description | Provide a description for the user.                                                                                                    |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |
|             | ... description "My long description"                                                                                                  |
|             | ... description My_long_description                                                                                                    |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# description MyDescription

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName)# no description

.. **Help line:** Configure login user description

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+


```

## system login user key ssh-rsa file
```rst
system login user key ssh-rsa file
--------------------------------------

**Minimum user role:** admin

Public key authentication is step forward to the security improvement of password-protected systems. It provides a cryptographic strength that is considerably stronger than conventional passwords (even if they are extremely long or complicated). With SSH, authentication using a public key dismisses the need of users creating and remembering complex passwords.

You can use this command to import an SSH public key from a file located in the ssh-keys directory. You can then login to the CLI and NETCONF using the matching private key.

To import a public key from a file for a user:

**Command syntax: user [user-name]** key ssh-rsa file [filename]

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- The public key file must be located in the NCC ssh-keys directory and must contain one line in the format "ssh-rsa <base64-encoded key> [optional comment]". Empty lines and lines beginning with '#' will be ignored.

- You are required to have a password or an SSH public key, but if both exist you can use either to authenticate.

.. - no command removes the key.

	- User that has both password and SSH key may authenticate with either.

	**Validation:**

	- User must have either a password or an SSH public key or both.

	- The file must be found in NCC ssh-keys directory.

	- The file must contain one line in the format "ssh-rsa <base64-encoded key> [optional comment]". Empty lines and lines starting with '#' are ignored.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| filename  | The name of the file where the public key is located. | String | \-      |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# key ssh-rsa file john_id_rsa.pub


**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName)# no key

.. **Help line:** Configure SSH user public key for key-based login to CLI and NETCONF.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## system login user key ssh-rsa terminal
```rst
system login user key ssh-rsa terminal
--------------------------------------

**Minimum user role:** operator

Public key authentication is step forward to the security improvement of password-protected systems. It provides a cryptographic strength that is considerably stronger than conventional passwords (even if they are extremely long or complicated). With SSH, authentication using a public key dismisses the need of users creating and remembering complex passwords.

Once you have generated a private-public key (outside of DNOS), the public key needs to be verified by DNOS to be a valid SSH RSA public key. You can then login to the CLI and NETCONF using the matching private key.

To configure a user public key from a terminal:

**Command syntax: user [user-name]** key ssh-rsa terminal [public-key-string]

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- If a username doesn't exist, a new user will be created.

- You are required to have a password or an SSH public key, but if both exist you can use either to authenticate.

.. - no command removes the key.

	- If user name does not exist, new user is created.

	- User that has both password and SSH key may authenticate with either.

	**Validation:**

	- User must have either a password or an SSH public key or both.

**Parameter table**

+-------------------+-------------------------------------------------+--------+---------+
| Parameter         | Description                                     | Range  | Default |
+===================+=================================================+========+=========+
| public-key-string | The SSHv2 RSA public key in OpenSSH format:     | String | \-      |
|                   | ssh-rsa <base64-encoded key> [optional comment] |        |         |
+-------------------+-------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# key ssh-rsa terminal "ssh-rsa AAAAB3NzaC1yc2EAAA...D4I7SFrQ== MyUserName@My-MacBook-Pro"
	dnRouter(cfg-system-login)# user AnotherUser
	dnRouter(cfg-system-login-AnotherUser)# key ssh-rsa terminal "ssh-rsa AAAAFGbnj1yc2EAAA...D4I8KJd6=="


**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName)# no key

.. **Help line:** Configure SSH user public key for key-based login to CLI and NETCONF.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## system login user password
```rst
system login user password
--------------------------

**Minimum user role:** admin

The password is a mandatory parameter for authentication. When creating new users, you must configure them with a password, otherwise the commit will fail. Once a password is configured, it cannot be deleted, only changed.

To set up a password or change an existing password for a user:

**Command syntax: user [user-name]** password {[hashed-password] \| [password]}

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- Only users with an admin or techsupport role can edit passwords for users. Admins cannot edit the password for users with a techsupport role.

- Special characters that have a command function (' ') are not allowed.

- You are required to have a password or an SSH public key.

If you enter the password command without a hashed-password, you will be prompted to enter a clear text password with double confirmation.
Clear passwords must include the following:

- Clear passwords must be at least eight (8) characters in length.

- Must include a combination of at least 2 of the following groups: letters, numbers, special characters (e.g.@#$!)

- The password must be different from the user-id (except for the default local user passwords)

.. - One line command allows to enter password in SHA-512 format only.

	- no command removes the password.

	- If password with no value is entered, clear text password is requested with double confirmation

	**Validation:**

	- User must have either a password or an SSH public key or both.

	- only user with admin/techsupport role can edit passwords for users

	- user with role admin, cannot edited password for user in techsupport role

	- Clear passwords must be at least eight (8) characters in length.

	- Clear passwords must include characters from at least two (2) of these groupings: alpha, numeric, and special characters.

	- User should not be able to type a special characters that may have command function.

	- Clear passwords must not be the same as the userid with which they are associated, except the default local user passwords.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------+
| Parameter       | Description                                                                                |
+=================+============================================================================================+
| hashed-password | Enter the user's existing password. The password is inserted as a hashed string (SHA-512). |
+-----------------+--------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName2
	dnRouter(cfg-system-login-MyUserName2)# password $6$qOB4/fW9kH0yWvta$MF4iWvbAztfrbOBKAQLZ7GCFO7wVhUY4GoILSs/4HtG1QP8TjzPiQQ33B0J/t3ReeEHARLNR3QnMzFowTgETR.

	dnRouter(cfg-system-login-MyUserName2)# password
	Enter password:
	Enter password for verification:



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName2)# no password

.. **Help line:** Configure user password

**Command History**

+---------+--------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                     |
+=========+==================================================================================================+
| 5.1.0   | Command introduced                                                                               |
+---------+--------------------------------------------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                                                            |
+---------+--------------------------------------------------------------------------------------------------+
| 10.0    | Applied new hierarchy                                                                            |
+---------+--------------------------------------------------------------------------------------------------+
| 11.2    | Added note about forbidden special characters.                                                   |
+---------+--------------------------------------------------------------------------------------------------+
| 15.0    | Added the option to remove the password and updated minimum length of password to six characters |
+---------+--------------------------------------------------------------------------------------------------+
| 19.1    | Updated minimum length of password to eight characters                                           |
+---------+--------------------------------------------------------------------------------------------------+
```

## system login user role
```rst
system login user role
----------------------

**Minimum user role:** operator

Only users with admin or techsupport role can change roles of existing users. Users with an admin role cannot change the role of a user with a techsupport role.

More complex profiles can be set by combining roles with groups in the TACACS+ server. For more details, see system aaa-server.

Local users can only be configured with Admin, Operator, or Viewer roles. It is not possible to create new local roles.

To assign a role to a local user:

**Command syntax: user [user-name]** role [role]

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command reverts the role to its default value

	The following roles exist by default:

	- admin - has full control

	- operator - has full control with several exceptions

	- viewer - able to use "show" commands only

	- If user name does not exist, new user is created

	**Validation:**

	- only admin and techsupport role users can change roles of existing users

	- user with role admin, cannot change role of techsupport role user

	- TACACS can be configured with any of the default system roles.

	- Local users can be configured only with admin/operator/viewer. It is not possible to configure new local roles


**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                       |
+===========+===================================================================================================================================================+
| role      | Enter admin/operator/viewer (lowercase). The default is "viewer". If you do not assign a role, the user will be assigned the default viewer role. |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+

Roles are used for authorization. After a user is authenticated, the user is granted access depending on his/her assigned role.

The available roles are:

- Techsupport - has full control

- Admin - has full control

- Operator - has full control, except request system restart commands

- Viewer - can execute show commands only

The minimum user role required for each command is specified for every command in this manual, as follows:

The minimum user role required for this command:

+--------------+----------------------------------------------------------------------+
| User Role    | Description                                                          |
+==============+======================================================================+
| Techsupport  | Only Techsupport can execute the command.                            |
+--------------+----------------------------------------------------------------------+
| Admin        | Administrators and Techsupport can execute the command.              |
+--------------+----------------------------------------------------------------------+
| Operator     | Operators, Administrators, and Techsupport can execute the command.  |
+--------------+----------------------------------------------------------------------+
| Viewer       | Viewers, Operators, and Administrators can execute the command.      |
+--------------+----------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName 
	dnRouter(cfg-system-login-MyUserName)# role admin
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-MyUserName)# no role

.. **Help line:** Configure user role

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+


```

## system login user
```rst
system login user 
------------------

**Minimum user role:** operator

You can configure users locally and/or on a TACACS+.RADIUS server. If both local and remote authentication types are set, local authentication, via a password stored on the device, will be used only if the authentication from the TACACS+ or RADIUS authentication server is not available or fails.

The following sections describe how to configure users locally using the DNOS CLI. For instructions on configuring users on the TACACS+.RADIUS server, refer to the TACACS+/RADIUS documentation.

The following default users are mandatory:

- dnroot - with role admin - the default password can only be changed by users with "admin" or "techsupport" roles

- dntechsupport - with role techsupport - the default password can only be changed by users with "techsupport" role

- Users with "techsupport" role can only be created, changed, or deleted by other users with a "techsupport" role

To create a local user and/or enter a user's configuration mode:

**Command syntax: user [user-name]**

**Command mode:** config

**Hierarchies**

- system login


**Note**

- Notice the change in prompt.

- Default local users cannot be deleted or changed.

.. - If user name does not exist, new user is created

	- no command removes the user configuration. By default new user name get "Viewer" role.

	- User must be configured with a password or with an SSH key or with both, otherwise commit will fail.

	- The following default users should exist:

	- dnroot - role admin

	- dntechsupport - role techsupport

	- default local users cannot be deleted

	- default local users role cannot be changed

	- techsupport role user can only be created/changed/deleted by techsupport

	- admin/operator/viewer role users can only be created/changed deleted by admin/techsupport users

	- default local users password can ONLY be changed according to the following-rules

	- dnroot - can be changed by admin/techsupport

	- dntechsupport - can be changed by techsupport

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                                               |
+===========+===========================================================================================================================================================================+
| user-name | The user identifier. This is a mandatory parameter and it must be unique in the system. The user name must have a minimum of 2 characters and a maximum of 20 characters. |
|           | Allowed characters: a-z, A-Z, 0-9, - (hyphen), _ (underscore), ~ (tilda)                                                                                                  |
|           | The first character must be a letter, a-z or A-Z.                                                                                                                         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

If the user name does not exist, it will be created.

The user must be configured with a password or with an SSH key, or with both. If it isn't, the commit will fail. See system login user password.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no user MyUserName

.. **Help line:** Configure login user name

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                          |
+---------+----------------------------------------------------------------+
| 10.0    | Added limitations on creating/updating users depending on role |
|         | Applied new user hierarchy                                     |
+---------+----------------------------------------------------------------+


```

## system management
```rst
system management 
------------------

**Minimum user role:** operator

To enter the system management configuration mode:

**Command syntax: management**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt.

.. - "no management" - remove all configuration under management


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management 
	dnRouter(cfg-system-mgmt)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no management


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


```

## system management vrf
```rst
system management vrf  
---------------------

**Minimum user role:** operator

To enter management vrf configuration level:

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- system management


**Note**

- Notice the change in prompt

.. - "no static" removes all configuration from management vrf

**Parameter table**

+-----------+-----------------------------+-----------------------------------+---------+
| Parameter | Description                 | Range                             | Default |
+===========+=============================+===================================+=========+
| vrf       | Displays the management vrf | mgmt0, mgmt-ncc-0, mgmt-ncc-1     | \-      |
+-----------+-----------------------------+-----------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system 
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)#


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-mgmt)# no mgmt0


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


```

## system management vrf static address-familiy
```rst
system management vrf static address-familiy
--------------------------------------------

**Minimum user role:** operator

To configure static routes for out-of-band management mgmt vrfs. These vrfs are not part of any traffic forwarding vrf:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- system management static


**Note**

- Notice the change in prompt

.. - "no [address-family]" removes all static routes from the specified address-family

**Parameter table**

+----------------+----------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                | Range | Default |
+================+============================================================================+=======+=========+
| address-family | Enters the address-family for which to configure management static routes. | IPv4  | \-      |
|                |                                                                            | IPv6  |         |
+----------------+----------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static 
	dnRouter(cfg-system-mgmt-vrf-static)# address-family ipv4
	dnRouter(cfg-mgmt-vrf-static-ipv4)#

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static 
	dnRouter(cfg-system-mgmt-vrf-static)# address-family ipv6
	dnRouter(cfg-mgmt-vrf-static-ipv6)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-mgmt-vrf-static)# no address-family ipv4 


**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Command syntax updated |
+---------+------------------------+


```

## system management vrf static address-family route next-hop
```rst
system management static address-family route next-hop
------------------------------------------------------

**Minimum user role:** operator

Configure a static route for the mgmt0 interface. mgmt0 is the out-of-band management interface and is not part of any traffic forwarding VRF.

To configure a static route for the OOB management interface (mgmt0):

**Command syntax: route [ip-prefix] next-hop [gateway]**

**Command mode:** config

**Hierarchies**

- system management static address-family


**Note**

- Static routes to mgmt0 VRF ignores admin-distance values and all routes will be installed.

.. -  [ip-prefix] & [gateway] address type must match the route ip address

	-  "no [ip-prefix]" removes all static routes with [prefix] destination.

	-  "no [ip-prefix] next-hop [gateway]" removes the specific prefix&gateway entry.

	-  Static route to mgmt0 VRF ignores admin-distance value. All routes will be installed

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| Parameter   | Description                                                                                                                                                                                                                                        | Range             | Default |
+=============+====================================================================================================================================================================================================================================================+===================+=========+
| ip-prefix   | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                               | A.B.C.D/x         | \-      |
|             | In IPv4-unicast configuration mode you can only set IPv4 destination prefixes and in IPv6-unicast configuration mode you can only set IPv6 destination prefixes.                                                                                   | x:x::x:x/x        |         |
|             | When setting a non /32 prefix, the route installed is the matching subnet network address. For example, for route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same applies for IPv6 prefixes. |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| description | Provide a description for the route.                                                                                                                                                                                                               | 1..255 characters | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example:                                                                                                             |                   |         |
|             | ... description "My long description"                                                                                                                                                                                                              |                   |         |
|             | ... description My_long_description                                                                                                                                                                                                                |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| next-hop    | The gateway IPv4 or IPv6 address for the prefix.                                                                                                                                                                                                   | A.B.C.D           | \-      |
|             | In IPv4-unicast configuration mode you can only set IPv4 next hops and in IPv6-unicast configuration mode you can only set IPv6 next hops.                                                                                                         | x:x::x:x          |         |
|             | You can set multiple IP next hops for the same route.                                                                                                                                                                                              |                   |         |
|             | The next-hop address must be different from the route address.                                                                                                                                                                                     |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)# address-family ipv4
	dnRouter(cfg-vrf-static-ipv4)# route 10.0.0.0/24 next-hop 192.168.0.1
	dnRouter(cfg-vrf-static-ipv4)# route 10.0.0.0/24 next-hop 192.150.1.4

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)# address-family ipv6
	dnRouter(cfg-vrf-static-ipv6)# route 2001:1111::0/124 next-hop abde::1
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-vrf-static-ipv4)# no route 10.0.0.0/24 next-hop 192.150.1.4
	dnRouter(cfg-vrf-static-ipv4)# no route 10.0.0.0/24


**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Command syntax updated |
+---------+------------------------+


```

## system management vrf static
```rst
system management vrf static 
----------------------------

**Minimum user role:** operator

To enter management static route configuration mode:

**Command syntax: static**

**Command mode:** config

**Hierarchies**

- system management


**Note**

- Notice the change in prompt

.. - "no static" removes all static routes from all static routes from management interface


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)#


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-mgmt)# no static



**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Updated command syntax |
+---------+------------------------+

```

## system overview
```rst
System Overview
---------------

System commands enable to configure and edit the server's information. Use the system command to add information about the server/rack. System commands also enable to configure the logging mechanism (see System Logging).
```

## system snmp class-of-service
```rst
system snmp class-of-service
----------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing SNMP sessions:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system snmp

.. **Note**

	- Configuration is global for all outgoing snmp applications (trap-server output etc).

	- Value is the dscp value on the ip header

**Parameter table**

+------------+---------------------------------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                                                 | Range | Default |
+============+=============================================================================================+=======+=========+
| dscp-value | The DSCP value that is used in the IP header to classify the packet and give it a priority. | 0..56 | 16      |
+------------+---------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# class-of-service 54
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no class-of-service

.. **Help line:** Configure system snmp class of service value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


```

## system snmp community access
```rst
system snmp community access
----------------------------

**Minimum user role:** operator

You can set the following access rights for the SNMP community:

Read-only - The device responds to SNMP Get, GetNext, and GetBulk commands

To set the SNMP community authorization:

**Command syntax: access [authorization]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

    - By default, snmp community access is read-only

    - no command reverts the snmp community access to its default value

**Parameter table**

+-----------+---------------------------------------+------------+-----------+
| Parameter | Description                           | Range      | Default   |
+===========+=======================================+============+===========+
| access    | The access rights for SNMP community. | read-only  | read-only |
+-----------+---------------------------------------+------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MyPublicSnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# access read-only

    dnRouter(cfg-system-snmp)# community MyPrivateSnmpCommunity vrf mgmt0
    dnRouter(cfg-system-snmp-community)# access read-write


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-system-snmp-community)# no access

.. **Help line:** Configure system snmp community

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy for SNMP      |
+---------+-------------------------------------+
| 9.0     | Applied new hierarchy for community |
+---------+-------------------------------------+
| 18.1    | Removed the access right read-write |
+---------+-------------------------------------+
```

## system snmp community admin-state
```rst
system snmp community admin-state
---------------------------------

**Minimum user role:** operator

Configure system snmp community admin state.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Note:**

No command reverts the admin-state configuration to its default value

Validation: fail commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.

**Parameter table:**

+--------------+------------------------+---------------+
| Parameter    | Values                 | Default value |
+==============+========================+===============+
| admin-state  | enabled/disabled       | enabled       |
+--------------+------------------------+---------------+

**Example:**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# admin-state disabled

    dnRouter(cfg-system-snmp)# community MyPrivateSnmpCommunity vrf mgmt0
    dnRouter(cfg-system-snmp-community)# admin-state disabled

    dnRouter(cfg-system-snmp)# community MyPublicSnmpCommunity vrf my_vrf
    dnRouter(cfg-system-snmp-community)# admin-state enabled


**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 16.2    | Command introduced                    |
+---------+---------------------------------------+



```

## system snmp community client-list
```rst
system snmp community client-list
---------------------------------

**Minimum user role:** operator

A client-list is a group of clients that are provided with authorization to access the device. You can configure multiple client-lists for an SNMP community. By default an SNMP community has open access to all clients (0.0.0.0/0).

To configure a client-list:

**Command syntax: client-list [network-address]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

	- By default, snmp community has open access to all clients(0.0.0.0/0 or the IPv6 equivalent ::/0)

	- It is possible to configure multiple clients for an SNMP community per vrf

	- no command removes a specific / all clients for a given snmp community

**Parameter table**

+-------------+-------------------------------------------------------------------------------------------------+-----------+---------+
| Parameter   | Description                                                                                     | Range     | Default |
+=============+=================================================================================================+===========+=========+
| client-list | A group of clients to add to the SNMP community.                                                | A.B.C.D/x | \-      |
|             | You can configure multiple clients for an SNMP community.                                       | x:x::x:x  |         |
|             | By default an SNMP community has open access to all clients (0.0.0.0/0 or IPv6 equivalent ::/0) |           |         |
+-------------+-------------------------------------------------------------------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
	dnRouter(cfg-system-snmp-community)# client-list 192.168.0.0/24
	dnRouter(cfg-system-snmp-community)# client-list 172.17.0.0/16
	dnRouter(cfg-system-snmp-community)# client-list 2001:db8:2222::/48
	dnRouter(cfg-system-snmp-community)# client-list 2001:ab12::1/128
	


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-community)# no client-list
	dnRouter(cfg-system-snmp-community)# no client-list 172.17.0.0/16
	dnRouter(cfg-system-snmp-community)# no client-list 2001:db8:2222::/48

.. **Help line:** Configure system snmp community

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 5.1.0   | Command introduced                    |
+---------+---------------------------------------+
| 6.0     | Applied new hierarchy for SNMP        |
+---------+---------------------------------------+
| 9.0     | Applied new hierarchy for community   |
+---------+---------------------------------------+
| 15.1    | Added support for IPv6 address format |
+---------+---------------------------------------+


```

## system snmp community
```rst
system snmp community
---------------------

**Minimum user role:** operator

An SNMP community is the grouping of an SNMP server with its authorized SNMP clients. You can define the relationship that the device has with the SNMP server by configuring SNMP community properties.

To configure community properties:

**Command syntax: community [community] vrf [vrf-name]** parameter [parameter-value]

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- SNMP community is a v1/v2c concept and is not related to v3.

- Notice the change in prompt from dnRouter(cfg-system-snmp)# to dnRouter(cfg-system-snmp-community)# (SNMP community configuration mode).

- User can configure multiple snmp communities per VRF

Validations :
    - Only 2 in-band VRFs and up to 1 out-of-band VRF are allowed to be in admin-state enabled:
        - VRF default
        - Single non-default VRF
        - VRF mgmt0
    - In case snmp community is configured with non-default VRF and a user is trying to delete the non-default VRF, the commit will fail on validation.
    - Up to 10 snmp servers are allowed to be configured in total.

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+
| Parameter | Description                                                                                                           | Range                      | Default |
+===========+=======================================================================================================================+============================+=========+
| community | The name for the SNMP community                                                                                       | string                     | \-      |
+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+
| vrf-name  | Defines whether the client-list attachment to the snmp-server is via in-band (default VRF, or out-of-band (mgmt0 VRF) | default - in-band          | \-      |
|           |                                                                                                                       | non-default-vrf - in-band  |         |
|           |                                                                                                                       | mgmt0- out-of-band         |         |
+-----------+-----------------------------------------------------------------------------------------------------------------------+----------------------------+---------+

The following are the parameters that you can set for each community:

- system snmp community view

- system snmp community access

- system snmp community client-list

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# view MySnmpView
    dnRouter(cfg-system-snmp-community)# access read-only
    dnRouter(cfg-system-snmp-community)# clients 192.168.0.0/24
    dnRouter(cfg-system-snmp-community)# clients 172.17.0.0/16
    dnRouter(cfg-system-snmp-community)# clients 2001:db8:2222::/48
    dnRouter(cfg-system-snmp-community)# access read-write

    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf my_vrf
    dnRouter(cfg-system-snmp-community)# view MySnmpView1
    dnRouter(cfg-system-snmp-community)# access read-only
    dnRouter(cfg-system-snmp-community)# clients 192.168.1.0/24
    dnRouter(cfg-system-snmp-community)# clients 172.17.1.0/16
    dnRouter(cfg-system-snmp-community)# clients 2001:db8:3333::/48


**Removing Configuration**

To remove the SNMP community configuration:
::

	dnRouter(cfg-system-snmp)# no community MySnmpCommunity vrf default


.. **Help line:** Configure system snmp server

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1.0   | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | no system snmp community command reverts to default configuration. |
|         | Applied new hierarchy for SNMP                                     |
+---------+--------------------------------------------------------------------+
| 9.0     | Applied new hierarchy for community                                |
+---------+--------------------------------------------------------------------+
| 13.1    | Added support for out-of-band community                            |
+---------+--------------------------------------------------------------------+
```

## system snmp community view
```rst
system snmp community view
--------------------------

**Minimum user role:** operator

A view is a collection of MIB object types that you want to group together to restrict or provide access to SNMP objects. For information on configuring SNMP views, see system snmp view.

To configure a view for the community:

**Command syntax: view [view]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

	- An SNMP community can only have 1 view attached

	- no command reverts the snmp view configuration to default config

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                                                                 | Range  | Default     |
+===========+=============================================================================================================+========+=============+
| view      | Select an existing view for the community. For information on configuring SNMP views, see system snmp view. | string | viewdefault |
|           | Only one view is allowed per community.                                                                     |        |             |
+-----------+-------------------------------------------------------------------------------------------------------------+--------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
	dnRouter(cfg-system-snmp-community)# view MySnmpView
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-community)# no view

.. **Help line:** Configure system snmp community view

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy for SNMP      |
+---------+-------------------------------------+
| 9.0     | Applied new hierarchy for community |
+---------+-------------------------------------+


```

## system snmp compatibility-mode cisco
```rst
system snmp compatibility-mode cisco
------------------------------------

**Minimum user role:** operator

To configure the SNMP compatibility mode with Cisco:

**Command syntax: cisco [admin-state]**

**Command mode:** config

**Hierarchies**

- system snmp compatibility-mode

**Parameter table**

+-------------+-------------------------------+--------------+---------+
| Parameter   | Description                   | Range        | Default |
+=============+===============================+==============+=========+
| admin-state | SNMP Cisco compatibility-mode | | enabled    | enabled |
|             |                               | | disabled   |         |
+-------------+-------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)# cisco enabled

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)# cisco disabled


**Removing Configuration**

To revert the SNMP compatibility with Cisco configuration to default:
::

    dnRouter(cfg-system-snmp-compatibility)# no cisco

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
```

## system snmp compatibility-mode
```rst
system snmp compatibility-mode
------------------------------

**Minimum user role:** operator

To configure SNMP compatibility mode:

**Command syntax: compatibility-mode**

**Command mode:** config

**Hierarchies**

- system snmp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)#


**Removing Configuration**

To revert the compatibility-mode configuration to its default value:
::

    dnRouter(cfg-system-snmp)# no compatibility-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
```

## system snmp packet-size
```rst
system snmp packet-size
----------------------------

**Minimum user role:** operator

You can configure the maximum packet size (in bytes) for all outgoing SNMP packets.

**Command syntax: packet-size [packet-size]**

**Command mode:** config

**Hierarchies**

- system snmp 

.. **Note**

	- Configuration is global for all outgoing SNMP responses and traps.

	- Value includes 20 bytes for IPv4 header and 8 bytes for UDP header.

	- 'no' command reverts the value to default.

**Parameter table**

+-------------+----------------------------------------+-----------+---------+
| Parameter   | Description                            | Range     | Default |
+=============+========================================+===========+=========+
| packet-size | The size of the SNMP packet (in bytes) | 100..9300 | 1500    |
+-------------+----------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# packet-size 1000
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no packet-size

.. **Help line:** Configure SNMP maximum outgoing packet size in bytes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system snmp trap
```rst
system snmp trap
----------------

**Minimum user role:** operator

All traps are enabled by default. You can disable a trap, or enable a disabled trap, as follows:

**Command syntax: trap [trap-type] [trap-name] enabled \| disabled**

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- When multiple SNMP servers are configured, all enabled traps are sent to all SNMP servers.

.. - all traps are enabled by default

	- no command removes the trap configuration - essentially enables the trap

	- trap-type includes all supported trap-names children (see supported snmp suppressed traps)

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                      |
+====================+==================================================================================================================================================+
| trap-type          | Groups traps together, allowing you to enable/disable the entire group with one command, to control and limit the scale of SMNP traps generated. |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| trap-name          | The name of the trap to be enabled/disabled.                                                                                                     |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| enabled | disabled | Select whether to enable or disable the specified trap. All traps are enabled by default.                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap interface disabled
	dnRouter(cfg-system-snmp)# trap interface linkUp enabled
	dnRouter(cfg-system-snmp)# trap interface linkDown enabled
	dnRouter(cfg-system-snmp)# trap system coldStart enabled



**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no trap bgp
	dnRouter(cfg-system-snmp)# no trap bgp bgpEstablishedNotification

.. **Help line:** Configure system snmp traps

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 5.1.0   | Command introduced                                   |
+---------+------------------------------------------------------+
| 6.0     | New BFD traps added                                  |
|         | Applied new hierarchy                                |
+---------+------------------------------------------------------+
| 11.4    | Updated BGP traps and added RSVP traps               |
+---------+------------------------------------------------------+
| 11.5    | Renamed bgpEstablished as bgpEstablishedNotification |
+---------+------------------------------------------------------+```

## system snmp trap-server admin-state
```rst
system snmp trap-server admin-state
-----------------------------------

**Minimum user role:** operator

Configure system snmp trap-server admin state.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Note:**

no command reverts the admin-state configuration to its default value

Validation: fail commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.


**Parameter table:**

+--------------+------------------------+---------------+
| Parameter    | Values                 | Default value |
+==============+========================+===============+
| admin-state  | enabled/disabled       | enabled       |
+--------------+------------------------+---------------+

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# admin-state enabled
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf my_vrf
	dnRouter(cfg-system-snmp-trap-server)# admin-state disabled
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# admin-state disabled
	


**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 16.2    | Command introduced                    |
+---------+---------------------------------------+


```

## system snmp trap-server community
```rst
system snmp trap-server community
---------------------------------

**Minimum user role:** operator

To configure the SNMP trap-server community used for communicating with the remote agent:

**Command syntax: community [community-value]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- community parameter is mandatory for snmp trap server configuration

	- Only one community can be configured per trap server

	- it is not possible to remove community configuration from trap server

	- This community field is not related to "snmp community [community-value]" command

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                              | Range  | Default |
+===========+==========================================================================================================+========+=========+
| community | Mandatory. The community string used to communicate with the remote agent.                               | string | \-      |
|           | Relevant only to SNMP version 1 or 2c and is mandatory. Only one community can be configured per server. |        |         |
+-----------+----------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	
	

**Removing Configuration**

You cannot remove the community configuration. To delete the community, run the command with a new community string: 
::

	dnRouter(cfg-system-snmp-trap-server)# community MyNewSnmpCommunity

.. **Help line:** Configure system snmp trap server community

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 5.1.0   | Command introduced               |
+---------+----------------------------------+
| 6.0     | Applied new hierarchy for SNMP   |
+---------+----------------------------------+
| 9.0     | Applied new hierarchy for server |
+---------+----------------------------------+


```

## system snmp trap-server max-throughput
```rst
system snmp trap-server max-throughput
--------------------------------------

**Minimum user role:** operator

To configure the SNMP max-throughput. This is the maximum number of traps that are send to the server in one second. If the generated traps are larger then this, then the rest of the traps will be discared.

**Command syntax: max-throughput [max-throughput]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| max-throughput | Maximum numbers of traps that can be sent to the server in one second. If there  | 1-1000 | 100     |
|                | is a larger number of traps generated then everything above the value of the     |        |         |
|                | throughput will be discarded                                                     |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-system-snmp-trap-server)# max-throughput 1000
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
    dnRouter(cfg-system-snmp-trap-server)# max-throughput 300


**Removing Configuration**

To revert the max throughput to default
::

    dnRouter(cfg-system-snmp-trap-server)# no max-throughput

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2.3  | Command introduced |
+---------+--------------------+
```

## system snmp trap-server port
```rst
system snmp trap-server port
----------------------------

**Minimum user role:** operator

To configure the SNMP port to which the remote device is connected:

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- no command reverts the port configuration to its default value

**Parameter table**

+-----------+-----------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                           | Range    | Default |
+===========+=======================================================================+==========+=========+
| port      | The port on the local device to which the remote device is connected. | 0..65535 | 162     |
+-----------+-----------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# port 123
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf default
	dnRouter(cfg-system-snmp-trap-server)# port 444
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# port 43
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-trap-server)# no port

.. **Help line:** Configure system snmp trap server port

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 5.1.0   | Command introduced               |
+---------+----------------------------------+
| 6.0     | Applied new hierarchy for SNMP   |
+---------+----------------------------------+
| 9.0     | Applied new hierarchy for server |
+---------+----------------------------------+


```

## system snmp trap-server
```rst
system snmp trap-server
-----------------------

**Minimum user role:** operator

Configures the system snmp trap-server. The system supports up to 5 different trap-servers.
To configure the system snmp trap-server:

**Command syntax: trap-server [server-ip] vrf [vrf-name]** parameter [parameter-value]

**Removing Configuration**

**Note:**

Creation of a new snmp trap server requires configuration of server-ip & community.

vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

Up to 5 snmp servers are allowed to be configured in total on all VRFs (mgmt0, default and non-default VRF).

snmp trap source address type will be set according to the destination server IP address type.


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+
| Parameter | Description                                                                                               | Range                     | Default |
+===========+===========================================================================================================+===========================+=========+
| server-ip | Mandatory. The IP address of the SNMP server                                                              | A.B.C.D                   | \-      |
|           |                                                                                                           | x:x::x:x                  |         |
+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+
| vrf-name  | Defines whether the trap-server listens to in-band or out-of-band interfaces for snmp-client get messages | default - in-band         | \-      |
|           |                                                                                                           | non-default-vrf - in-band |         |
|           |                                                                                                           | mgmt0 - out-of-band       |         |
+-----------+-----------------------------------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# community MySnmpCommunity 
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123

	dnRouter(cfg-system-snmp)# trap-server 2004:3221::1  vrf my_vrf
	dnRouter(cfg-system-snmp-trap-server)# community MyPrivateSnmpCommunity
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123

	dnRouter(cfg-system-snmp)# trap-server 2003:3221::1  vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# community MyNewSnmpCommunity
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	dnRouter(cfg-system-snmp-trap-server)# port 123
	
**Removing Configuration**

To remove the SNMP trap-server configuration:
::

	dnRouter(cfg-system-snmp)# no trap-server 1.2.3.4 vrf default

.. **Help line:** Configure system snmp trap server

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 5.1.0   | Command introduced                            |
+---------+-----------------------------------------------+
| 6.0     | Applied new hierarchy for SNMP                |
+---------+-----------------------------------------------+
| 9.0     | Applied new hierarchy for server              |
+---------+-----------------------------------------------+
| 10.0    | Changed syntax from "server" to "trap-server" |
+---------+-----------------------------------------------+
| 13.1    | Added trap-server out-of-band support         |
+---------+-----------------------------------------------+
| 15.1    | Added support for IPV6 address format         |
+---------+-----------------------------------------------+
```

## system snmp trap-server source-interface
```rst
system snmp trap-server source-interface
----------------------------------------

**Minimum user role:** operator

This command is applicable to the following interfaces:

physical interfaces logical interfaces (sub-interfaces) bundle interfaces bundle sub-interfaces loopback interfaces

By default, the source-interface for SNMP sessions is the system in-band-management source-interface. To override the default behavior and configure a different source-interface for SNMP sessions:

**Command syntax: source-interface [source-interface]**

**Description:** configure system snmp source interface for outgoing snmp sessions per server per VRF.

	- Validation that ip address must be configured on the interface configuration.

	- source-interface must be configured with the same address type as the remote snmp server otherwise the trap won't be sent.

**Parameter table**

+----------------+---------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter      | Description                                                                                                                     | Range                                               | Default |
+================+=================================================================================================================================+=====================================================+=========+
| interface-name | The name of the interface whose source IP address will be used for all SNMP sessions.                                           | A configured interface:                             | \-      |
|                | This interface must be configured with an IPv4 address.                                                                         |                                                     |         |
|                | The source-interface must be configured with the same address type as the remote snmp server, otherwise the trap won't be sent. | ge<interface speed>-<A>/<B>/<C>                     |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>  |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | bundle-<bundle id>                                  |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | bundle-<bundle id>.<sub-interface id>               |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | lo<lo-interface id>                                 |         |
+----------------+---------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-snmp-trap-server)# source-interface lo100
    dnRouter(cfg-snmp-trap-server)# source-interface bundle-1
    dnRouter(cfg-snmp-trap-server)# source-interface ge100-0/0/0

    dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf mgmt0
    dnRouter(cfg-snmp-trap-server)# source-interface mgmt0

    dnRouter(cfg-system-snmp-trap-server)#  no source-interface

**Command mode:** config

**TACACS role:** operator

**Removing Configuration**

Configuration is per server per VRF for all outgoing snmp applications (trap-server output etc).

-  By default used global configuration for source interface is used "system inband source-interface" for VRF default and "network-services vrf management-plane source-interface" for non-default in-band management VRF.
    - in case source-interface under trap-server is specified it will override the global source-interface config for that server.
    - Validation: source-interface is associated with the same VRF as the trap server, otherwise commit will fail validation

-  Only mgmt0 source-interface can be supported for mgmt0 VRF and it is the default value.

.. **Help line:** Configure system snmp source interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## system snmp trap-server trap-source-port
```rst
system snmp trap-server trap-source-port
----------------------------------------

**Minimum user role:** operator

To configure system SNMP source port for all outgoing SNMP traps:

**Command syntax: trap-source-port [port]**

**Description:** configure system snmp source port for per server per VRF for outgoing snmp traps

	- no command reverts the port configuration to its default value.

**Parameter table**

+-----------+-------------------------------------------------------------------------+-------------+--------------------------------------+
| Parameter | Description                                                             | Range       | Default                              |
+===========+=========================================================================+=============+======================================+
| port      | Set the port that will be used as a source for all outgoing SNMP traps. | 1024..65535 | Ephemerally allocated from the range |
+-----------+-------------------------------------------------------------------------+-------------+--------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-snmp-trap-server)# trap-source-port 1900

	dnRouter(cfg-system-snmp-server)# no trap-source-port

**Command mode:** config

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-system-snmp)# no trap-source-port

Configuration of SNMP traps source port per SNMP trap server per VRF for outgoing snmp traps.

.. **Help line:** Configure system snmp trap source port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+


```

## system snmp trap-server version
```rst
system snmp trap-server version
-------------------------------

**Minimum user role:** operator

To configure the trap-server SNMP version:

**Command syntax: version [version]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- No command reverts snmp version to its default value

**Parameter table**

+-----------+------------------+-------+---------+
| Parameter | Description      | Range | Default |
+===========+==================+=======+=========+
| version   | The SNMP version | 1     | 2c      |
|           |                  | 2c    |         |
+-----------+------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf default
	dnRouter(cfg-system-snmp-trap-server)# version 1
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-trap-server)# no version

.. **Help line:** Configure system snmp trap server version

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 5.1.0   | Command introduced               |
+---------+----------------------------------+
| 6.0     | Applied new hierarchy for SNMP   |
+---------+----------------------------------+
| 9.0     | Applied new hierarchy for server |
+---------+----------------------------------+


```

## system snmp user
```rst
system snmp user
-----------------

**Minimum user role:** operator

To configure a user for SNMP and enter the SNMP user configuration mode:

**Command syntax: user [user-name] parameter** [parameter-value]

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- Notice the change in prompt.

.. - Creation of a user must include auth-type and auth-password

	- password will be displayed as encrypted text. (enc-xxxx)

	- The same password is used for encryption and authentication

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------+-----------+
| Parameter | Description                                                                             | Range     |
+===========+=========================================================================================+===========+
| user-name | Enter a user name. If the user name does not already exist, a new user will be created. | String    |
+-----------+-----------------------------------------------------------------------------------------+-----------+

When creating an SNMP user, you must set the authentication (type of authentication and password are both required) for the user. See system snmp user authentication.

For each user, you can optionally set encryption and view options. The same password is used for authentication and for encryption. See system snmp user encryption and system snmp user view, respectively.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# user MySnmpUser2
	dnRouter(cfg-system-snmp-user)# authentication md5 password enc-#dsddsd546
	dnRouter(cfg-system-snmp-user)# encryption des
	dnRouter(cfg-system-snmp-user)# view MyView

	dnRouter(cfg-system-snmp)# user MySnmpUser3
	dnRouter(cfg-system-snmp-user)# authentication sha
	dnRouter(cfg-system-snmp-user)# password enc-234asds$#5



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-snmp)# no user MySnmpUser1

.. **Help line:** Configure system snmp user authentication

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 5.1.0   | Command introduced             |
+---------+--------------------------------+
| 6.0     | Applied new hierarchy for SNMP |
+---------+--------------------------------+
| 9.0     | Applied new hierarchy for user |
+---------+--------------------------------+
```

## system snmp user view
```rst
system snmp user view
---------------------

**Minimum user role:** operator

To configure SNMP user authentication:

**Command syntax: view [view-name]**

**Command mode:** config

**Hierarchies**

- system snmp

.. **Note**

	- validation: snmp view must be pre-configured in "system snmp view" for the user view configuration to apply (values for this command should be auto-complete)

	- by default, a user has view value of "viewdefault"(default snmp view in the system)

	- no command removes the specific view configuration

**Parameter table**

+-----------+-----------------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                                 | Range  | Default     |
+===========+=============================================================================+========+=============+
| view-name | The name of the view collection allowed for the user. See system snmp view. | String | viewdefault |
+-----------+-----------------------------------------------------------------------------+--------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# user MySnmpUser2 
	dnRouter(cfg-system-snmp-user)# view MyAllView
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-user)# no view

.. **Help line:** Configure system snmp user view

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 5.1.0   | Command introduced             |
+---------+--------------------------------+
| 6.0     | Applied new hierarchy for SNMP |
+---------+--------------------------------+
| 9.0     | Applied new hierarchy for user |
+---------+--------------------------------+

```

## system snmp view
```rst
system snmp view
----------------

**Minimum user role:** operator

A view is a collection of MIB object types that you want to group together to restrict or provide access to SNMP objects. The system has a single default view named "viewdefault". This view includes all MIBs in the system (i.e. no exclusions). You can configure 10 different views with 10 different OIDs.

To configure an SNMP View:

**Command syntax: mib {[oid \| mib-name]} {include \| exclude}**

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- Notice the change in prompt.

.. - view can contain multiple include/exclude mibs/oid

	- By default, the system holds a single view named "viewdefault". this view includes all mibs in the system

	- Per view, Matching include/exclude is done using longest-prefix-match while exclude > include

	- (excluded oids have prioirty vs included oids).

	- For example:

	- INCLUDE: 1.3.6.1.2.1.2.2.1.2 (ifDescr)

	- EXCLUDE: 1.3.6.1.2.1.2 (ifTable)

	- The results of doing a walk on ifTable will produce only ifDescr.

	- If the same OID is both included and excluded, then it is excluded.

	- no command removes the snmp view configuration, or the specific mib configuration

	- There should be 3 OIDs that should be excluded by default:

	- 1.3.6.1.6.3.15 (snmpUsmMIB)

	- 1.3.6.1.6.3.16 (snmpVacmMIB)

	- 1.3.6.1.6.3.18 (snmpCommunityMIB)

	- Rest of the OIDs are included.

**Parameter table**

+-----------+-----------------------------------------+
| Parameter | Description                             |
+===========+=========================================+
| view-name | Provide a name for the view collection. |
+-----------+-----------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# view MyViewName 
	dnRouter(cfg-system-snmp-view)# mib 1.3.6.1.2.1.1 include
	dnRouter(cfg-system-snmp-view)# mib 1.3.6.1.2.1.1.5 exclude
	dnRouter(cfg-system-snmp-view)# mib BGP4-MIB include
	

	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no view MyViewName
	dnRouter(cfg-system-snmp-view)# no mib 1.3.6.1.2.1.1 
	dnRouter(cfg-system-snmp-view)# no mib BGP4-MIB

.. **Help line:** Configure system snmp view

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy for SNMP      |
+---------+-------------------------------------+
| 9.0     | Applied new hierarchy for SNMP view |
+---------+-------------------------------------+


```

## system ssh
```rst
system ssh
-----------

**Minimum user role:** operator

Secure shell (SSH) is a generic connection protocol used to provide remote access to a device and provide secured file transfer protocol. DNOS enables to configure an SSH Server to enable access to the system via SSH (CLI) and also multiple SSH Clients, to enable to access remote devices from the system via SSH.

SSH Server/Client must be available via in-band management (default VRF) or out-of-band (mgmt0 interface) only.

To manage SSH sessions:

**Command syntax: ssh [parameters]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt from dnRouter(cfg-system)# to dnRouter(cfg-system-ssh)# (system SSH configuration mode).

.. - no command returns the state to default.

**Parameter table**

+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| Parameter               | Description                                                                                                   | Reference                              |
+=========================+===============================================================================================================+========================================+
| client admin-state      | Enable or disable the client SSH functionality                                                                | system ssh client admin-state          |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server client-list      | Configure a list of incoming IP addresses that will or will not be permitted access to an in-band SSH server. | system ssh server vrf client-list      |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server client-list type | Sets the server client-list as a white-list or black-list.                                                    | system ssh server vrf client-list type |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server max-sessions     | Configure the maximum number of concurrent SSH sessions                                                       | system ssh server max-sessions         |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server admin-state      | Enable/disable the SSH server                                                                                 | system ssh server admin-state          |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ssh
	dnRouter(cfg-system-ssh)# client admin-state enabled
	dnRouter(cfg-system-ssh)# server
	dnRouter(cfg-system-ssh-server)#



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ssh)# no client admin-state

.. **Help line:** configure ssh server and client functionality.

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 6.0     | Command introduced for new hierarchy |
+---------+--------------------------------------+
```

## system ssh security
```rst
system ssh security
-------------------

**Minimum user role:** operator

Configure SSH security parameters:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system ssh

**Note**

- Security affects both SSH Server and Netconf servers on all vrfs

- Security does not affect SSH Client

- Notice the change in prompt.

- no commands removes configuration/set the default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# security
    dnRouter(cfg-system-ssh-security)# mac hmac-sha2-512
    dnRouter(cfg-system-ssh-security)# !
    dnRouter(cfg-system-ssh)# security ciphers chacha20-poly1305-openssh.com,aes256-gcm-openssh.com


**Removing Configuration**

To revert to default algorithms
::

    dnRouter(cfg-system-ssh)# no security

**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 19.1.3  | Command introduced as part of new hierarchy |
+---------+---------------------------------------------+
| TBD     | Fix prompt from cli_examples                |
+---------+---------------------------------------------+
```

## system ssh server max-attempts
```rst
system ssh server max-attempts
------------------------------

**Minimum user role:** operator

Configure the maximal number of SSH connection attempts within the defined time window.

**Command syntax: max-attempts [max-attempts]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Parameter table**

+--------------+----------------------------------------------------------+-------+---------+
| Parameter    | Description                                              | Range | Default |
+==============+==========================================================+=======+=========+
| max-attempts | maximum number of connection attempts within time-window | 1-50  | 10      |
+--------------+----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# max-attempts 20


**Removing Configuration**

To revert ssh server max-attempts to default: 
::

    dnRouter(cfg-system-ssh-server)# no max-attempts

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1.3  | Command introduced |
+---------+--------------------+
```

## system ssh server time-window
```rst
system ssh server time-window
-----------------------------

**Minimum user role:** operator

To configure the time window for SSH connections rate limiting:

**Command syntax: time-window [time-window]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Parameter table**

+-------------+-----------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                     | Range  | Default |
+=============+=================================================================+========+=========+
| time-window | length of time window for SSH sessions connection rate limiting | 1-3600 | 60      |
+-------------+-----------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# time-window 100


**Removing Configuration**

To revert ssh server time-window to default: 
::

    dnRouter(cfg-system-ssh-server)# no time-window

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1.3  | Command introduced |
+---------+--------------------+
```

## system telnet server vrf client-list type
```rst
system telnet server vrf client-list type
-----------------------------------------

**Minimum user role:** operator

This command defines whether the configured client-list (see system telnet server vrf client-list) is a white list or a black list. This will determine if the listed clients will be granted access to the system in-band telnet server.

**Command syntax: server vrf client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system telnet server 

**Note**

- If client-list type is set to "allow", the client-list must not be empty.

.. - no command return the list type to its default value

	- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+-----------+-------------------------------------------+-------+---------+
| Parameter | Description                               | Range | Default |
+===========+===========================================+=======+=========+
| list-type | The type of list of incoming IP addresses | allow | deny    |
|           |                                           | deny  |         |
+-----------+-------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet 
	dnRouter(cfg-system-telnet)# server vrf default
	dnRouter(cfg-telnet-server-vrf)# client-list type allow
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-telnet-server-vrf)# no client-list type

.. **Help line:** configure black or white list of incoming IP-addresses for system in-band telnet server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


```

## system timezone
```rst
system timezone
---------------

**Minimum user role:** operator
System timezone provides a full sync for dates and times between all the containers in all the clusters or Standalone components.

To set the system time-zone, use the following command:

**Command syntax: timezone [timezone]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Changing the time-zone will affect the displayed system uptime, logs, traces, debug files, and CLI transactions.

.. - No system timezone return timezone parameter to default value (UTC)

**Parameter table**

+-----------+-----------------------------------+---------------------------------------------------------------+---------+
| Parameter | Description                       | Range                                                         | Default |
+===========+===================================+===============================================================+=========+
| timezone  | Sets the time-zone for the system | Linux time-zone list, use the 'tab' help key to view the list | UTC     |
+-----------+-----------------------------------+---------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# timezone UTC



**Removing Configuration**

To revert the timezone to default:
::

	dnRouter(cfg-system)# no timezone

.. **Help line:** Configure system timezone

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 5.1.0   | Command introduced                                      |
+---------+---------------------------------------------------------+
| 6.0     | Applied new hierarchy                                   |
+---------+---------------------------------------------------------+
| 13.1    | Added timezone configuration for formats other than UTC |
+---------+---------------------------------------------------------+
```

## system timing-mode
```rst
system timing-mode 
-------------------

**Minimum user role:** operator

Set the timing mode to "NTP" to enable NTP functionality.

**Command syntax: timing-mode [mode]**

**Command mode:** config

**Hierarchies**

- system 

**Note**

- The system's timing mode must match that of DNOR. If you manually set the system's date-time value to 10 years higher or lower than date-time value on DNOR, DNOR cluster management may be lost. It will not be possible to add/remove NCC nodes from the cluster.

.. - no command returns timing-mode to default.

	- When system timing mode "NTP" is set, the system time source from remote server via NTP protocol is used. If no remote NTP server was configured as time source for the system, the system will operate in a free-running state using the time that was set during DNOS cluster creation.

	- When system timing mode "manual" is set, user may set the time & date to any value using "set system datetime" CLI command. If manually set date-time value is 10 years higher or 10 years lower than date-time value on DNOR, cluster management by DNOR may be lost. In this case, NCC add/remove from cluster functionality will not be available.

	- When system timing-mode "manual" is set, NTP functionalities are disabled.

**Parameter table**

+-----------+------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter | Description                  | Range                                                                                                                                                                                                                                  | Default |
+===========+==============================+========================================================================================================================================================================================================================================+=========+
| mode      | The timing mode of operation | NTP - enables the NTP functionality (see system ntp server). If no remote NTP server is configured as time source for the system, the system will operate in a free-running state using the time that was set during cluster creation. | NTP     |
|           |                              | manual - disables the NTP functionality and uses the manually set time (see set system datetime).                                                                                                                                      |         |
+-----------+------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# timing-mode ntp
	dnRouter(cfg-system)# timing-mode manual
	WARNING: System and Conductor must be in the same time domain. By setting system date and time manually, you may lose the ability to add and remove nodes to cluster!
	
	
	

**Removing Configuration**

To revert the timing-mode to default: 
::

	dnRouter(cfg-system)# no timing-mode

.. **Help line:** Configure system timing mode.

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+


```

## thermal-shutdown-auto-restart
```rst
system thermal-shutdown-auto-restart
------------------------------------

**Minimum user role:** operator

To change the mode of automatic power up after thermal shutdown:

**Command syntax: thermal-shutdown-auto-restart [thermal-shutdown-auto-restart]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- When the platform is shut down due to thermal considerations, it may automatically power up after the system cools down or stay powered off depending on the auto-restart mode.

- When disabled, upon system thermal shutdown, manual intervention using ipmi access or unplugging and plugging the power cord will be required to power up the system.

- The configuration applies to supporting NCP, NCF, and NCM nodes.

**Parameter table**

+-------------------------------+------------------------------------------------------------------+--------------+---------+
| Parameter                     | Description                                                      | Range        | Default |
+===============================+==================================================================+==============+=========+
| thermal-shutdown-auto-restart | The state of platform automatic power up after thermal shutdown. | | enabled    | enabled |
|                               |                                                                  | | disabled   |         |
+-------------------------------+------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# thermal-shutdown-auto-restart disabled


**Removing Configuration**

To revert auto power up mode to default:
::

    dnRouter(cfg-system)# no thermal-shutdown-auto-restart

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

