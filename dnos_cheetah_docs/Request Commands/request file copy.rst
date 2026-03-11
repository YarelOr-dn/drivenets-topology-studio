request file copy
--------------------

**Minimum user role:** admin

Copy the file from the local directory to the destination.

**Command syntax: request file copy** { ncc [ncc-id] } **[file-type] [source_file_absolute_path] [destination_folder]** | force

**Command mode:** operational

**Note:**

- Validation : User Yes/No question with the specified file name.

- Only `integrity-report-retrieves` is supported currently starting with v18.2.1.

- The destination directory for `integrity-report-retrieves` has a limit of maximum 10 files.

- File types locations:

 -  integrity-report-retrieves - /core/integrity_report_retrieves

- File types to copy from the NCCs:

 -  integrity-report-retrieves

**Parameter table:**

+---------------------------+-----------------------------------------------+---------------+
| Parameter                 | Values                                        | Default value |
+===========================+===============================================+===============+
| file-type                 | integrity-report-retrieves                    | \-            |
+---------------------------+-----------------------------------------------+---------------+
| ncc-id                    | 0-1                                           | \-            |
+---------------------------+-----------------------------------------------+---------------+
| container                 | cluster-engine / dnos-agent / host            | \-            |
|                           | / management-engine / ncc-conducto            |               |
|                           | / node-manager / policy-executor / redis      |               |
|                           | / redis_config / routing-engine               |               |
+---------------------------+-----------------------------------------------+---------------+
| source-file-absolute-path |                                               | \-            |
+---------------------------+-----------------------------------------------+---------------+
| destination-folder        | integrity_report_retrieves                    | \-            |
+---------------------------+-----------------------------------------------+---------------+
| force                     | \-                                            | disabled      |
+---------------------------+-----------------------------------------------+---------------+

**Example**
::

	dnRouter# request file copy integrity-report-retrieves /define_notif_net.sh
	File /define_notif_net.sh was copied successfully


	dnRouter# request file copy integrity-report-retrieves /define_notif_net.sh
	File /define_notif_net.sh already exists
	Do you want to overwrite it? (Yes/No) [No]?


**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2.1    | Command introduced                |
+---------+-------------------------------------+
