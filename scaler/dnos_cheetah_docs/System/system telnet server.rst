system telnet server
--------------------

**Minimum user role:** operator

To configure the telnet server parameters.

**Command syntax: server [parameters]**

**Command mode:** config

**Hierarchies**

- system telnet

**Note**

- Notice the change in prompt.

.. - no commands removes configuration/set the default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telnet
    dnRouter(cfg-system-telnet)# server vrf default
    dnRouter(cfg-telnet-server-vrf)# client-list 2001:ab12::1/128
    dnRouter(cfg-telnet-server-vrf)# client-list type deny
    dnRouter(cfg-system-telnet-server-vrf)# !
    dnRouter(cfg-system-telnet-server)# max-sessions 5
    dnRouter(cfg-system-telnet-server)# admin-state disable



**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-telnet-server-vrf)# no client-list
    dnRouter(cfg-system-telnet-server)# no max-sessions
    dnRouter(cfg-system-telnet-server)# no admin-state

.. **Help line:** configure telnet server parameters.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


