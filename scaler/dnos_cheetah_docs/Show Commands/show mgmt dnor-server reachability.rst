show mgmt dnor-server reachability
----------------------------------

**Minimum user role:** viewer

To display the reachability of configured DNOR servers in the system:



**Command syntax: show mgmt dnor-server reachability**

**Command mode:** operational

**Example**
::

	dnRouter# show mgmt dnor-server reachability

	| Host        | VRF     | Status        | Last Reachable Time   |
	|-------------+---------+---------------+-----------------------|
	| 127.0.0.1   | mgmt0   | reachable     | 2023-06-26 10:29:47   |
	| 192.168.1.1 | mgmt0   | not reachable | N/A                   |
	| 127.0.0.1   | default | not reachable | N/A                   |
	| 192.168.1.1 | default | not reachable | N/A                   |

.. **Help line:** show mgmt dnor-server reachability

**Command History**

+-----------+-------------------------------+
|  Release  | Modification                  |
+===========+===============================+
|  18.2.1   | Command introduced            |
+-----------+-------------------------------+
