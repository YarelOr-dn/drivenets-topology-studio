system ncp clock synce smb-10mhz mode
-------------------------------------

**Minimum user role:** operator

Set the SMB 10MHz port as input or output or disabled.

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce smb-10mhz

**Parameter table**

+-----------+------------------------------------------------------------+--------------+----------+
| Parameter | Description                                                | Range        | Default  |
+===========+============================================================+==============+==========+
| mode      | Set the 10MHz SMB port mode as input or output or disabled | | disabled   | disabled |
|           |                                                            | | output     |          |
|           |                                                            | | input      |          |
+-----------+------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# smb-10mhz
    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# mode input


**Removing Configuration**

To revert the SMB 10mhz mode to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no smb-10mhz

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
