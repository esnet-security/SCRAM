Feature: Syncing Entries from Other Instances

  Scenario: Entry added from another instance is ingested and announced
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And an entry 192.168.0.10/32 from scram instance "scram2.example.com" is added to the database
    When process_updates is run
    Then 192.168.0.10/32 is announced by block translators

  Scenario: Don't reannounce entries
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And an entry 192.168.0.20/32 from scram instance "current" is added to the database
    When process_updates is run
    Then the entry 192.168.0.20/32 should not be announced again
