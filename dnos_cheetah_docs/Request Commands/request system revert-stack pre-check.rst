request system revert-stack pre-check
-------------------------------------

**Minimum user role:** admin

Pre-checks revert stack packages compatibility before upgrade/deployment.

**Command syntax: request system revert-stack pre-check**

**Command mode:** operational

.. **Note**

**Example**
::

    dnRouter# request system revert-stack pre-check

    Status: OK


    dnRouter# request system revert-stack pre-check

    Status: Error
    Reason: NCM A0 FW wrong revision


.. **Help line:** Validates revert stack packages compatibility.

**Parameter table:**

+----------------------+------------------------------------------+----------------------------------------------+---------------+
| Parameter            | Description                              |  Values                                      | Default value |
+======================+==========================================+==============================================+===============+
| Status               | The status of the revert-stact pre-check |  OK, Error                                   | \-            |
+----------------------+------------------------------------------+----------------------------------------------+---------------+
| Reason               | The reason of the error                  |  String - in case of status Error            | \-            |
+----------------------+------------------------------------------+----------------------------------------------+---------------+

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
