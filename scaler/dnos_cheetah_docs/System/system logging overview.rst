System Logging Overview
-----------------------
Logging is a process that receives logs from the various system components allowing you to track events on the device. DNOS uses the Event Manager to record operations and distribute them to other services. By default, logs are stored in files locally. You can also configure up to five remote syslog servers to collect all or some logs in a unified location. For information on configuring a syslog server, see system logging syslog server.

Log files are stored in two locations:

- On the NCC - in the /var/log/syslog folder
- On a remote syslog server (if syslog is enabled) - for information on configuring a syslog server, see system logging syslog server.

You can set the maximum size of the logged files and the number of files that will be saved and the event group. When the file size is reached, the system opens a new file for storing the logs. When the set number of files is reached, the system deletes the oldest file before it starts saving to a new file. System events are grouped to allow configuration on the group. You can set the minimum severity to save to the log file for the entire group. By default, all logs are saved to file. You can change the severity of an event-group to only save logs with a minimum severity level. All logs with that severity level or higher, will be saved. All other logs will be discarded.

The messages use the format:

Facility.Severity Version Timestamp Hostname Appname ProcID MSGID Structure-data message

+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Message Category | Description                                                                                                                                                         |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Facility         | A number that identifies the facility that a system event is associated with.                                                                                       |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Severity         | A severity level assigned to the system event to indicate the importance of the message.                                                                            |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Version          | 1, the version of the syslog protocol.                                                                                                                              |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Timestamp        | Date, Time (including ms).                                                                                                                                          |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Hostname         | NCE hostname.                                                                                                                                                       |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Appname          | A syslog tag that identifies the device or application that originated the message.                                                                                 |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ProcID           | A syslog tag Identifier.                                                                                                                                            |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MSGID            | A syslog tag that identifies the type of message.                                                                                                                   |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Structure-Data   | A syslog tag which can display information about the syslog message or application-specific information.                                                            |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Message          | Event-Name:Message: Text string that uniquely identifies the message, in all uppercase letters and using the underscore (_) to separate words and the message text. |
+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The following table describes the severity levels:

+---------------+----------------------------------+
| Level         | Description                      |
+---------------+----------------------------------+
| 0 - Emergency | System is unusable               |
+---------------+----------------------------------+
| 1 - Alert     | Immediate action is needed       |
+---------------+----------------------------------+
| 2 - Critical  | Critical condition               |
+---------------+----------------------------------+
| 3 - Error     | Error condition                  |
+---------------+----------------------------------+
| 4 - Warning   | Warning condition                |
+---------------+----------------------------------+
| 5 - Notice    | Normal but significant condition |
+---------------+----------------------------------+
| 6 - Info      | Informational message only       |
+---------------+----------------------------------+
| 7 - Debug     | Debug message only               |
+---------------+----------------------------------+

The following table describes the facility codes:

+---------------+----------+------------------------------------------+
| Facility Code | Keyword  | Description                              |
+---------------+----------+------------------------------------------+
| 0             | kern     | kernel messages                          |
+---------------+----------+------------------------------------------+
| 1             | user     | user-level messages                      |
+---------------+----------+------------------------------------------+
| 2             | mail     | mail system                              |
+---------------+----------+------------------------------------------+
| 3             | daemon   | system daemons                           |
+---------------+----------+------------------------------------------+
| 4             | auth     | security/authorization messages          |
+---------------+----------+------------------------------------------+
| 5             | syslog   | messages generated internally by syslogd |
+---------------+----------+------------------------------------------+
| 6             | lpr      | line printer subsystem                   |
+---------------+----------+------------------------------------------+
| 7             | news     | network news subsystem                   |
+---------------+----------+------------------------------------------+
| 8             | uucp     | UUCP subsystem                           |
+---------------+----------+------------------------------------------+
| 9             |          | clock daemon                             |
+---------------+----------+------------------------------------------+
| 10            | authpriv | security/authorization messages          |
+---------------+----------+------------------------------------------+
| 11            | ftp      | FTP daemon                               |
+---------------+----------+------------------------------------------+
| 12            | -        | NTP subsystem                            |
+---------------+----------+------------------------------------------+
| 13            | -        | log audit                                |
+---------------+----------+------------------------------------------+
| 14            | -        | log alert                                |
+---------------+----------+------------------------------------------+
| 15            | cron     | scheduling daemon                        |
+---------------+----------+------------------------------------------+
| 16            | local0   | local use 0 (local0)                     |
+---------------+----------+------------------------------------------+
| 17            | local1   | local use 1 (local1)                     |
+---------------+----------+------------------------------------------+
| 18            | local2   | local use 2 (local2)                     |
+---------------+----------+------------------------------------------+
| 19            | local3   | local use 3 (local3)                     |
+---------------+----------+------------------------------------------+
| 20            | local4   | local use 4 (local4)                     |
+---------------+----------+------------------------------------------+
| 21            | local5   | local use 5 (local5)                     |
+---------------+----------+------------------------------------------+
| 22            | local6   | local use 6 (local6)                     |
+---------------+----------+------------------------------------------+
| 23            | local7   | local use 7 (local7)                     |
+---------------+----------+------------------------------------------+

You can configure the facility to which the system log messages belongs and its severity level. The default facility for syslog messages is local7.

An example syslog message for a system event "ssh-session-terminated" with facility=6, severity=5, trigger process=sshd generated by an NCE with system name "dls470sw" will looks as follows:

<65>1 2003-10-11T22:14:15.003Z DLS470SW - bgpd - - ssh-session-terminated:SSH session 456 (remote host 10.1.1.1) terminated by user dnRoot