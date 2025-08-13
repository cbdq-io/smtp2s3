# smtp2s3
A container to receive SMTP messages and route them to S3 storage.


## Configuration

The container is configured via environment variables.

- `AWS_ACCESS_KEY_ID` The public identifier for your AWS account used to
  specify which account is making a request.
- `AWS_SECRET_ACCESS_KEY` The private cryptographic key paired with the access
  key ID to securely sign and authenticate AWS API requests.
- `LOG_LEVEL` The verbosity of the logging.  Valid values are DEBUG, INFO,
  WARN (or WARNING), ERROR or CRITICAL.  The default is WARN.
- `S3_ENDPOINT_URL` The endpoint to connect to the S3 service.
- `S3_PREFIX_PATTERN` A URL for the prefix of the path to the S3 object to be
  written.  See below for more information.
- `SMTP_DATA_SIZE_LIMIT` The maximum size in bytes for a message to be
  accepted.  Defaults to 10MB.
- `SMTP_HOSTNAME` The host name to run the SMTP service on.  The default is
  127.0.0.1.
- `SMTP_PORT` The port number to run the SMTP service on.  The default is
  8025.

### Substitution in the S3_PREFIX_PATTERN

The following substitutions will be made in the provided pattern to create
the path for writing the data to:
- `{YYYY}` for the year.
- `{MM}` for the month (zero padded).
- `{dd}` for the day (zero padded).
- `{HH}` for the hour (zero padded).
- `{mm}` for the minute (zero padded).

For example if `S3_PREFIX_PATTERN` is set to:

```
s3://mybucket/emails/year={YYYY}/month={MM}/day={dd}/hour={HH}/minute={mm}
```

Then the data for messages will be written to an object with a name looking
like:

```
s3://mybucket/emails/year=2025/month=08/day=12/hour=06/minute=38/b307edd6-6d17-44e2-9af3-3369227cd647.eml.gz
```
