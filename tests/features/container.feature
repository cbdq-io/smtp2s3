Feature: Test the smtp2s3 container
    In order to maintain the container
    As a container maintain
    I want verify the container artefact

    Scenario: Verify the container
        Given the TestInfra host with URL "docker://sut" is ready
        When the TestInfra user is "nobody"
        Then the TestInfra user is present
        And the TestInfra user group is nobody
        And the TestInfra user shell is /sbin/nologin
