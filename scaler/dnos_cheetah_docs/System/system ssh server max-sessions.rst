system ssh server max-sessions
------------------------------

**Minimum user role:** operator

Configure the maximum number of concurrent SSH sessions

**Command syntax: max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Note**

- To enable these concurrent sessions, ssh-client must be enabled. See system ssh client admin-state

- no command returns the number of maximum sessions to default

**Parameter table**

+--------------+---------------------------------------------------------+-------+---------+
| Parameter    | Description                                             | Range | Default |
+==============+=========================================================+=======+=========+
| max-sessions | maximum number of concurrent CLI sessions to SSH server | 1-32  | 10      |
+--------------+---------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# max-sessions 5


**Removing Configuration**

To revert ssh server max-sessions to default: 
::

    dnRouter(cfg-system-ssh-server)# no max-sessions

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 5.1.0   | Command introduced            |
+---------+-------------------------------+
| 6.0     | Applied new hierarchy         |
+---------+-------------------------------+
| 10.0    | Merged with system ssh server |
+---------+-------------------------------+
| 11.0    | Moved into system ssh server  |
+---------+-------------------------------+
