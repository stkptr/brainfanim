hello_world = '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.'

class Machine:
    EOF = 0

    def __init__(self, program='', max_steps=0):
        self.input = lambda x: max(0, ord(input()[0])) % 256
        self.print = lambda x, y: print(chr(y), end='')
        self.exit = lambda x: None
        self.program = list(program)
        self.memory = []
        self.steps = 0
        self.max_steps = max_steps
        self.reset()

    @property
    def instruction(self):
        if self.progptr < len(self.program):
            return self.program[self.progptr]

    @property
    def cell(self):
        return self.memget(self.memptr)

    def reset(self):
        self.maxmemsize = 0
        self.memptr = 0
        self.memory = [0 for x in self.memory]
        self.progptr = 0

    def __memexpand(self, minpos):
        minpos += 1
        if len(self.memory) > minpos:
            return

        new = min(minpos, self.maxmemsize) if self.maxmemsize else minpos
        self.memory += [0 for i in range(new - len(self.memory))]

    def memget(self, pos):
        self.__memexpand(pos)
        return self.memory[pos]

    def memset(self, pos, value):
        self.__memexpand(pos)
        self.memory[pos] = value

    def __add(self):
        self.memset(self.memptr, (self.memget(self.memptr) + 1) % 256)

    def __sub(self):
        self.memset(self.memptr, (self.memget(self.memptr) - 1) % 256)

    def __right(self):
        self.memptr += 1

    def __left(self):
        self.memptr = max(0, self.memptr - 1)

    def __print(self):
        self.print(self, self.memget(self.memptr))

    def __input(self):
        self.memset(self.memptr, self.input(self))

    def __skip(self, pluschar, minuschar, direction):
        bracket = 1
        while bracket:
            self.progptr += direction
            op = self.program[self.progptr]
            if op == pluschar:
                bracket += 1
            elif op == minuschar:
                bracket -= 1

    def __while(self):
        if not self.memget(self.memptr):
            self.__skip('[', ']', 1)

    def __end(self):
        self.__skip(']', '[', -1)
        self.progptr -= 1

    def step(self):
        opcodes = {
            '+': self.__add,
            '-': self.__sub,
            '>': self.__right,
            '<': self.__left,
            '.': self.__print,
            ',': self.__input,
            '[': self.__while,
            ']': self.__end,
        }

        if (self.progptr >= len(self.program) or
            self.steps > self.max_steps):
            self.exit(self)
            return False

        opcodes[self.instruction]()
        self.progptr += 1
        self.steps += 1
        return True

    def run(self):
        run = True
        while run:
            run = self.step()
