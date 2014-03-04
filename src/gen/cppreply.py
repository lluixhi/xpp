from utils import _n, _ext, _n_item, get_namespace
from resource_classes import _resource_classes

_templates = {}

_templates['reply_using'] = \
'''\
namespace checked { namespace reply {
using %s =
  xpp::generic::reply<
    xpp::generic::checked::reply<SIGNATURE(xcb_%s_reply)>>;
}; }; // namespace checked::reply

namespace unchecked { namespace reply {
using %s =
  xpp::generic::reply<
    xpp::generic::unchecked::reply<SIGNATURE(xcb_%s_reply)>>;
}; }; // namespace unchecked::reply
'''

def _reply_using(name):
    return _templates['reply_using'] % \
            ( name
            , name
            , name
            , name
            )

_templates['reply_class'] = \
'''\
namespace reply {
template<typename Connection, typename Check>
class %s
  : public xpp::generic::reply<Connection,
                               SIGNATURE(%s_reply),
                               SIGNATURE(%s),
                               %s<Connection, Check>,
                               Check>
  , public xpp::generic::error_handler<Connection, xpp::%s::error::dispatcher>
{
  public:
    typedef xpp::generic::reply<Connection,
                                SIGNATURE(%s_reply),
                                SIGNATURE(%s),
                                %s<Connection, Check>,
                                Check>
                                  base;

    typedef xpp::generic::error_handler<Connection, xpp::%s::error::dispatcher>
      error_handler;

    template<typename ... Parameter>
    %s(Connection && c, Parameter && ... parameter)
      : base(std::forward<Connection>(c), std::forward<Parameter>(parameter) ...)
      , error_handler(std::forward<Connection>(c))
    {}

    void
    handle(const std::shared_ptr<xcb_generic_error_t> & error)
    {
      error_handler::handle(error);
    }
%s\
%s\
}; // class %s
}; // namespace reply
'''

def _reply_class(name, c_name, ns, cookie, accessors):
    return _templates['reply_class'] % \
            ( name
            , c_name # base class
            , c_name # base class
            , name # base class
            , ns # base class
            , c_name # typedef
            , c_name # typedef
            , name # typedef base
            , ns # typedef error_handler
            , name # c'tor
            , cookie.make_static_getter()
            , accessors
            , name
            )

'''\
namespace generic { namespace reply {
template<typename ReplyMethod>
class %s
  : public xpp::generic::reply<ReplyMethod>
             // xpp::generic::checked::reply<SIGNATURE(xcb_%s_reply)>>
{
  public:
    // typedef %s self;
    typedef xpp::generic::reply<ReplyMethod> base;
    using base::base;
%s\
};
}; }; // namespace generic::reply

namespace checked { namespace reply {
using %s =
  generic::reply::%s<
    xpp::generic::checked::reply<SIGNATURE(xcb_%s_reply)>>;
}; }; // namespace checked::reply

namespace unchecked { namespace reply {
using %s =
  generic::reply::%s<
    xpp::generic::unchecked::reply<SIGNATURE(xcb_%s_reply)>>;
}; }; // namespace unchecked::reply
'''

# def _reply_class(name, accessors):
#     return _templates['reply_class'] % \
#             ( name
#             , name
#             , name
#             , accessors
#             , name
#             , name
#             , name
#             , name
#             , name
#             , name
#             )

_templates['reply_member_accessor'] = \
'''\
    template<typename ReturnType = %s, typename ... Parameter>
    ReturnType
    %s(Parameter ... parameter)
    {
      using make = xpp::generic::factory::make<Connection,
                                               decltype(this->get()->%s),
                                               ReturnType,
                                               Parameter ...>;
      return make()(this->get()->%s, this->m_c, parameter ...);
    }
'''

def _reply_member_accessor(request_name, name, c_type, template_type):
    return _templates['reply_member_accessor'] % \
            ( c_type
            , name
            , name
            , name
            )

class CppReply(object):
    def __init__(self, namespace, name, cookie, reply, accessors, parameter_list):
        self.namespace = namespace
        self.name = name
        self.reply = reply
        self.cookie = cookie
        self.accessors = accessors
        self.parameter_list = parameter_list
        self.request_name = _ext(_n_item(self.name[-1]))
        self.c_name = "xcb" \
            + (("_" + get_namespace(namespace)) if namespace.is_ext else "") \
            + "_" + self.request_name

    def make_accessors(self):
        return "\n".join(map(lambda a: "\n%s\n" % a, self.accessors))

    def make(self):
        accessors = [self.make_accessors()]
        naccessors = len(self.accessors)

        for field in self.reply.fields:
            if (field.field_type[-1] in _resource_classes
                and not field.type.is_list
                and not field.type.is_container):

                naccessors = naccessors + 1

                name = field.field_name.lower()
                c_type = field.c_field_type
                template_type = field.field_name.capitalize()

                accessors.append(_reply_member_accessor(self.request_name, name, c_type, template_type))

        # result = "namespace reply {\n"
        result = ""
        result += _reply_class(
            self.request_name, self.c_name, get_namespace(self.namespace),
            self.cookie, "\n".join(accessors))
        return result

        # if naccessors > 0:
        #     result += _reply_class(self.request_name, "\n".join(accessors))
        # else:
        #     result += _reply_using(self.request_name)
        # return result # + "}; // reply\n"
