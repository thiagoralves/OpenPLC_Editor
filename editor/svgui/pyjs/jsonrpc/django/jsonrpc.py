# jsonrpc.py
#   original code: http://trac.pyworks.org/pyjamas/wiki/DjangoWithPyJamas
#   also from: http://www.pimentech.fr/technologies/outils

from __future__ import absolute_import
import datetime
from builtins import str as text

from django.core.serializers import serialize


from svgui.pyjs.jsonrpc.jsonrpc import JSONRPCServiceBase
# JSONRPCService and jsonremote are used in combination to drastically
# simplify the provision of JSONRPC services.  use as follows:
#
# jsonservice = JSONRPCService()
#
# @jsonremote(jsonservice)
# def test(request, echo_param):
#     return "echoing the param back: %s" % echo_param
#
# dump jsonservice into urlpatterns:
#  (r'^service1/$', 'djangoapp.views.jsonservice'),


class JSONRPCService(JSONRPCServiceBase):

    def __call__(self, request, extra=None):
        return self.process(request.raw_post_data)


def jsonremote(service):
    """Make JSONRPCService a decorator so that you can write :

    from jsonrpc import JSONRPCService
    chatservice = JSONRPCService()

    @jsonremote(chatservice)
    def login(request, user_name):
        (...)
    """
    def remotify(func):
        if isinstance(service, JSONRPCService):
            service.add_method(func.__name__, func)
        else:
            emsg = 'Service "%s" not found' % str(service.__name__)
            raise NotImplementedError(emsg)
        return func
    return remotify


# FormProcessor provides a mechanism for turning Django Forms into JSONRPC
# Services.  If you have an existing Django app which makes prevalent
# use of Django Forms it will save you rewriting the app.
# use as follows.  in djangoapp/views.py :
#
# class SimpleForm(forms.Form):
#     testfield = forms.CharField(max_length=100)
#
# class SimpleForm2(forms.Form):
#     testfield = forms.CharField(max_length=20)
#
# processor = FormProcessor({'processsimpleform': SimpleForm,
#                            'processsimpleform2': SimpleForm2})
#
# this will result in a JSONRPC service being created with two
# RPC functions.  dump "processor" into urlpatterns to make it
# part of the app:
#  (r'^formsservice/$', 'djangoapp.views.processor'),


def builderrors(form):
    d = {}
    for error in form.errors.keys():
        if error not in d:
            d[error] = []
        for errorval in form.errors[error]:
            d[error].append(text(errorval))
    return d


# contains the list of arguments in each field
field_names = {
    'CharField': ['max_length', 'min_length'],
    'IntegerField': ['max_value', 'min_value'],
    'FloatField': ['max_value', 'min_value'],
    'DecimalField': ['max_value', 'min_value', 'max_digits', 'decimal_places'],
    'DateField': ['input_formats'],
    'DateTimeField': ['input_formats'],
    'TimeField': ['input_formats'],
    'RegexField': ['max_length', 'min_length'],  # sadly we can't get the expr
    'EmailField': ['max_length', 'min_length'],
    'URLField': ['max_length', 'min_length', 'verify_exists', 'user_agent'],
    'ChoiceField': ['choices'],
    'FilePathField': ['path', 'match', 'recursive', 'choices'],
    'IPAddressField': ['max_length', 'min_length'],
}


def describe_field_errors(field):
    res = {}
    field_type = field.__class__.__name__
    msgs = {}
    for n, m in field.error_messages.items():
        msgs[n] = text(m)
    res['error_messages'] = msgs
    if field_type in ['ComboField', 'MultiValueField', 'SplitDateTimeField']:
        res['fields'] = map(describe_field, field.fields)
    return res


def describe_fields_errors(fields, field_names):
    res = {}
    if not field_names:
        field_names = fields.keys()
    for name in field_names:
        field = fields[name]
        res[name] = describe_field_errors(field)
    return res


def describe_field(field):
    res = {}
    field_type = field.__class__.__name__
    for fname in (field_names.get(field_type, []) +
                  ['help_text', 'label', 'initial', 'required']):
        res[fname] = getattr(field, fname)
    if field_type in ['ComboField', 'MultiValueField', 'SplitDateTimeField']:
        res['fields'] = map(describe_field, field.fields)
    return res


def describe_fields(fields, field_names):
    res = {}
    if not field_names:
        field_names = fields.keys()
    for name in field_names:
        field = fields[name]
        res[name] = describe_field(field)
    return res


class FormProcessor(JSONRPCService):
    def __init__(self, forms, _formcls=None):

        if _formcls is None:
            JSONRPCService.__init__(self)
            for k in forms.keys():
                s = FormProcessor({}, forms[k])
                self.add_method(k, s.__process)
        else:
            JSONRPCService.__init__(self, forms)
            self.formcls = _formcls

    def __process(self, request, params, command=None):

        f = self.formcls(params)

        if command is None:  # just validate
            if not f.is_valid():
                return {'success': False, 'errors': builderrors(f)}
            return {'success': True}

        elif 'describe_errors' in command:
            field_names = command['describe_errors']
            return describe_fields_errors(f.fields, field_names)

        elif 'describe' in command:
            field_names = command['describe']
            return describe_fields(f.fields, field_names)

        elif 'save' in command:
            if not f.is_valid():
                return {'success': False, 'errors': builderrors(f)}
            instance = f.save()  # XXX: if you want more, over-ride save.
            return {'success': True, 'instance': json_convert(instance)}

        elif 'html' in command:
            return {'success': True, 'html': f.as_table()}

        return "unrecognised command"

# The following is incredibly convenient for saving vast amounts of
# coding, avoiding doing silly things like this:
#     jsonresult = {'field1': djangoobject.field1,
#                   'field2': djangoobject.date.strftime('%Y.%M'),
#                    ..... }
#
# The date/time flatten function is there because JSONRPC doesn't
# support date/time objects or formats, so conversion to a string
# is the most logical choice.  pyjamas, being python, can easily
# be used to parse the string result at the other end.
#
# use as follows:
#
# jsonservice = JSONRPCService()
#
# @jsonremote(jsonservice)
# def list_some_model(request, start=0, count=10):
#     l = SomeDjangoModelClass.objects.filter()
#     res = json_convert(l[start:end])
#
# @jsonremote(jsonservice)
# def list_another_model(request, start=0, count=10):
#     l = AnotherDjangoModelClass.objects.filter()
#     res = json_convert(l[start:end])
#
# dump jsonservice into urlpatterns to make the two RPC functions,
# list_some_model and list_another_model part of the django app:
#  (r'^service1/$', 'djangoapp.views.jsonservice'),


def dict_datetimeflatten(item):
    d = {}
    for k, v in item.items():
        k = str(k)
        if isinstance(v, datetime.date):
            d[k] = str(v)
        elif isinstance(v, dict):
            d[k] = dict_datetimeflatten(v)
        else:
            d[k] = v
    return d


def json_convert(l, fields=None):
    res = []
    for item in serialize('python', l, fields=fields):
        res.append(dict_datetimeflatten(item))
    return res
