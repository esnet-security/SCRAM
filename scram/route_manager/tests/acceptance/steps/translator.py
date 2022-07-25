from behave import then
from behave.api.async_step import async_run_until_complete
from channels.testing import WebsocketCommunicator

from config.asgi import ws_application


async def query_translator(route, actiontype, is_announced=True):
    communicator = WebsocketCommunicator(ws_application, f"/ws/route_manager/webui_{actiontype}/")
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to({"type": "wui_check_req", "message": {"route": route}})
    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'wui_check_resp'
    assert response['message']['is_blocked'] == is_announced

    await communicator.disconnect()


@then("{route} is announced by {actiontype} translators")
@async_run_until_complete
async def step_impl(context, route, actiontype):
    await query_translator(route, actiontype)


@then("{route} is not announced by {actiontype} translators")
@async_run_until_complete
async def step_impl(context, route, actiontype):
    await query_translator(route, actiontype, is_announced=False)
