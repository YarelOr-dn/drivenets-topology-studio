system ncp clock synce smb-10mhz quality-level
----------------------------------------------

**Minimum user role:** operator

Set SMB 10mhz reference source quality-level.

**Command syntax: quality-level [quality-level]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce smb-10mhz

**Parameter table**

+---------------+--------------------------------+----------------------------+---------+
| Parameter     | Description                    | Range                      | Default |
+===============+================================+============================+=========+
| quality-level | Reference source quality level | | no_ql                    | no_ql   |
|               |                                | | -- Option-1 Levels: --   |         |
|               |                                | | ql_prc                   |         |
|               |                                | | ql_ssu_a                 |         |
|               |                                | | ql_ssu_b                 |         |
|               |                                | | ql_sec                   |         |
|               |                                | | ql_dnu                   |         |
|               |                                | | -- Option-2 Levels: --   |         |
|               |                                | | ql_prs                   |         |
|               |                                | | ql_stu                   |         |
|               |                                | | ql_st2                   |         |
|               |                                | | ql_tnc                   |         |
|               |                                | | ql_st3e                  |         |
|               |                                | | ql_st3                   |         |
|               |                                | | ql_smc                   |         |
|               |                                | | ql_prov                  |         |
|               |                                | | ql_dus                   |         |
+---------------+--------------------------------+----------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# smb-10mhz
    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# quality-level ql_prc


**Removing Configuration**

To revert the SMB 10mhz source quality-level to default
::

    dnRouter(cfg-system-ncp-7-clk-synce-smb-10mhz)# no quality-level

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
