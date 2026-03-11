system ncp clock synce smb-10mhz holdoff
----------------------------------------

**Minimum user role:** operator

Set SMB 10mhz reference source hold-off-time parameter.

**Command syntax: holdoff [hold-off-time]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce smb-10mhz

**Parameter table**

+---------------+--------------------+----------+---------+
| Parameter     | Description        | Range    | Default |
+===============+====================+==========+=========+
| hold-off-time | SyncE holdoff time | 300-1800 | 300     |
+---------------+--------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# smb-10mhz
    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# holdoff 400


**Removing Configuration**

To revert the SMB 10mhz reference source to default hold-off time:
::

    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# no holdoff

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
