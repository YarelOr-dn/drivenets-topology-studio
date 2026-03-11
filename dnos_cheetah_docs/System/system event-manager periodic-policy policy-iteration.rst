system event-manager periodic-policy policy-iteration
-----------------------------------------------------

**Minimum user role:** admin

To configure the number of times a policy is executed.

**Command syntax: policy-iteration [iteration]**

**Command mode:** config

**Hierarchies**

- system event-manager periodic-policy


**Note**

.. -  Once the policy is executed the policy-iteration number of times the policy will appear in operational-state "inactive".

-  Any updates to the policy-iteration configuration during a policy execution are implemeted at the next policy execution.

.. - "0" is used as infinite value.

**Parameter table**

+-------------------------+-----------------------------------------------------+-----------------------------+---------------+
| Parameter               | Description                                         | Range                       | Default       |
+=========================+=====================================================+=============================+===============+
|  iteration              | The maximum number of times a policy is executed.   | 0 | 1 - 1000                | 0             |
|                         | Zero is used as an infinite value.                  |                             |               |
+-------------------------+-----------------------------------------------------+-----------------------------+---------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# periodic-policy test
    dnRouter(cfg-periodic-policy-test)#  policy-iteration 0
    dnRouter(cfg-periodic-policy-test)#
    dnRouter(cfg-periodic-policy-test)#  policy-iteration 20
    dnRouter(cfg-periodic-policy-test)#

**Removing Configuration**

To revert the router-id to default: 
::

        dnRouter(cfg-periodic-policy-test)# no policy-iteration

.. **Help line:** configure the number of policy-iterations parameter.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


