import math


NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"


class ModelParser:
    def __init__(self, node):
        self._node = node
        self._expectedChildren = []
        self._child_results = []

    def parse(self):
        if not self.canParse(self._node):
            raise Exception("Cannot parse node")

        curr_expected_child_idx = 0
        curr_child_count = 0
        for child in self._node:
            expectedChild = self._expectedChildren[curr_expected_child_idx]
            while not expectedChild["name"] != child.tag or not expectedChild[
                "type"
            ].canParse(child):
                if curr_child_count >= expectedChild["min"]:
                    curr_expected_child_idx += 1
                    curr_child_count = 0
                    expectedChild = self._expectedChildren[curr_expected_child_idx]
                else:
                    raise Exception("Unexpected child")
            curr_child_count += 1
            foundChild = expectedChild["type"](child)
            foundChild.parse()
            self._child_results.append(
                {"idx": curr_expected_child_idx, "result": foundChild.getContents()}
            )

        while curr_expected_child_idx < len(self._expectedChildren):
            expectedChild = self._expectedChildren[curr_expected_child_idx]
            if curr_child_count < expectedChild["min"]:
                raise Exception("Missing child")
            curr_expected_child_idx += 1

    def getContents(self):
        raise NotImplementedError

    @classmethod
    def canParse(cls, _node):
        raise NotImplementedError


class Block(ModelParser):
    def __init__(self, node):
        super().__init__(node)

        self._expectedChildren = [
            {
                "type": ReturnStatement,
                "name": "statements",
                "min": 0,
                "max": math.inf,
            }
        ]

    def getContents(self):
        return (
            "<block>"
            + "".join([child["result"] for child in self._child_results])
            + "</block>"
        )

    @classmethod
    def canParse(cls, node):
        return node.get(f"{NS_XSI}type") == "java:Block"


class MethodInvocation(ModelParser):
    def __init__(self, node):
        super().__init__(node)

        self._expectedChildren = [
            {
                "type": MethodInvocation,
                "name": "expression",
                "min": 0,
                "max": 1,
            }
        ]

    def getContents(self):
        return (
            "<method invocation>"
            + "".join([child["result"] for child in self._child_results])
            + "</method invocation>"
        )

    @classmethod
    def canParse(cls, node):
        return node.get(f"{NS_XSI}type") == "java:MethodInvocation"


class ReturnStatement(ModelParser):
    def __init__(self, node):
        super().__init__(node)

        self._expectedChildren = [
            {
                "type": MethodInvocation,
                "name": "expression",
                "min": 1,
                "max": 1,
            }
        ]

    def getContents(self):
        return (
            "<tatements return statement>"
            + "".join([child["result"] for child in self._child_results])
            + "</tatements return statement>"
        )

    @classmethod
    def canParse(cls, node):
        return node.get(f"{NS_XSI}type") == "java:ReturnStatement"


class AnyStatement(ModelParser):
    def __init__(self, node):
        super().__init__(node)

        self._expectedChildren = [
            {
                
            }
        ]
