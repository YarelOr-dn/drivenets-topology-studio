system ncp clock gnss
---------------------

**Minimum user role:** operator

Enter GNSS related configuration options and reference synchronization clock settings.

To configure the sync parameters:

**Command syntax: gnss**

**Command mode:** config

**Hierarchies**

- system ncp clock

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk/gnss)#


**Removing Configuration**

To revert GNSS config to default values:
::

    dnRouter(cfg-system-ncp-7-clk)# no gnss

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
