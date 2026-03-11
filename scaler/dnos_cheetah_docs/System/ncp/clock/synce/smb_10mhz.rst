system ncp clock synce smb-10mhz
--------------------------------

**Minimum user role:** operator

Configure SMB 10MHz port parameters

**Command syntax: smb-10mhz**

**Command mode:** config

**Hierarchies**

- system ncp clock synce

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# smb-10mhz
    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)#


**Removing Configuration**

To revert the clock sync-ethernet 10mhz SMB port to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no smb-10mhz

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
