Feature: Environment Config
    Scenario Outline: Default Values
        Given the Environment Config
        When default Environment Config values are used
        And the S3_PREFIX_PATTERN environment variable is set to 's3://mybucket'
        Then Environment Config attribute <attribute> is <value>

        Examples:
            | attribute             | value     |
            | aws_access_key_id     | None      |
            | aws_secret_access_key | None      |
            | log_level             | 30        |
            | s3_endpoint_url       | None      |
            | s3_prefix_pattern     | None      |
            | smtp_hostname         | 127.0.0.1 |
            | smtp_port             | 8025      |

    Scenario: Invalid Values
        Given the Environment Config
        When the Environment Variable <variable> is set to <value>
        Then a Value Error Exception is Raised

        Examples:
            | variable  | value   |
            | LOG_LEVEL | VERBOSE |
