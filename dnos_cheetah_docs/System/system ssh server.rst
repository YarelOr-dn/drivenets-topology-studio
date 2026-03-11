system ssh server
-----------------

**Minimum user role:** operator

Configure SSH server parameters:

**Command syntax: server**

**Command mode:** config

**Hierarchies**

- system ssh

**Note**

- SSH is supported on the default, mgmt and non-default vrf.

- Notice the change in prompt.

- no commands removes configuration/set the default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server vrf default
    dnRouter(cfg-ssh-server-vrf)# client-list 2001:ab12::1/128
    dnRouter(cfg-ssh-server-vrf)# client-list type
    dnRouter(cfg-ssh-server-vrf)#  !
    dnRouter(cfg-system-ssh-server)# max-sessions 5
    dnRouter(cfg-system-ssh-server)# admin-state disable


**Removing Configuration**

To revert the ssh server admin-state
::

    cfg-system-ssh-server)# no admin-state

To revert ssh server class of service
::

    dnRouter(cfg-system-ssh-server)# no class-of-service

To revert ssh server max-sessions:
::

    dnRouter(cfg-system-ssh-server)# no max-sessions

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 10.0    | Command introduced as part of new hierarchy   |
+---------+-----------------------------------------------+
| 11.0    | Parameters moved to the lower level hierarchy |
+---------+-----------------------------------------------+
