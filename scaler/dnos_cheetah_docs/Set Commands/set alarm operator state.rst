
set alarm operator state
---------------------------

**Minimum user role:** viewer

Used by the operator to update the alarm operator state, used to acknowledge/close the alarm.

**Command syntax: set alarm operator state**

**Command mode:** operational

**Parameter table:**

+----------------------+---------------------------------------------+---------------+
| Parameter            | Values                                      | Default value |
+======================+=============================================+===============+
| state                | ack, closed                                 |  -/           |
+----------------------+---------------------------------------------+---------------+
| alarm-unique-id      | random generated number                     |  -/           |
+----------------------+---------------------------------------------+---------------+
| description          | string                                      |  -/           |
+----------------------+---------------------------------------------+---------------+

**Note**
-  The alarm-unique-id is a unique id per alarm, presented under show system alarms.
-  State - set by the operator as part of the alarm handling process.
-  Description is a text in quotation marks, length 1..255.


**Example**
::

	dnRouter# set alarm operator state ack alarm 1278605535506855

	dnRouter# set alarm operator state closed alarm 1278605535506855 description "handled the adjacency on the peer"

.. **Help line:** Configure DNOR servers.


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 18.0        | Command introduced    |
+-------------+-----------------------+
