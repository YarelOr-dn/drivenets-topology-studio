system ncp clock synce smb-10mhz wtr
------------------------------------

**Minimum user role:** operator

Set SMB 10mhz reference source wait-to-restore time.

**Command syntax: wtr [wtr]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce smb-10mhz

**Parameter table**

+-----------+-------------------------------------------+-------+---------+
| Parameter | Description                               | Range | Default |
+===========+===========================================+=======+=========+
| wtr       | Sets the wait to restore time in minutes. | 0-12  | 5       |
+-----------+-------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# smb-10mhz
    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# wtr 5


**Removing Configuration**

To revert the SMB 10mhz source wtr time to default values:
::

    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# no wtr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
