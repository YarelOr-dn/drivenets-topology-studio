system ncp clock
----------------

**Minimum user role:** operator

Enter timing related configuration options and reference synchronization clock settings.

To configure timing parameters:

**Command syntax: clock**

**Command mode:** config

**Hierarchies**

- system ncp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)#


**Removing Configuration**

To revert the clock to its default value:
::

    dnRouter(cfg-system-ncp-7)# no clock

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
