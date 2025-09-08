# 查询类定义名节点
query_class_def = {
    'python'    :   '(class_definition name:(identifier) @name) @class',
    'c'         :   '(struct_specifier name:(type_identifier)@name)@class',
    'cpp'       :   '(class_specifier name:(type_identifier)@name)@class',
    'c_sharp'   :   '(class_declaration name:(identifier)@name)@class',
    'java'      :   '(class_declaration name:(identifier)@name)@class',
    'javascript':   '(class_declaration name:(identifier)@name)@class',
    'php'       :   '(class_declaration name: (name) @name) @class',
    'rust'      :   '(struct_item name:(type_identifier)@name)@class',
    'ruby'      :   '(class name:(constant)@name)@class',
    'go'        :   '(type_spec name:(type_identifier)@name)@class',
}
# 查询函数定义名节点
query_func_def = {
    'python'    :   '(function_definition name:(identifier)@name)@func',
    'c'         :   '(function_definition declarator:(function_declarator declarator:(identifier)@name))@func',
    'cpp'       :   '(function_definition declarator:(function_declarator declarator:(identifier)@name))@func',
    'c_sharp'   :   '(local_function_statement name:(identifier)@name)@func',
    'java'      :   '(method_declaration name:(identifier)@name)@func',
    'javascript':   '(function_declaration name:(identifier)@name)@func',
    'php'       :   '(function_definition name:(name)@name)',
    'rust'      :   '(function_item name:(identifier)@name)@func',
    'ruby'      :   '(method name:(identifier)@name)@func',
    'go'        :   '(function_declaration name:(identifier)@name)@func',
}
# 查询索引节点
query_subscript = {
    'python': {
        'integer': '(subscript value: (identifier)@value subscript:(integer) @index) @node',
        'string': '(subscript value: (identifier)@value subscript:(string (string_content)@index)) @node',
        'identifier': '(subscript value: (identifier)@value subscript:(identifier) @index) @node',
    },
    'c': {
        'integer': '(subscript_expression argument:(identifier)@value index:(number_literal)@index)@node',
        'identifier': '(subscript_expression argument: (identifier) @value index: (identifier) @index) @node',
        'string': '(subscript_expression argument:(identifier)@value index:(char_literal)@index)@node',
    },  
    'cpp': {
        'integer': '(subscript_expression argument: (identifier) @value indices: (subscript_argument_list (number_literal)@index)) @node',
        'string': '(subscript_expression argument: (identifier) @value indices: (subscript_argument_list (string_literal (string_content)@index))) @node',
        'identifier': '(subscript_expression argument: (identifier) @value indices: (subscript_argument_list (identifier)@index)) @node',
    },
    'c_sharp': {
        'integer': '(element_access_expression expression:(identifier)@value subscript:(bracketed_argument_list (argument (integer_literal)@index)))@node',
        'string': '(element_access_expression expression:(identifier)@value subscript:(bracketed_argument_list (argument (string_literal (string_literal_content)@index)@index)))@node',
        'identifier': '(element_access_expression expression:(identifier)@value subscript:(bracketed_argument_list (argument (identifier)@index)))@node',
    },
    'java': {
        'integer':'(array_access array: (identifier) @value index: (decimal_integer_literal) @index) @node',
        'string': '(array_access array: (identifier) @value index: (character_literal) @index) @node',
        'identifier': '(array_access array: (identifier) @value index: (identifier) @index) @node',
    },
    'javascript': {
        'integer': '(subscript_expression object:(identifier) @value index:(number) @index)',
        'string': '(subscript_expression object:(identifier) @value index:(string (string_fragment)@index))',
        'identifier': '(subscript_expression object:(identifier) @value index:(identifier) @index)',
    },
    'php': {
        'integer': '(subscript_expression (variable_name)@value (integer)@index)@node',
        'string': '(subscript_expression (variable_name)@value (string (string_content)@index))@node',
        'identifier': '(subscript_expression (variable_name)@value (name)@index)@node',
    },
    'rust':{
        'integer':'(index_expression (identifier) @value (integer_literal) @index) @node',
        'string': '(index_expression (identifier) @value (char_literal) @index) @node',
        'identifier': '(index_expression (identifier) @value (identifier) @index) @node',
    },         
    'ruby': {
        'integer': '(element_reference object:(identifier)@value (integer)@index)@node',
        'string': '(element_reference object:(identifier)@value (string (string_content)@index))@node',
        'identifier': '(element_reference object:(identifier)@value (identifier)@index)@node',
    },
    'go': {
        'integer': '(index_expression operand: (identifier) @value index: (int_literal) @index) @node',
        'identifier': '(index_expression operand: (identifier) @value index: (identifier) @index) @node',
        'string': '(index_expression operand: (identifier) @value index: (rune_literal) @index) @node'
    },   
    'swift':{
        'integer': '(subscript name:(variable_name)@value index:(number)@index)',
        'string': '(subscript name:(variable_name)@value index:(word)@index)',
        'identifier': '(subscript name:(variable_name)@value index:(raw_string)@index)',
    }
}
# 查询类实例化
query_class_call = {
    'c': '(declaration type:(type_identifier)@class)@node',
    'cpp': '(declaration type:(type_identifier)@class)@node',
    'c_sharp': '(variable_declaration type:(identifier)@class)@node',
    'go': '(composite_literal type:(type_identifier)@class)@node',
    'python': '(call function:(identifier)@class)@node',
    'php': '(object_creation_expression (name)@class)@node',
    'java': '(local_variable_declaration type:(type_identifier)@class)@node',
    'javascript': '(new_expression constructor:(identifier)@class)@node',
    'rust': '(call_expression function:(scoped_identifier path:(identifier)@class))@node',
    'ruby': '(call receiver:(constant)@class)@node'
}
# 查询方法调用节点
query_func_call = {
    'python'    :   '(call function:(identifier)@func )@call',
    'c'         :   '(call_expression function:(identifier)@func)@call',
    'cpp'       :   '(call_expression function:(identifier)@func)@call',
    'c_sharp'   :   '(invocation_expression function:(identifier)@func)@call',
    'java'      :   '(method_invocation name:(identifier)@func)@call',
    'javascript':   '(call_expression function:(identifier)@func)@call',
    'php'       :   '(function_call_expression function:(name)@func)@call',
    'rust'      :   '(call_expression function:(identifier)@func)@call',
    'ruby'      :   '(call method:(identifier)@func)@call',
    'go'        :   '(call_expression function:(identifier)@func)@call',
}
# 查询方法调用节点
query_parameters = {
    'python'    :   '(call function:(_)@func arguments:(_ (_)@paras))@call',
    'c'         :   '(call_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'cpp'       :   '(call_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'c_sharp'   :   '(invocation_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'java'      :   '(method_invocation name:(_)@func arguments:(_ (_)@paras))@call',
    'javascript':   '(call_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'php'       :   '(function_call_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'rust'      :   '(call_expression function:(_)@func arguments:(_ (_)@paras))@call',
    'ruby'      :   '(call method:(_)@func arguments:(_ (_)@paras))@call',
    'go'        :   '(call_expression function:(_)@func arguments:(_ (_)@paras))@call',
}
# 查询binary表达式
query_binary_expression = {
    'python'    :   '(binary_operator left: (_) @left right: (_) @right)@binary',
    'c'         :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'cpp'       :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'c_sharp'   :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'java'      :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'javascript':   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'php'       :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'rust'      :   '(binary_expression left:(_)@left right:(_)@right)@binary',
    'ruby'      :   '(binary left:(_)@left right:(_)@right)@binary',
    'go'        :   '(binary_expression left:(_)@left right:(_)@right)@binary',
}
# 查询if判断语句
query_if_condition = {
    'python'    :   '(if_statement ("if")@if condition:(_)@condition)',
    'c'         :   '(if_statement ("if")@if condition:(_ ("(") (_)@condition (")")))',
    'cpp'       :   '(if_statement ("if")@if condition:(_)@condition)',
    'c_sharp'   :   '(if_statement ("if")@if condition:(_)@condition)',
    'java'      :   '(if_statement ("if")@if condition:(_ ("(")(_)@condition(")")))',
    'javascript':   '(if_statement ("if")@if condition:(_ ("(")(_)@condition(")")))',
    'php'       :   '(if_statement ("if")@if condition:(_ ("(")(_)@condition (")")))',
    'rust'      :   '(if_expression ("if")@if condition:(_)@condition)',
    'ruby'      :   '(if ("if")@if condition:(_)@condition)',
    'go'        :   '(if_statement ("if")@if condition:(_ ("(")(_)@condition(")")))',
}
# 查询返回值语句
query_return = {
    'python'    :   '(return_statement ("return") (_)@value)@return',
    'c'         :   '(return_statement ("return") (_)@value)@return',
    'cpp'       :   '(return_statement ("return") (_)@value)@return',
    'c_sharp'        :   '(return_statement ("return") (_)@value)@return',
    'java'      :   '(return_statement ("return") (_)@value)@return',
    'javascript':   '(return_statement ("return") (_)@value)@return',
    'php'       :   '(return_expression ("return") (_)@value)@return',
    'rust'      :   '(return_expression ("return") (_)@value)@return',
    'ruby'      :   '(return ("return") (_)@value)@return',
    'go'        :   '(return_statement ("return") (_)@value)@return',
}
# 查询string
query_string = {
    'python'    :   '(string)@node',
    'c'         :   '(char_literal)@node',
    'cpp'       :   '(char_literal)@node',
    'c_sharp'   :   '(character_literal)@node',
    'go'        :   '(interpreted_string_literal)@node', # 带有""
    'javascript':   '(string)@node',
    'php'       :   '(string)@node', # 带有“”
    'rust'      :   '(string_literal)@node',
    'ruby'      :   '(string)@node',
    'java'      :   '(string_literal)@node',
}
# 查询注释
query_comment = {
    'python'    :   '(comment)@node', # #
    'c'         :   '(comment) @node', # // /* */
    'cpp'       :   '(comment) @node', # // /* */
    'c_sharp'   :   '(comment) @node', # // /* */
    'java'      :   '(line_comment) @node', # //
    'javascript':   '(comment) @node', # // /* */
    'php'       :   '(comment) @node', # // # /* */
    'rust'      :   '(line_comment) @node',# //
    'ruby'      :   '(comment) @node', # #
    'go'        :   '(comment) @node', # // /* */
}
# 查询引入
query_import = {
    'python': {
        'import_only': '(import_statement (dotted_name)@ref)@full',
        'import_from': '(import_from_statement (dotted_name)@package_name ("import") (dotted_name)@ref)@full'
    },
    'c': {
        'system':'(preproc_include path:(system_lib_string)@ref)@full',
        'local':'(preproc_include path:(string_literal)@ref)@full'
    },
    'cpp': {
        'system':'(preproc_include path:(system_lib_string)@ref)@full',
        'local':'(preproc_include path:(string_literal)@ref)@full'
    },
    'c_sharp'        :   '(using_directive ("using") (_)@ref)@full',
    'java'      :   '(import_declaration ("import") (_)@ref)@full',
    'javascript':   '(import_statement source:(string (string_fragment)@ref))@full',
    'php': {
        'require': '(require_expression ("require") (_ ("'")(_)@ref("'")))@full',
        'include': '(include_expression ("include") (_ ("'")(_)@ref("'")))@full'
    },     
    'rust':{
        'a': '(use_declaration argument:(_ path:(scoped_identifier)@path name:(identifier)@ref))@full',
        'b': '(use_declaration argument:(_ path:(identifier)@ref))@full' 
    }, 
    'ruby'      :   '(call method:(identifier)@require arguments:(argument_list(string (string_content)@ref)))@full', # require == 'require'
    'go'        :   '(import_declaration (_ (import_spec path:(_)@ref)))@full', # import ( "github.com/gin-gonic/gin" "myproject/utils")
}
