show system platform security
-----------------------------

**Minimum user role:** viewer

To display platform security configuration and state parameters:

**Command syntax: show system platform security** [node-name] [node-id]

**Command mode:** operational

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter | Description                                                                                                                                | Range              |
+===========+============================================================================================================================================+====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..191        |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Example**
::

    dnRouter# show system platform security ncp 0

    Platform Measured boot parameters:
        Admin-state:                      enabled
        Reference TPM PCR valid:          true
        Last PCR quote compare status:    failed
        TPM PCR mismatched slots:         2, 7

    Platform Signature validation parameters:
        Admin-state:                      enabled
        Last SW update validation status: failed
        UEFI SPI Flash device:            1

**Example**
::

    dnRouter# show system platform security

    Platform Measured boot parameters:
        Admin-state:                      disabled
        Reference TPM PCR valid:          false
        Last PCR quote compare status:
        TPM PCR mismatched slots:

    Platform Signature validation parameters:
        Admin-state:                      enabled
        Last SW update validation status: passed
        UEFI SPI Flash device:            0

.. **Help line:** show system platform security [ncp] [0..191]

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.2    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
