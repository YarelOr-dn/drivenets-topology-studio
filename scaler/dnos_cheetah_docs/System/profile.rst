system profile
--------------

**Minimum user role:** operator

The system profile dictates the set of features that can be supported simultaneously in the system.

To configure the global profile, that shall be applied for all NCPs in the cluster:

**Command syntax: profile [system-profile]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- DNOS configuration cannot conflict with the configured system profile. A validation will enforce that the configuration is valid.

- Profile reconfiguration is traffic affecting, will require the user to confirm the change and shall cause the WB Agent process on each NCP to restart.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                      | Range   | Default |
+================+==================================================================================+=========+=========+
| system-profile | The name of the profile applied to the system. The profile is applied to all     | default | default |
|                | NCPs in the cluster.                                                             |         |         |
+----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# profile profile_a
    Notice: Continuing with the commit will cause the following:
    The following commit will change the system profile. WB Agent process on all NCPs shall restart, traffic loss will occur and some features may not be available after this change takes effect.
    Enter yes to continue with commit, no to abort commit (yes/no) [no]


**Removing Configuration**

To revert the global system profile to its default value:
::

    dnRouter(cfg-system)# no profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
