"""Finite, allowlisted arithmetic for explicit source-bound formula proposals.

No eval, imports, attributes, calls, variables or generated execution. General
formula OCR and dimensional reasoning are deliberately unsupported here.
"""
import ast
from decimal import Decimal, localcontext, InvalidOperation
import hashlib
import re

def evaluate_formula(expression: str, *, source_sha256: str, locator: str):
    if not isinstance(expression,str) or len(expression)>256 or not re.fullmatch(r'[0-9eE+*/().\-\s]+',expression):
        raise ValueError('Unsupported formula grammar')
    if not re.fullmatch(r'[a-f0-9]{64}',source_sha256) or not isinstance(locator,str) or not 1<=len(locator)<=200:
        raise ValueError('Formula requires source provenance')
    tree=ast.parse(expression,mode='eval')
    if len(list(ast.walk(tree)))>64:
        raise ValueError('Formula complexity budget exceeded')
    def number(node,depth=0):
        if depth>12:
            raise ValueError('Formula depth exceeded')
        if isinstance(node,ast.Constant) and type(node.value) in {int,float}:
            value=Decimal(ast.get_source_segment(expression,node))
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            value=number(node.operand,depth+1)*(1 if isinstance(node.op,ast.UAdd) else -1)
        elif isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            left,right=number(node.left,depth+1),number(node.right,depth+1)
            if isinstance(node.op,ast.Add): value=left+right
            elif isinstance(node.op,ast.Sub): value=left-right
            elif isinstance(node.op,ast.Mult): value=left*right
            elif not right: raise ValueError('Division by zero')
            else: value=left/right
        else:
            raise ValueError('Unsupported formula expression')
        if not value.is_finite() or (value and abs(value.adjusted())>100):
            raise ValueError('Formula exceeds finite magnitude budget')
        return value
    try:
        with localcontext() as context:
            context.prec=28
            result=number(tree.body)
    except (InvalidOperation,OverflowError) as error:
        raise ValueError('Invalid finite arithmetic') from error
    return dict(expression=expression,value=str(result),source_sha256=source_sha256,locator=locator,
        expression_sha256=hashlib.sha256(expression.encode()).hexdigest(),precision=28,
        status='unverified_formula_proposal',units='dimensionless',generated_execution=False)
