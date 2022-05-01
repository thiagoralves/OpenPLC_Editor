# pylint: disable=undefined-variable


from svgui.pyjs.jsonrpc.jsonrpc import JSONRPCServiceBase


class JSONRPCService(JSONRPCServiceBase):

    def serve(self):
        return self.process(request.body.read())

    def __call__(self, func):
        self.methods[func.__name__] = func
        return func
