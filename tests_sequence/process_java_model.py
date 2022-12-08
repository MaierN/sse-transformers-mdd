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


def generate_sequence(example):
    generate_sequence.problem = False

    xmi = example["xmi"]

    generate_sequence.root = ET.fromstring(xmi)

    body_declaration = generate_sequence.root.find(
        "."
        # "/ownedElements[@name='targetpackage']"
        "/ownedElements"
        f"/ownedElements[@{NS_XSI}type='java:ClassDeclaration']"
        f"/bodyDeclarations[@{NS_XSI}type='java:MethodDeclaration']"
    )
    body = body_declaration.find("body")
    for _parameters in body_declaration.findall("parameters"):
        pass  # TODO add to scope

    res = process_elt(body)

    return res


generate_sequence.root = None
generate_sequence.problem = False


def find_element_by_model_path(path):
    if not path.startswith("//"):
        print("weird path", path)
    path = path[2:]

    curr_elt = generate_sequence.root

    for part in path.split("/"):
        if not path.startswith("@"):
            print("weird part", path)
        part = part[1:]
        part = part.split(".")
        elt_tag = part[0]
        elt_idx = int(part[1]) if len(part) > 1 else 0

        curr_elt = curr_elt.findall(elt_tag)[elt_idx]

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
        printi(f"### PROBLEM (extra child in {elt_type}):", child.tag, child.items())
        generate_sequence.problem = True

    return res


def assert_elt(elt, elt_tag):
    if elt.tag != elt_tag:
        printi(f"### PROBLEM assert_elt {elt_tag}:", elt.tag, elt.items())
        generate_sequence.problem = True


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
        to = [find_element_by_model_path(elt.get("variable")).get("name")]
    elif elt_type in [
        "java:MethodInvocation",
        "java:ClassInstanceCreation",
        "java:StringLiteral",
        "java:ArrayAccess",
        "java:InfixExpression",
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
        if field is not None:
            to += [find_element_by_model_path(field.get("variable")).get("name")]
    elif elt_type == "java:TypeAccess":
        to = [find_element_by_model_path(elt.get("type")).get("name")]
    elif elt_type == "java:ParenthesizedExpression":
        return get_to_path(elt.find("expression"))
    elif elt_type == "java:CastExpression":
        return get_to_path(elt.find("expression"))
    else:
        print("### PROBLEM get_to_path:", elt, elt.items())
        generate_sequence.problem = True
        return None

    child_to = []
    children = elt.findall("*")
    if len(children) > 0:
        child = children[-1]
        child_to = get_to_path(child)
        if child_to is None:
            return None

    return child_to + to


def process_not_implemented(elt, itr):
    printi("### process_not_implemented:", elt.tag, elt.get(f"{NS_XSI}type"))
    generate_sequence.problem = True
    for _child in itr:
        pass
    return [
        {
            "type": "not_implemented",
            "elt_tag": elt.tag,
            "elt_type": elt.get(f"{NS_XSI}type"),
        }
    ]


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
    _param = next_elt(itr, "parameter")
    # TODO param add new variable to scope

    return process_elt(expression) + [
        {
            "type": "enhancedFor",
            "contents": process_elt(body),
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

    return res + [
        {
            "type": "methodInvocation",
            "to": to if to is not None else "### unk",
            "method": find_element_by_model_path(elt.get("method")).get("name"),
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

    return res + [
        {
            "type": "superMethodInvocation",
            "to": to if to is not None else "### unk",
            "method": find_element_by_model_path(elt.get("method")).get("name"),
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
            "type": "superConstructorInvocation",
            "to": to if to is not None else "### unk",
        }
    ]


def process_IfStatement(elt, itr):
    expression = next_elt(itr, "expression")
    then_block = next_elt(itr, "thenStatement")
    else_block = get_maybe(itr, "elseStatement")

    return process_elt(expression) + [
        {
            "type": "ifStatement",
            "contents_then": process_elt(then_block),
            "contents_else": process_elt(else_block) if else_block else [],
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
    return contents + ["return"]


def process_Assignment(elt, itr):
    _left_hand_side = next_elt(itr, "leftHandSide")
    right_hand_side = next_elt(itr, "rightHandSide")
    # TODO left_hand_side add new variable to scope
    return process_elt(right_hand_side)


def process_ClassInstanceCreation(elt, itr):
    res = []
    for arguments in get_many(itr, "arguments"):
        res += process_elt(arguments)

    _anonymous_class_decl = get_maybe(itr, "anonymousClassDeclaration")
    expression = get_maybe(itr, "expression")
    if expression is not None:
        res += process_elt(expression)
    _instance_type = next_elt(itr, "type")

    method = find_element_by_model_path(elt.get("method"))

    return res + [
        {"type": "newInstance", "constructor": method.get("name")}
    ]  # TODO add to info


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
    _variable_type = next_elt(itr, "type")
    for fragments in get_many(itr, "fragments"):
        fragments = filter_iter(fragments)
        initializer = get_maybe(fragments, "initializer")
        if initializer is not None:
            res += process_elt(initializer)
    _modifier = next_elt(itr, "modifier")
    for _annotations in get_many(itr, "annotations"):
        pass
    # TODO add new variable to scope
    return res


def process_PrefixExpression(elt, itr):
    operand = next_elt(itr, "operand")
    return process_elt(operand)


def process_ConditionalExpression(elt, itr):
    else_expr = next_elt(itr, "elseExpression")
    cond_expr = next_elt(itr, "expression")
    then_expr = next_elt(itr, "thenExpression")
    return process_elt(cond_expr) + [
        {
            "type": "ifExpression",
            "contents_then": process_elt(then_expr),
            "contents_else": process_elt(else_expr),
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
            "type": "synchronized",
            "contents": process_elt(body),
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
        _exception = next_elt(catch_clauses, "exception")
        catch_body = next_elt(catch_clauses, "body")
        catch_res.append(process_elt(catch_body))
    return [
        {
            "type": "try",
            "contents_try": process_elt(body),
            "contents_catch": catch_res,
            "contents_finally": process_elt(finally_clause) if finally_clause else [],
        }
    ]


def process_TypeLiteral(elt, itr):
    _type = next_elt(itr, "type")
    return []


def process_ThrowStatement(elt, itr):
    expression = next_elt(itr, "expression")
    return process_elt(expression) + [{"type": "throw"}]


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
            "type": "whileStatement",
            "contents": process_elt(body),
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
    # TODO add new variables to scope
    return res_initializers + [
        {
            "type": "forStatement",
            "contents_cond": process_elt(cond_expr) if cond_expr is not None else [],
            "contents_updater": res_updaters,
            "contents": process_elt(body),
        }
    ]


def process_PostfixExpression(elt, itr):
    operand = next_elt(itr, "operand")
    return process_elt(operand)


def process_VariableDeclarationExpression(elt, itr):
    res = []
    _variable_type = next_elt(itr, "type")
    for fragments in get_many(itr, "fragments"):
        fragments = filter_iter(fragments)
        initializer = get_maybe(fragments, "initializer")
        if initializer is not None:
            res += process_elt(initializer)
    _modifier = next_elt(itr, "modifier")
    for _annotations in get_many(itr, "annotations"):
        pass
    # TODO add new variable to scope
    return res


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
    # TODO switch should be a block
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
    return [{"type": "break"}]


def process_ContinueStatement(elt, itr):
    return [{"type": "continue"}]


def process_DoStatement(elt, itr):
    expression = next_elt(itr, "expression")
    body = next_elt(itr, "body")
    return process_elt(expression) + [
        {
            "type": "doStatement",
            "contents": process_elt(body),
        }
    ]


def process_ArrayInitializer(elt, itr):
    res = []
    for expressions in get_many(itr, "expressions"):
        res += process_elt(expressions)
    return res


def process_AssertStatement(elt, itr):
    message = get_maybe(itr, "message")
    expression = next_elt(itr, "expression")
    return {
        "type": "assert",
        "message": process_elt(message) if message is not None else [],
        "contents": process_elt(expression),
    }


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
