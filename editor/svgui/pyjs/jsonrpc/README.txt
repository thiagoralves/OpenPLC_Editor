These classes are intended for use server-side.

e.g. in a django view.py :

    from pyjs.jsonrpc.django import JSONService, jsonremote

    jsonservice = JSONRPCService()

    @jsonremote(jsonservice)
    def test(request, echo_param):
         return "echoing the param back: %s" % echo_param

