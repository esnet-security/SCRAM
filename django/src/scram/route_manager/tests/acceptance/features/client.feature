Feature: We can register and use clients

  Scenario: We can register a client with a UUID provided
    When we register a client named authorized_client.es.net with the uuid of 0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3
    Then we get a 201 status code

  Scenario: We can register a client without a UUID provided
    When we register a client named authorized_client.es.net and no UUID
    Then we get a 201 status code

  Scenario: We can do an idempotent create of a client with UUID
    When we register a client named authorized_client2.es.net with the uuid of 1e24e7c3-f746-401e-8ae6-3fc3ff3aa814
    Then we get a 201 status code
    When we register a client named authorized_client2.es.net with the uuid of 1e24e7c3-f746-401e-8ae6-3fc3ff3aa814
    Then we get a 200 status code

   Scenario: We do not leak client names
    When we register a client named authorized_client3.es.net with the uuid of 9b3b9fee-3658-4e70-a52d-662f3b2d68ab
    Then we get a 201 status code
    When we register a client named authorized_client3.es.net with the uuid of da6845fb-f8a6-44ec-846a-54f0ee78fcf8
    Then we get a 400 status code


  Scenario: We can add a block using an authorized client
    Given a client with block authorization
    When we're logged in
    And we add the entry 192.0.2.216
    Then we get a 201 status code

  Scenario: We can't block with an unauthorized client even if we are logged in
    Given a client without block authorization
    When we're logged in
    And we add the entry 192.0.2.217
    Then we get a 403 status code
