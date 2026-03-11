request system tech-support
---------------------------

**Command syntax: request system tech-support [file-name]** {brief \| extended}

**Description:** generate system tech-support file while in recovery mode

-  In recovery mode, tech-support is extended by default, and will include core dumps

**CLI example:**
::

	dnRouter(RECOVERY)#  # request system tech-support MyTechSupportFile

	System is generating Tech-support file
	Collecting log files from NCC-1
	Collecting system config and status commands

	Tech-support successfully generated on /techsupport/MyTechSupportFile_13:32:00_30-01-2017.tar.gz

	dnRouter(RECOVERY)#  # request system tech-support MyBreifTechSupportFile

	System is generating Tech-support file
	Collecting log files from NCC-1
	Collecting system config and status commands

	Tech-support successfully generated on /techsupport/MyBreifTechSupportFile_13:35:00_30-01-2017.tar.gz



**Command mode:** recovery

**Note:**

-  In recovery mode, generated tech-support file will not include operational CLI command outputs

**Help line:**

**Parameter table:**

+-----------+--------+---------------+
| Parameter | Values | Default value |
+===========+========+===============+
| file-name | string |               |
+-----------+--------+---------------+
| brief     |        |               |
+-----------+--------+---------------+

.. _show-rollback-1:
