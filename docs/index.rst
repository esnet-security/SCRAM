###################################
 Welcome to SCRAM's documentation!
###################################

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   config
   scram

   howto
   pycharm/configuration
   users

############
 WebSockets
############

WebSockets are used in two places:

#. Between SCRAM and the systems that act on the actions (the
   "translators."). :class:`config.consumers.TranslatorConsumer`

#. Between the user's web browser and SCRAM for asynchronous operations
   (currently just querying about an entry's current status).
   :class:`config.consumers.WebUIConsumer`

**************
 Architecture
**************

SCRAM is the source of truth, and has one or more action types (e.g.
block, redirect, etc.). When an entry is added to SCRAM, it has one
action type assigned to it.

WebSocket messages are sent to the group called
``translator_<actiontype_name>``, such as ``translator_block``. All
translators that implement a block action type subscribe to that group.

Three message types are defined: ``translator_add``,
``translator_remove``, and ``translator_check``. The first two are sent
as entries are added and removed (possibly due to expiration), and the
last is to inquire if the Entry is currently active in the translator.
The translator replies with a ``translator_check_resp`` message.

***************
 WebUIConsumer
***************

When viewing an :class:`scram.route_manager.models.Entry` in the web
interface, we want to know if the entry is currently blocked, and by
which translator(s). In the template for that page, some Javascript code
sends a WebSocket query of type ``wui_check_req``:

.. code::

   {# Open connection to the websocket #}
   let socket = new WebSocket(wss_uri + "/ws/route_manager/webui_block/")

   {# Send status request message #}
   function getStatus(route, pk) {
     let data = {"type": "wui_check_req", "message": {"route": route, "row": pk}};
     sendMessage(socket, JSON.stringify(data))
   }

``wui_check_req`` messages are forwarded to the appropriate translator
group, as a ``translator_check`` message. The ``translator_check_resp``
message is converted to a ``wui_check_resp`` message and returned to the
browser.

####################
 Indices and tables
####################

-  :ref:`genindex`
-  :ref:`modindex`
-  :ref:`search`
