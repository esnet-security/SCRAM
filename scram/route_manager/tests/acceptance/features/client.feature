Feature: We can register and use clients

  Scenario: We can register a client
    When we register a client named authorized_client.es.net with the uuid of 0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3
    Then we get a 201 status code

  Scenario: We can add a block using an authorized client
    Given a client with block authorization
    When we're logged in
    And we add the entry 1.2.3.4
    Then we get a 201 status code

  Scenario: We can't block with an unauthorized client even if we are logged in
    Given a client without block authorization
    When we're logged in
    And we add the entry 1.2.3.4
    Then we get a 403 status code
