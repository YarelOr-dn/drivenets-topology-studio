show file integrity-report list
--------------------------------

**Minimum user role:** admin

Display a detailed list of the integrity-report directory.


**Command syntax: show file integrity-report**

**Command mode:** operational

**Note**

**Example**
::

    dnRouter# show file integrity-report list


    | Type   | Id  | File name                                            | Size [Bytes]  | Last modified             |
    +--------+-----+------------------------------------------------------+---------------+---------------------------+
    | NCC    | 1   | integrity_report_dnRouter_20231018_155010.json.gz    | 12M           | 18-Oct-2023 15:50:10 UTC  |
    | NCC    | 1   | integrity_report_dnRouter_20250404_001308.json.gz    | 12M           | 04-Apr-2025 00:13:08 UTC  |


.. **Help line:** Displays files detailed list

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 19.1        | Command introduced    |
+-------------+-----------------------+
