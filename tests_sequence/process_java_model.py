import xml.etree.ElementTree as ET
from more_itertools import peekable


NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"


def printi(*args, **kwargs):
    indent = " " * printi.depth * 2
    print(f"{indent}", *args, **kwargs)


printi.depth = 0


def printi_depth(func):
    def wrapper(*args, **kwargs):
        printi.depth += 1
        res = func(*args, **kwargs)
        printi.depth -= 1
        return res

    return wrapper


def generate_sequence(xmi_string):
    try:
        generate_sequence.root = ET.fromstring(xmi_string)

        body_declaration = generate_sequence.root.find(
            "ownedElements"
            f"/ownedElements[@{NS_XSI}type='java:ClassDeclaration']"
            f"/bodyDeclarations[@{NS_XSI}type='java:MethodDeclaration']"
        )
        body = body_declaration.find("body")
        for _parameters in body_declaration.findall("parameters"):
            pass

        return process_elt(body)
    except Exception as e:
        print("exception:", e)
        return []


generate_sequence.root = None


@printi_depth
def find_element_by_model_path(path):
    # printi("find_by_path", path)

    if not path.startswith("//"):
        print("weird path", path)
    path = path[2:]

    curr_elt = generate_sequence.root

    full_path = []

    for part in path.split("/"):
        if not path.startswith("@"):
            print("weird part", path)
        part = part[1:]
        part = part.split(".")
        elt_tag = part[0]
        elt_idx = int(part[1]) if len(part) > 1 else 0

        new_elt = curr_elt.findall(elt_tag)[elt_idx]
        if new_elt.tag == "ownedPackages":
            full_path.append(curr_elt.get("name"))
        curr_elt = curr_elt.findall(elt_tag)[elt_idx]

    full_path.append(curr_elt.get("name"))
    curr_elt.set("fullpath", ".".join(full_path))

    return curr_elt


def is_discarded(elt):
    if elt.tag == "comments":
        return True
    return False


def filter_iter(elt):
    return peekable(child for child in elt if not is_discarded(child))


@printi_depth
def process_elt(elt):
    # printi("handling", elt.tag, elt.get(f"{NS_XSI}type"))
    if elt is None:
        print("### PROBLEM process None")

    handlers = {
        "java:Block": process_Block,
        "java:ExpressionStatement": process_ExpressionStatement,
        "java:EnhancedForStatement": process_EnhancedForStatement,
        "java:MethodInvocation": process_MethodInvocation,
        "java:IfStatement": process_IfStatement,
        "java:InfixExpression": process_InfixExpression,
        "java:ReturnStatement": process_ReturnStatement,
        "java:Assignment": process_Assignment,
        "java:ClassInstanceCreation": process_ClassInstanceCreation,
        "java:FieldAccess": process_FieldAccess,
        "java:SuperFieldAccess": process_SuperFieldAccess,
        "java:UnresolvedItemAccess": process_UnresolvedItemAccess,
        "java:SuperMethodInvocation": process_SuperMethodInvocation,
        "java:VariableDeclarationStatement": process_VariableDeclarationStatement,
        "java:PrefixExpression": process_PrefixExpression,
        "java:ConditionalExpression": process_ConditionalExpression,
        "java:ParenthesizedExpression": process_ParenthesizedExpression,
        "java:SynchronizedStatement": process_SynchronizedStatement,
        "java:CastExpression": process_CastExpression,
        "java:TryStatement": process_TryStatement,
        "java:TypeLiteral": process_TypeLiteral,
        "java:ThrowStatement": process_ThrowStatement,
        "java:InstanceofExpression": process_InstanceofExpression,
        "java:ArrayCreation": process_ArrayCreation,
        "java:WhileStatement": process_WhileStatement,
        "java:ForStatement": process_ForStatement,
        "java:PostfixExpression": process_PostfixExpression,
        "java:VariableDeclarationExpression": process_VariableDeclarationExpression,
        "java:ArrayLengthAccess": process_ArrayLengthAccess,
        "java:ArrayAccess": process_ArrayAccess,
        "java:SingleVariableAccess": process_SingleVariableAccess,
        "java:SwitchStatement": process_SwitchStatement,
        "java:SwitchCase": process_SwitchCase,
        "java:BreakStatement": process_BreakStatement,
        "java:ContinueStatement": process_ContinueStatement,
        "java:DoStatement": process_DoStatement,
        "java:ArrayInitializer": process_ArrayInitializer,
        "java:AssertStatement": process_AssertStatement,
        "java:TypeAccess": process_TypeAccess,
        "java:PackageAccess": process_PackageAccess,
        "java:LabeledStatement": process_LabeledStatement,
        "java:TypeDeclarationStatement": process_TypeDeclarationStatement,
        "java:ThisExpression": process_ThisExpression,
        "java:SuperConstructorInvocation": process_SuperConstructorInvocation,
        "java:NullLiteral": process_AnyLiteral,
        "java:StringLiteral": process_AnyLiteral,
        "java:BooleanLiteral": process_AnyLiteral,
        "java:NumberLiteral": process_AnyLiteral,
        "java:CharacterLiteral": process_AnyLiteral,
        "java:EmptyStatement": lambda elt, itr: [],
    }
    itr = filter_iter(elt)

    elt_type = elt.get(f"{NS_XSI}type")

    if elt_type is None and elt.tag in ["body", "finally"]:
        res = process_Block(elt, itr)
    elif elt_type not in handlers:
        res = process_not_implemented(elt, itr)
    else:
        res = handlers[elt_type](elt, itr)

    for child in itr:
        raise Exception(f"extra child in {elt_type}: {child.tag} {child.items()}")

    return res


def assert_elt(elt, elt_tag):
    if elt.tag != elt_tag:
        raise Exception(f"assert_elt {elt_tag}: {elt.tag} {elt.items()}")


def next_elt(itr, elt_tag):
    elt = next(itr)
    assert_elt(elt, elt_tag)
    return elt


def get_maybe(itr, elt_tag):
    if itr.peek(None) is not None and itr.peek().tag == elt_tag:
        return next_elt(itr, elt_tag)
    return None


def get_many(itr, elt_tag):
    while itr.peek(None) is not None and itr.peek().tag == elt_tag:
        yield next_elt(itr, elt_tag)


@printi_depth
def get_to_path(elt):
    elt_type = elt.get(f"{NS_XSI}type")

    # printi("get_to_path", elt_type, elt.items())

    if elt_type == "java:UnresolvedItemAccess":
        to = [find_element_by_model_path(elt.get("element")).get("name")]
    elif elt_type == "java:SingleVariableAccess":
        variable = elt.get("variable")
        if variable is not None:
            to = [find_element_by_model_path(elt.get("variable")).get("name")]
        else:
            return None
    elif elt_type in [
        "java:MethodInvocation",
        "java:SuperMethodInvocation",
        "java:ClassInstanceCreation",
        "java:StringLiteral",
        "java:NullLiteral",
        "java:ArrayAccess",
        "java:InfixExpression",
        "java:ConditionalExpression",
    ]:
        return None
    elif elt_type == "java:ThisExpression":
        qualifier = elt.find("qualifier")
        if qualifier is not None:
            elt = qualifier
            to = [find_element_by_model_path(elt.get("type")).get("name")]
        else:
            to = []
    elif elt_type == "java:SuperFieldAccess" or elt_type == "java:FieldAccess":
        qualifier = elt.find("qualifier")
        field = elt.find("field")
        to = []
        if qualifier is not None:
            elt = qualifier
            to += [find_element_by_model_path(elt.get("type")).get("name")]
        else:
            elt = None
        if field is not None:
            to += [find_element_by_model_path(field.get("variable")).get("name")]
    elif elt_type == "java:TypeAccess":
        to = [find_element_by_model_path(elt.get("type")).get("name")]
    elif elt_type == "java:ParenthesizedExpression":
        return get_to_path(elt.find("expression"))
    elif elt_type == "java:CastExpression":
        return get_to_path(elt.find("expression"))
    elif elt_type == "java:TypeLiteral":
        type_literal = elt.find("type")
        return [
            find_element_by_model_path(type_literal.get("type")).get("name"),
            "class",
        ]
    elif elt_type == "java:PackageAccess":
        return [find_element_by_model_path(elt.get("package")).get("fullpath")]
    elif elt_type == "java:Assignment":
        left_hand_side = elt.find("leftHandSide")
        return get_to_path(left_hand_side)
    else:
        raise Exception(f"get_to_path: {elt} {elt.items()}")

    child_to = []
    children = elt.findall("*") if elt is not None else []
    children = [child for child in filter_iter(children)]
    if len(children) > 0:
        child = children[-1]
        child_to = get_to_path(child)
        if child_to is None:
            return None

    return child_to + to


@printi_depth
def get_guard_name(elt):
    if elt is None:
        return None

    elt_type = elt.get(f"{NS_XSI}type")

    if elt_type == "java:InfixExpression":
        left = elt.find("leftOperand")
        right = elt.find("rightOperand")
        return f"{get_guard_name(left)} {elt.get('operator')} {get_guard_name(right)}"
    elif elt_type == "java:NumberLiteral":
        return elt.get("tokenValue")
    elif elt_type == "java:SingleVariableAccess":
        return find_element_by_model_path(elt.get("variable")).get("name")
    elif (
        elt_type == "java:MethodInvocation" or elt_type == "java:SuperMethodInvocation"
    ):
        return (
            "[...]."
            + find_element_by_model_path(elt.get("method")).get("name")
            + ("([...])" if elt.find("arguments") is not None else "()")
        )
    elif elt_type == "java:NullLiteral":
        return "null"
    elif elt_type == "java:UnresolvedItemAccess":
        return find_element_by_model_path(elt.get("element")).get("name")
    elif elt_type == "java:SuperFieldAccess" or elt_type == "java:FieldAccess":
        field = elt.find("field")
        if field is not None:
            return find_element_by_model_path(field.get("variable")).get("name")
        qualifier = elt.find("qualifier")
        if qualifier is not None:
            return find_element_by_model_path(elt.get("type")).get("name")
    elif elt_type == "java:PrefixExpression":
        return f"{elt.get('operator')}{get_guard_name(elt.find('operand'))}"
    elif elt_type == "java:PostfixExpression":
        return f"{get_guard_name(elt.find('operand'))}{elt.get('operator')}"
    elif elt_type == "java:ParenthesizedExpression":
        return f"({get_guard_name(elt.find('expression'))})"
    elif elt_type == "java:ThisExpression":
        qualifier = elt.find("qualifier")
        if qualifier is not None:
            return find_element_by_model_path(qualifier.get("type")).get("name")
        else:
            return "this"
    elif elt.tag == "exception":
        return (
            f"{find_element_by_model_path(elt.find('type').get('type')).get('name')} "
            f"{elt.get('name')}"
        )
    elif elt_type == "java:TypeLiteral":
        type_literal = elt.find("type")
        return (
            f"{find_element_by_model_path(type_literal.get('type')).get('name')}.class"
        )
    elif elt_type == "java:InstanceofExpression":
        left = elt.find("leftOperand")
        right = elt.find("rightOperand")
        return f"{get_guard_name(left)} instanceof {get_guard_name(right)}"
    elif elt.tag == "rightOperand" and elt_type is None:
        return find_element_by_model_path(elt.get("type")).get("name")
    elif elt_type == "java:ArrayLengthAccess":
        return f"{get_guard_name(elt.find('array'))}.length"
    elif elt_type == "java:CharacterLiteral":
        return elt.get("escapedValue")
    elif elt_type == "java:ArrayAccess":
        return (
            f"{get_guard_name(elt.find('array'))}[{get_guard_name(elt.find('index'))}]"
        )
    elif elt_type == "java:Assignment":
        left = elt.find("leftHandSide")
        right = elt.find("rightHandSide")
        operator = elt.get("operator")
        return (
            f"{get_guard_name(left)} "
            f"{operator if operator is not None else '='} "
            f"{get_guard_name(right)}"
        )
    elif elt_type == "java:BooleanLiteral":
        return elt.get("value")
    elif elt_type == "java:ConditionalExpression":
        return (
            f"{get_guard_name(elt.find('expression'))} ? "
            f"{get_guard_name(elt.find('thenExpression'))} : "
            f"{get_guard_name(elt.find('elseExpression'))}"
        )
    elif elt_type == "java:CastExpression":
        return (
            f"({find_element_by_model_path(elt.find('type').get('type')).get('name')}) "
            f"{get_guard_name(elt.find('expression'))}"
        )
    elif elt_type == "java:ClassInstanceCreation":
        return (
            f"new {find_element_by_model_path(elt.find('type').get('type')).get('name')}"
            + ("([...])" if elt.find("arguments") is not None else "()")
        )
    elif elt_type == "java:ArrayCreation":
        return f"new {find_element_by_model_path(elt.find('type').get('type')).get('name')}[]"
    elif elt_type == "java:StringLiteral":
        return elt.get("escapedValue")

    raise Exception(f"get_guard_name: {elt} {elt.items()}")


def process_not_implemented(elt, itr):
    raise Exception(f"nnot_implemented: {elt} {elt.items()}")


def process_AnyLiteral(elt, itr):
    return []


def process_Block(elt, itr):
    contents = []

    for child in itr:
        assert_elt(child, "statements")
        contents += process_elt(child)

    return contents


def process_ExpressionStatement(elt, itr):
    expression = next_elt(itr, "expression")
    return process_elt(expression)


def process_EnhancedForStatement(elt, itr):
    body = next_elt(itr, "body")
    expression = next_elt(itr, "expression")
    param = next_elt(itr, "parameter")

    return process_elt(expression) + [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "for",
                    "guard": f"{param.get('name')} in {get_guard_name(expression)}",
                    "contents": [{"type": "scopedVariable", "name": param.get("name")}]
                    + process_elt(body),
                }
            ],
        }
    ]


def process_MethodInvocation(elt, itr):
    res = []

    for arguments in get_many(itr, "arguments"):
        res += process_elt(arguments)

    for _type_arguments in get_many(itr, "typeArguments"):
        pass

    expression = get_maybe(itr, "expression")
    to = None
    if expression is not None:
        to = get_to_path(expression)
        res += process_elt(expression)
    else:
        to = []

    method = elt.get("method")
    return res + [
        {
            "type": "methodInvocation",
            "to": to if to is not None else "### unk",
            "method": find_element_by_model_path(elt.get("method")).get("name")
            if method is not None
            else "### unk",
        }
    ]


def process_SuperMethodInvocation(elt, itr):
    to = None
    qualifier = get_maybe(itr, "qualifier")
    if qualifier is not None:
        to = []
        child = qualifier.find("*")
        if child is not None:
            to += get_to_path(child)
        to += [find_element_by_model_path(qualifier.get("type")).get("name")]
    else:
        to = []

    res = []
    for arguments in get_many(itr, "arguments"):
        res += process_elt(arguments)

    method = elt.get("method")
    return res + [
        {
            "type": "methodInvocation",
            "to": to if to is not None else "### unk",
            "method": find_element_by_model_path(elt.get("method")).get("name")
            if method is not None
            else "### unk",
        }
    ]


def process_SuperConstructorInvocation(elt, itr):
    expression = get_maybe(itr, "expression")
    res = []
    to = None

    if expression is not None:
        to = get_to_path(expression)
        res += process_elt(expression)
    else:
        to = []

    for arguments in get_many(itr, "arguments"):
        res += process_elt(arguments)
    return res + [
        {
            "type": "methodInvocation",
            "to": to if to is not None else "### unk",
        }
    ]


def process_IfStatement(elt, itr):
    expression = next_elt(itr, "expression")
    then_block = next_elt(itr, "thenStatement")
    else_block = get_maybe(itr, "elseStatement")

    blocks = [
        {
            "name": "if",
            "guard": get_guard_name(expression),
            "contents": process_elt(then_block),
        }
    ]

    if else_block is not None:
        blocks += [
            {
                "name": "else",
                "guard": None,
                "contents": process_elt(else_block),
            }
        ]

    return process_elt(expression) + [
        {
            "type": "blocks",
            "blocks": blocks,
        }
    ]


def process_InfixExpression(elt, itr):
    right_operand = next_elt(itr, "rightOperand")
    left_operand = next_elt(itr, "leftOperand")
    res = []
    for extended_operands in get_many(itr, "extendedOperands"):
        res += process_elt(extended_operands)
    return process_elt(left_operand) + process_elt(right_operand) + res


def process_ReturnStatement(elt, itr):
    contents = []
    expression = get_maybe(itr, "expression")
    if expression is not None:
        contents += process_elt(expression)
    return contents + [
        {
            "type": "return",
            "value": get_guard_name(expression) if expression is not None else None,
        }
    ]


def process_Assignment(elt, itr):
    _left_hand_side = next_elt(itr, "leftHandSide")
    right_hand_side = next_elt(itr, "rightHandSide")
    # INFO maybe this should be a new scoped variable
    # return process_elt(right_hand_side) + [
    #     {"type": "scopedVariable", "name": get_to_path(left_hand_side)}
    # ]
    return process_elt(right_hand_side)


def process_ClassInstanceCreation(elt, itr):
    res = []
    for arguments in get_many(itr, "arguments"):
        res += process_elt(arguments)

    _anonymous_class_decl = get_maybe(itr, "anonymousClassDeclaration")
    expression = get_maybe(itr, "expression")
    if expression is not None:
        res += process_elt(expression)
    instance_type = next_elt(itr, "type")

    return res + [
        {
            "type": "newInstance",
            "new_type": find_element_by_model_path(instance_type.get("type")).get(
                "name"
            ),
        }
    ]


def process_FieldAccess(elt, itr):
    _field = next_elt(itr, "field")
    expression = next_elt(itr, "expression")
    return process_elt(expression)


def process_SuperFieldAccess(elt, itr):
    qualifier = get_maybe(itr, "qualifier")
    res = []
    if qualifier is not None:
        for elt in qualifier.find("*"):
            res += process_elt(elt)
    _field = next_elt(itr, "field")
    return res


def process_UnresolvedItemAccess(elt, itr):
    qualifier = get_maybe(itr, "qualifier")
    if qualifier is not None:
        return process_elt(qualifier)
    return []


def process_VariableDeclarationStatement(elt, itr):
    res = []
    res_scoped_variables = []

    _variable_type = next_elt(itr, "type")

    for fragments in get_many(itr, "fragments"):
        res_scoped_variables.append(
            {"type": "scopedVariable", "name": fragments.get("name")}
        )

        fragments = filter_iter(fragments)
        initializer = get_maybe(fragments, "initializer")
        if initializer is not None:
            res += process_elt(initializer)

    _modifier = next_elt(itr, "modifier")
    for _annotations in get_many(itr, "annotations"):
        pass

    return res + res_scoped_variables


def process_VariableDeclarationExpression(elt, itr):
    res = []
    res_scoped_variables = []

    _variable_type = next_elt(itr, "type")

    for fragments in get_many(itr, "fragments"):
        res_scoped_variables.append(
            {"type": "scopedVariable", "name": fragments.get("name")}
        )

        fragments = filter_iter(fragments)
        initializer = get_maybe(fragments, "initializer")
        if initializer is not None:
            res += process_elt(initializer)

    _modifier = next_elt(itr, "modifier")
    for _annotations in get_many(itr, "annotations"):
        pass

    return res + res_scoped_variables


def process_PrefixExpression(elt, itr):
    operand = next_elt(itr, "operand")
    return process_elt(operand)


def process_ConditionalExpression(elt, itr):
    else_expr = next_elt(itr, "elseExpression")
    cond_expr = next_elt(itr, "expression")
    then_expr = next_elt(itr, "thenExpression")
    return process_elt(cond_expr) + [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "if",
                    "guard": get_guard_name(cond_expr),
                    "contents": process_elt(then_expr),
                },
                {
                    "name": "else",
                    "guard": None,
                    "contents": process_elt(else_expr),
                },
            ],
        }
    ]


def process_ParenthesizedExpression(elt, itr):
    expression = next_elt(itr, "expression")
    return process_elt(expression)


def process_SynchronizedStatement(elt, itr):
    body = next_elt(itr, "body")
    expression = next_elt(itr, "expression")
    return process_elt(expression) + [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "synchronized",
                    "guard": get_guard_name(expression),
                    "contents": process_elt(body),
                }
            ],
        }
    ]


def process_CastExpression(elt, itr):
    expression = next_elt(itr, "expression")
    _type = next_elt(itr, "type")
    return process_elt(expression)


def process_TryStatement(elt, itr):
    catch_res = []
    body = next_elt(itr, "body")
    finally_clause = get_maybe(itr, "finally")
    for catch_clauses in get_many(itr, "catchClauses"):
        catch_clauses = filter_iter(catch_clauses)
        exception = next_elt(catch_clauses, "exception")
        catch_body = next_elt(catch_clauses, "body")
        catch_res.append(
            {
                "contents": process_elt(catch_body),
                "guard": get_guard_name(exception),
            }
        )
    return [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "try",
                    "guard": None,
                    "contents": process_elt(body),
                },
            ]
            + [
                {
                    "name": "catch",
                    "guard": catch["guard"],
                    "contents": catch["contents"],
                }
                for catch in catch_res
            ]
            + (
                [
                    {
                        "name": "finally",
                        "guard": None,
                        "contents": process_elt(finally_clause),
                    }
                ]
                if finally_clause
                else []
            ),
        }
    ]


def process_TypeLiteral(elt, itr):
    _type = next_elt(itr, "type")
    return []


def process_ThrowStatement(elt, itr):
    expression = next_elt(itr, "expression")
    # return process_elt(expression) + [{"type": "throw"}]
    return process_elt(expression) + [{"type": "controlFlow", "name": "throw"}]


def process_InstanceofExpression(elt, itr):
    _right_operand = next_elt(itr, "rightOperand")
    left_operand = next_elt(itr, "leftOperand")
    return process_elt(left_operand)


def process_ArrayCreation(elt, itr):
    res = []
    for dimensions in get_many(itr, "dimensions"):
        res += process_elt(dimensions)
    initializer = get_maybe(itr, "initializer")
    if initializer is not None:
        initializer = filter_iter(initializer)
        for expressions in get_many(initializer, "expressions"):
            res += process_elt(expressions)
    _type = next_elt(itr, "type")
    return res


def process_WhileStatement(elt, itr):
    expression = next_elt(itr, "expression")
    body = next_elt(itr, "body")
    return process_elt(expression) + [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "while",
                    "guard": get_guard_name(expression),
                    "contents": process_elt(body),
                }
            ],
        }
    ]


def process_ForStatement(elt, itr):
    cond_expr = get_maybe(itr, "expression")
    res_updaters = []
    for updaters in get_many(itr, "updaters"):
        res_updaters += process_elt(updaters)
    res_initializers = []
    for initializers in get_many(itr, "initializers"):
        res_initializers += process_elt(initializers)
    body = next_elt(itr, "body")

    return [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "for init",
                    "guard": None,
                    "contents": res_initializers,
                },
                {
                    "name": "for",
                    "guard": get_guard_name(cond_expr),
                    "contents": (
                        process_elt(cond_expr) if cond_expr is not None else []
                    )
                    + process_elt(body)
                    + res_updaters,
                },
            ],
        }
    ]


def process_PostfixExpression(elt, itr):
    operand = next_elt(itr, "operand")
    return process_elt(operand)


def process_ArrayLengthAccess(elt, itr):
    array = next_elt(itr, "array")
    return process_elt(array)


def process_ArrayAccess(elt, itr):
    array = next_elt(itr, "array")
    index = next_elt(itr, "index")
    return process_elt(array) + process_elt(index)


def process_SingleVariableAccess(elt, itr):
    qualifier = get_maybe(itr, "qualifier")
    if qualifier is not None:
        return process_elt(qualifier)
    return []


def process_SwitchStatement(elt, itr):
    # INFO switch should be a block
    expression = next_elt(itr, "expression")
    res = []
    for statements in get_many(itr, "statements"):
        res += process_elt(statements)
    return process_elt(expression) + res


def process_SwitchCase(elt, itr):
    expression = get_maybe(itr, "expression")
    if expression is not None:
        return process_elt(expression)
    return []


def process_BreakStatement(elt, itr):
    # return [{"type": "break"}]
    return [{"type": "controlFlow", "name": "break"}]


def process_ContinueStatement(elt, itr):
    # return [{"type": "continue"}]
    return [{"type": "controlFlow", "name": "continue"}]


def process_DoStatement(elt, itr):
    expression = next_elt(itr, "expression")
    body = next_elt(itr, "body")
    return process_elt(expression) + [
        {
            "type": "blocks",
            "blocks": [
                {
                    "name": "do while",
                    "guard": get_guard_name(expression),
                    "contents": process_elt(body),
                }
            ],
        }
    ]


def process_ArrayInitializer(elt, itr):
    res = []
    for expressions in get_many(itr, "expressions"):
        res += process_elt(expressions)
    return res


def process_AssertStatement(elt, itr):
    _message = get_maybe(itr, "message")
    _expression = next_elt(itr, "expression")
    # return [{
    #     "type": "assert",
    #     "message": process_elt(message) if message is not None else [],
    #     "contents": process_elt(expression),
    # }]
    return []


def process_TypeAccess(elt, itr):
    qualifier = get_maybe(itr, "qualifier")
    if qualifier is not None:
        return process_elt(qualifier)
    return []


def process_PackageAccess(elt, itr):
    _qualifier = get_maybe(itr, "qualifier")
    return []


def process_LabeledStatement(elt, itr):
    body = next_elt(itr, "body")
    return process_elt(body)


def process_ThisExpression(elt, itr):
    _qualifier = get_maybe(itr, "qualifier")
    return []


def process_TypeDeclarationStatement(elt, itr):
    _declaration = next_elt(itr, "declaration")
    return []
