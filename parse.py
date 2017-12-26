

class Status:
	def __init__(self, count, msgs = None):
		if msgs:
			self.msgs = msgs
		else:
			self.msgs = []

		self.count = count

	def __str__(self):
		result = ""
		for msg in self.msgs:
			result += str(msg) + "\n\n"
		return result

	def __repr__(self):
		return str(self)

class Grammar:
	def __init__(self, terms=None):
		if terms:
			self.terms = terms
		else:
			self.terms = {}

	def __str__(self):
		result = ""
		for key, term in self.terms.items():
			if isinstance(term, tuple):
				result += str(key) + ":" + str(term[1]) + " -> " + str(term[0]) + ";\n"
			else:
				result += str(key) + " -> " + str(term) + ";\n"

		return result

	def __repr__(self):
		return str(self)

	def parse(self, tokens, term = "root"):
		if term in self.terms:
			gram = self.terms[term]
			if isinstance(gram, tuple):
				parser = gram[0]
				label = gram[1]
			else:
				parser = gram
				label = term

			result, stat = parser.parse(tokens)

			if len(stat.msgs) > 0:
				stat.msgs.append("Error parsing \"" + str(parser) + "\"")

			if label:
				return ([(result, label)], stat)
			else:
				return (result, stat)
		else:
			return ([], Status(0, ["Term \"" + str(term) + "\" not defined in grammar"]))

class Term:
	def __init__(self, grammar, name):
		self.grammar = grammar
		self.name = name

	def __str__(self):
		return str(self.name)

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		result, stat = self.grammar.parse(tokens, self.name)
		if len(stat.msgs) > 0:
			stat.msgs.append("Error parsing term \"" + str(self) + "\"")
		return (result, stat)

class Token:
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return str(self.value)

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		if not self.value and len(tokens) == 0:
			return ([], Status(0))
		elif tokens[0] == self.value:
			return ([tokens[0]], Status(1))
		else:
			return ([], Status(0, ["Expected token \"" + str(self) + "\" but found \"" + str(tokens[0]) + "\""]))

class Or:
	def __init__(self, *args):
		self.terms = args

	def __str__(self):
		result = ""
		for term in self.terms:
			if result:
				result += " | "
			result += str(term)
		return "(" + result + ")"

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		result = []
		stat = Status(-1)

		for term in self.terms:
			subresult, substat = term.parse(tokens)
			if len(substat.msgs) == 0:
				return subresult, substat
			elif substat.count > stat.count:
				result = subresult
				stat = substat

		stat.msgs.append("Error parsing or \"" + str(self) + "\"")
		return (result, stat)

class Seq:
	def __init__(self, *args):
		self.terms = args

	def __str__(self):
		result = ""
		for term in self.terms:
			if result:
				result += " "
			result += str(term)
		return "(" + result + ")"

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		result = []
		stat = Status(0)

		for term in self.terms:
			subresult, substat = term.parse(tokens[stat.count:])
			result.extend(subresult)
			stat.count += substat.count
			stat.msgs.extend(substat.msgs)

			if len(stat.msgs) > 0:
				stat.msgs.append("Error parsing sequence \"" + str(self) + "\"")
				return (result, stat)
		
		return (result, stat)

class Rep:
	def __init__(self, term, lo = 0, hi = -1):
		self.term = term
		self.lo = lo
		self.hi = hi

	def __str__(self):
		if self.lo == 0 and self.hi < self.lo:
			return str(self.term) + "*"
		elif self.lo == 1 and self.hi < self.lo:
			return str(self.term) + "+"
		elif self.lo == 0 and self.hi == 1:
			return str(self.term) + "?"
		else:
			return str(self.term) + "{" + str(self.lo) + " " + str(self.hi) + "}"

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		result = []
		stat = Status(0)

		i = 0
		while i < self.lo:
			subresult, substat = self.term.parse(tokens[stat.count:])
			result.extend(subresult)
			stat.count += substat.count
			stat.msgs.extend(substat.msgs)

			if len(stat.msgs) > 0:
				stat.msgs.append("Error parsing repetition \"" + str(self) + "\"")
				return (result, stat)
			i += 1
		
		while self.hi < self.lo or i < self.hi:
			subresult, substat = self.term.parse(tokens[stat.count:])
			if len(substat.msgs) == 0:
				result.extend(subresult)
				stat.count += substat.count
				stat.msgs.extend(substat.msgs)
				i += 1
			else:
				return (result, stat)

		return (result, stat)

class Ignore:
	def __init__(self, term):
		self.term = term

	def __str__(self):
		return "-" + str(self.term) + "-"

	def __repr__(self):
		return str(self)

	def parse(self, tokens):
		result, stat = self.term.parse(tokens)
		return ([], stat)


