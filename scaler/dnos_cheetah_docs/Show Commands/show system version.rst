show system version
-------------------

**Minimum user role:** viewer

To display the DNOS deployed version, use one of the following commands:

**Command syntax: show system version**

**Command mode:** operational



**Note**

- The version is displayed in the following format: W.X.Y, followed by build number Z, where:

	- W - major version

	- X - minor version

	- Y - BugFix version

	- Z - Build number

.. - show system version describes DNOS deployed cluster version.



**Example**
::

	dnRouter# show system version
	
	System Name: dnRouter 
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

.. **Help line:** show system version information

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 5.1.0   | Command introduced                                         |
+---------+------------------------------------------------------------+
| 10.0    | Updated to new NCR architecture; removed "extended" option |
+---------+------------------------------------------------------------+
| 17.2    | Split the build number from the DNOS version               |
+---------+------------------------------------------------------------+
