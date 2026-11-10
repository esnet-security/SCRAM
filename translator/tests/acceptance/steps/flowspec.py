"""Steps exercising the GoBGP FlowSpec wrapper and translator.process()'s flowspec handling."""

import ipaddress
import json

from api import common_pb2, gobgp_pb2
from behave import then, when
from behave.api.async_step import async_run_until_complete

from translator import translator

_TIMEOUT_SECONDS = 10

_ABSENT = object()

_DATA_FIELDS = ("protocol", "source-port", "destination-port", "action")

_DELETE_WARNING = "Attempted to delete a FlowSpec path that is not in the RIB"


def _flowspec_paths(context, afi):
    """Return every FlowSpec path gobgpd stores for one address family.

    Read with a raw ListPath instead of check_flowspec because that wrapper call is one of the
    things under test: it reports rules gobgpd really holds as missing.
    """
    request = gobgp_pb2.ListPathRequest(
        table_type=gobgp_pb2.TABLE_TYPE_GLOBAL,
        family=common_pb2.Family(afi=afi, safi=common_pb2.Family.SAFI_FLOW_SPEC_UNICAST),
    )
    paths = []
    for response in context.gobgp.stub.ListPath(request, _TIMEOUT_SECONDS):
        paths.extend(response.destination.paths)
    return paths


def _flowspec_counts(context):
    """Count the FlowSpec paths stored per family as an (IPv4, IPv6) tuple."""
    return (
        len(_flowspec_paths(context, common_pb2.Family.AFI_IP)),
        len(_flowspec_paths(context, common_pb2.Family.AFI_IP6)),
    )


def _unicast_counts(context):
    """Count the unicast paths stored per family as an (IPv4, IPv6) tuple."""
    counts = []
    for afi in (common_pb2.Family.AFI_IP, common_pb2.Family.AFI_IP6):
        request = gobgp_pb2.ListPathRequest(
            table_type=gobgp_pb2.TABLE_TYPE_GLOBAL,
            family=common_pb2.Family(afi=afi, safi=common_pb2.Family.SAFI_UNICAST),
        )
        counts.append(sum(len(response.destination.paths) for response in context.gobgp.stub.ListPath(request, 10)))
    return tuple(counts)


def _parse_cell(cell):
    """Convert a behave table cell into the value a SCRAM message would carry.

    An empty cell means the field is absent. A double-quoted cell stays a string, so scenarios can
    exercise string protocols and ports. Any other purely numeric cell becomes an int.

    Returns:
        The parsed value, or _ABSENT when the cell is empty.
    """
    if not cell:
        return _ABSENT
    if len(cell) > 1 and cell.startswith('"') and cell.endswith('"'):
        return cell[1:-1]
    try:
        return int(cell)
    except ValueError:
        return cell


def _rule_from_row(row):
    """Build the (source, destination, data) triple the GoBGP wrapper expects from one table row."""
    source = ipaddress.ip_interface(row["source"]) if row["source"] else None
    destination = ipaddress.ip_interface(row["destination"]) if row["destination"] else None
    data = {}
    for field in _DATA_FIELDS:
        value = _parse_cell(row[field])
        if value is not _ABSENT:
            data[field] = value
    return source, destination, data


def _wellformed_message(event_type, **changes):
    """Build a well-formed v4 filter message; a change value of None removes that key entirely."""
    message = {
        "channel": 1,
        "row": 99,
        "destination": "192.0.2.240/32",
        "source": "192.0.2.241/32",
        "protocol": 6,
        "destination-port": "80",
        "action": "discard",
    }
    for key, value in changes.items():
        if value is None:
            message.pop(key, None)
        else:
            message[key] = value
    return {"type": event_type, "message": message}


def _message_from_row(row):
    """Build the SCRAM-shaped message from the one-row table (type column plus message payload)."""
    message = {"channel": 1, "row": 99}
    for field in ("destination", "source"):
        value = _parse_cell(row[field])
        if value is not _ABSENT:
            message[field] = value
    for field in _DATA_FIELDS:
        value = _parse_cell(row[field])
        if value is not _ABSENT:
            message[field] = value
    return {"type": row["type"], "message": message}


def _track_rule(context, source, destination, data):
    """Remember an added rule for after_scenario cleanup, keeping the tracked list duplicate-free."""
    for tracked in context.flowspec_rules:
        if tracked == (source, destination, data):
            return
    context.flowspec_rules.append((source, destination, data))


def _track_message_rule(context, payload):
    """Remember the rule an add message carries so after_scenario can try to delete it."""
    message = payload.get("message") or {}
    try:
        source = ipaddress.ip_interface(message["source"]) if message.get("source") else None
        destination = ipaddress.ip_interface(message["destination"]) if message.get("destination") else None
    except ValueError:
        return
    data = {field: message[field] for field in _DATA_FIELDS if field in message}
    _track_rule(context, source, destination, data)


class _FakeWebsocket:
    """Stand-in for the websockets connection translator.process() replies on."""

    def __init__(self):
        self.sent = []

    async def send(self, data):
        """Record anything process() sends back."""
        self.sent.append(data)


async def _process_payload(context, payload):
    """Run one message through translator.process() and record any reply on context.ws."""
    context.ws = _FakeWebsocket()
    await translator.process(json.dumps(payload), context.ws, context.gobgp)


@when("a flowspec rule is added")
def add_flowspec_rule(context):
    """Add the FlowSpec rule described by the one-row table and remember it for cleanup."""
    source, destination, data = _rule_from_row(context.table.rows[0])
    context.flowspec_rule = (source, destination, data)
    context.flowspec_baseline = _flowspec_counts(context)
    context.gobgp.add_flowspec(source, destination, data)
    context.flowspec_after_add = _flowspec_counts(context)
    _track_rule(context, source, destination, data)


@when("a flowspec rule is added but the wrapper raises")
def add_flowspec_expect_type_error(context):
    """Pin that a string protocol crashes add_flowspec instead of being coerced.

    _build_flowspec_path int() casts the port fields (gobgp.py lines 187 and 202) but hands the
    protocol value to protobuf raw (line 172), so a string protocol raises TypeError from deep
    inside protobuf. In production translator.process()'s broad except swallows that error.
    """
    source, destination, data = _rule_from_row(context.table.rows[0])
    context.flowspec_baseline = _flowspec_counts(context)
    try:
        context.gobgp.add_flowspec(source, destination, data)
    except TypeError as exc:
        assert "'str' object cannot be interpreted as an integer" in str(exc)
    else:
        failure = "add_flowspec accepted a string protocol without raising TypeError"
        raise AssertionError(failure) from None


@then("the flowspec check finds the rule")
def check_finds_rule(context):
    """The NLRI comparison in _check_flowspec_path_on_rib matches what the add stored."""
    source, destination, data = context.flowspec_rule
    assert context.gobgp.check_flowspec(source, destination, data)


@then("the flowspec check does not find the rule")
def check_misses_rule(context):
    """Pin: the rebuilt NLRI never matches the stored one, so check_flowspec is always False."""
    source, destination, data = context.flowspec_rule
    assert not context.gobgp.check_flowspec(source, destination, data)


@then("deleting the rule removes it cleanly")
def delete_removes_rule(context):
    """del_flowspec matches the stored rule and withdraws it, restoring the RIB counts."""
    source, destination, data = context.flowspec_rule
    context.gobgp.del_flowspec(source, destination, data)
    assert _flowspec_counts(context) == context.flowspec_baseline


@then("deleting the rule warns and leaves it in the RIB")
def delete_warns_and_leaks(context):
    """Pin: when the NLRI comparison fails, del_flowspec skips DeletePath and the rule leaks."""
    source, destination, data = context.flowspec_rule
    context.gobgp.del_flowspec(source, destination, data)
    assert context.log_capture.find_event(_DELETE_WARNING)
    assert context.flowspec_after_add != context.flowspec_baseline
    assert _flowspec_counts(context) == context.flowspec_after_add


@then("exactly {v4:d} IPv4 and {v6:d} IPv6 flowspec paths are stored in the RIB")
def flowspec_rib_counts(context, v4, v6):
    """Pin the exact number of FlowSpec paths in each family's table."""
    assert _flowspec_counts(context) == (v4, v6)


@then("exactly {count:d} IPv4 flowspec paths are stored in the IPv4 RIB")
def flowspec_rib_count_v4(context, count):
    """Pin the FlowSpec path count for the IPv4 family."""
    assert _flowspec_counts(context)[0] == count


@then("exactly {count:d} IPv6 flowspec paths are stored in the IPv6 RIB")
def flowspec_rib_count_v6(context, count):
    """Pin the FlowSpec path count for the IPv6 family."""
    assert _flowspec_counts(context)[1] == count


@then("no unicast routes are stored in the RIB")
def no_unicast_routes(context):
    """Flowspec traffic must never leak into the unicast tables, and vice versa."""
    assert _unicast_counts(context) == (0, 0)


@then("the translator logged {event}")
def translator_logged(context, event):
    """Assert a logged event with this text was emitted during the scenario."""
    assert context.log_capture.find_event(event)


@then("the translator sends no message back")
def translator_sends_nothing(context):
    """Pin: flowspec add and remove never reply over the websocket."""
    assert context.ws.sent == []


@then("the translator sends a check response reporting {blocked} is_blocked")
def check_response_reports(context, blocked):
    """Pin the translator_check_resp message.

    process() rewrites type to translator_check_resp, pops destination and source out of the
    message payload while validating them, and adds is_blocked; channel and row survive untouched.
    """
    assert len(context.ws.sent) == 1
    response = json.loads(context.ws.sent[0])
    assert response["type"] == "translator_check_resp"
    message = response["message"]
    assert message["is_blocked"] is (blocked == "true")
    assert message["channel"] == 1 and message["row"] == 99
    assert "source" not in message
    assert "destination" not in message


@when("a flowspec message is received")
@async_run_until_complete
async def receive_flowspec_message(context):
    """Feed the message described by the one-row table to translator.process()."""
    payload = _message_from_row(context.table.rows[0])
    if payload["type"] == "translator_filter_add":
        _track_message_rule(context, payload)
    await _process_payload(context, payload)


@when("a flowspec-shaped message with an unknown event type is received")
@async_run_until_complete
async def receive_unknown_event_type(context):
    """Pin: SCRAM never sends type "flowspec"; such a message is rejected, not routed anywhere."""
    await _process_payload(context, _wellformed_message("flowspec"))
