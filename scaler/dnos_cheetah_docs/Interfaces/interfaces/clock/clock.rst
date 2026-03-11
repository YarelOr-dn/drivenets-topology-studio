interfaces clock
----------------

**Minimum user role:** operator

Enter timing related configuration options and reference synchronization clock settings.

To configure timing parameters:

**Command syntax: clock**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- Notice the change in prompt.

- This command is currently applicable only to physical 400G and breakout interfaces on UfiSpace NCP3 platforms or physical 10G and 100G interfaces on UfiSpace NCPL platforms.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock


**Removing Configuration**

To revert interface clock to its default value:
::

    dnRouter(cfg-if-ge400-0/0/0)# no clock

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
