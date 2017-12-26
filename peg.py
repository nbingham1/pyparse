import parse
from parse import Term, Token, Or, Seq, Rep, Ignore

class Label:
	def __init__(self):
		pass

	def __str__(self):
		return "label"

	def __repr__(self):
		return "label"

	def parse(self, tokens):
		i = 0
		while i < len(tokens) and tokens[i] not in "\"\'*+?|();->: \t\n\r":
			i += 1

		if i > 0:
			return ([tokens[0:i]], parse.Status(i))
		else:
			return ([], parse.Status(0, ["Error parsing label"]))

class Syntax:
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return "\"" + str(self.value) + "\""

	def __repr__(self):
		return "\"" + str(self.value) + "\""

	def parse(self, tokens):
		i = 0
		while i < len(tokens) and i < len(self.value) and tokens[i] == self.value[i]:
			i += 1

		if i == len(self.value):
			return ([tokens[0:i]], parse.Status(i))
		else:
			return ([], parse.Status(0, ["Error parsing syntax \"" + str(self) + "\""]))

class Text:
	def __init__(self):
		pass

	def __str__(self):
		return "text"

	def __repr__(self):
		return "text"

	def parse(self, tokens):
		if tokens[0] not in "\'\"":
			return ([], parse.Status(0, ["Error parsing text"]))

		i = 1
		while i < len(tokens) and tokens[i] != tokens[0]:
			i += 1

		if i >= len(tokens):
			return ([], parse.Status(0, ["Error parsing text"]))
		else:
			return ([tokens[0:i+1]], parse.Status(i+1))

class Space:
	def __init__(self):
		pass

	def __str__(self):
		return "space"

	def __repr__(self):
		return "space"

	def parse(self, tokens):
		i = 0
		while i < len(tokens) and tokens[i] in " \t\n\r":
			i += 1

		return ([], parse.Status(i))

class Grammar(parse.Grammar):
	def __init__(self):
		parse.Grammar.__init__(self)
		self.terms["root"] = Seq(Rep(Seq(Space(), Term(self, "rule")), 1), Space(), Token(None))
		self.terms["rule"] = Seq(
			Label(),
			Rep(Seq(
				Syntax(":"),
				Rep(Label(), 0, 1)
			), 0, 1), Space(),
			Syntax("->"), Space(),
			Term(self, "or"), Space(),
			Ignore(Syntax(";"))
		)
		self.terms["seq"]  = Seq(
			Or(Term(self, "rep"), Term(self, "term")),
			Rep(Seq(
				Space(),
				Or(Term(self, "rep"), Term(self, "term"))
			))
		)
		self.terms["or"]   = Seq(
			Term(self, "seq"),
			Rep(Seq(Space(), Ignore(Syntax("|")), Space(), Term(self, "seq")))
		)
		self.terms["rep"]  = Seq(
			Term(self, "term"),
			Or(Syntax("*"), Syntax("+"), Syntax("?"))
		)
		self.terms["term"] = Or(
			Seq(Ignore(Syntax("(")), Space(), Term(self, "or"), Space(), Ignore(Syntax(")"))),
			Label(),
			Text()
		)

	def loadExpr(self, grammar, expr):
		if isinstance(expr, tuple):
			if expr[1] == "or":
				if len(expr[0]) > 1:
					return Or(*[self.loadExpr(grammar, term) for term in expr[0]])
				elif len(expr[0]) > 0:
					return self.loadExpr(grammar, expr[0][0])
			elif expr[1] == "seq":
				if len(expr[0]) > 1:
					return Seq(*[self.loadExpr(grammar, term) for term in expr[0]])
				elif len(expr[0]) > 0:
					return self.loadExpr(grammar, expr[0][0])
			elif expr[1] == "rep":
				if expr[0][1] == "*":
					return Rep(self.loadExpr(grammar, expr[0][0]))
				elif expr[0][1] == "+":
					return Rep(self.loadExpr(grammar, expr[0][0]), 1)
				elif expr[0][1] == "?":
					return Rep(self.loadExpr(grammar, expr[0][0]), 0, 1)
			elif expr[1] == "term":
				return self.loadExpr(grammar, expr[0][0])
			else:
				print "Error: unrecognized syntax \"" + str(expr) + "\""
				return None
		elif expr[0] in "\"\'" and expr[-1] == expr[0]:
			return Syntax(expr[1:-1])
		else:
			return Term(grammar, expr)

	def load(self, text):
		gram, stat = self.parse(text)
		if len(stat.msgs) > 0:
			print stat
			return

		rules = gram[0][0]
		result = parse.Grammar()
		for rule in rules:
			key = rule[0][0]
			if rule[0][1] == ":":
				if rule[0][2] == "->":
					expr = self.loadExpr(result, rule[0][3])
					result.terms[key] = (expr, "")
				else:
					name = rule[0][2]
					expr = self.loadExpr(result, rule[0][4])
					result.terms[key] = (expr, name)
			else:
				expr = self.loadExpr(result, rule[0][2])
				result.terms[key] = expr
		return result

