Feature: SMTPD Handler

    Scenario Outline: Valid Path Prefix
        Given the prefix pattern is <prefix_pattern>
        When the timestamp is <timestamp>
        Then the path prefix is <path_prefix>

        Examples:
        | prefix_pattern                                                              | timestamp        | path_prefix                                                       |
        | s3://mybucket/emails/year={YYYY}/month={MM}/day={dd}/hour={HH}/minute={mm}/ | 2025-08-09T01:01 | s3://mybucket/emails/year=2025/month=08/day=09/hour=01/minute=01/ |
        | s3://mybucket/emails/year={YYYY}/month={MM}/day={dd}/hour={HH}/minute={mm}  | 2025-08-09T01:01 | s3://mybucket/emails/year=2025/month=08/day=09/hour=01/minute=01/ |
        | s3://mybucket/                                                              | 2025-08-09T01:01 | s3://mybucket/                                                    |
        | s3://mybucket                                                               | 2025-08-09T01:01 | s3://mybucket/                                                    |

    Scenario Outline: Invalid Path Prefix
        Given the prefix pattern is <prefix_pattern>
        When the timestamp is <timestamp>
        Then the handler.path_prefix method raised ValueError

        Examples:
        | prefix_pattern     | timestamp        |
        | mybucket           | 2025-08-09T01:01 | # No protocol.
        | s3://              | 2025-08-09T01:01 | # Protocol but no bucket.

    Scenario: Email Handler
        Given SMTP hostname is localhost
        And SMTP port is 8025
        When from address is anne@example.com
        And from name is Anne Person
        And to address is <to_address>
        Then message response is <smtp_response>
        And s3 object count is <s3_object_count>

        Examples:
            | to_address      | smtp_response | topic_name | s3_object_count |
            | foo@example.com | 205           | foo        | 1               |
