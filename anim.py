from manim import *
import bf
from collections import namedtuple


def nullable(f):
    return lambda x: None if x is None else f(x)


def sign(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    elif x == 0:
        return 0


class OGroup(Group):
    def set_opacity(self, opacity):
        for mobject in self.submobjects:
            mobject.set_opacity(opacity)

    def become(self, new_group):
        if len(self.submobjects) != len(new_group.submobjects):
            raise IndexError('Cannot become Group with differing length subobjects.')

        for i in range(len(self.submobjects)):
            self.submobjects[i].become(new_group.submobjects[i])


class FinishingAnimation(Animation):
    def __init__(self, *args, on_finish=lambda: None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_finish = on_finish

    def finish(self):
        self.on_finish()
        super().finish()


class Tape(OGroup):
    def __init__(self, data, size=6, scale=1):
        super().__init__()
        self.data = data
        self.size = size
        self.scale = scale
        self.cells = []
        self.__create()

    def __create(self):
        self.__draw_tape()

    def __get_cell(self, offset, data, origin=[0, 0, 0]):
        s = Square(side_length=self.scale)
        s.shift(origin + offset * RIGHT * self.scale)

        t = Text(data or '').scale(self.scale * 0.5)
        t.shift(s.get_center() - t.get_center())

        g = OGroup(s, t)

        if not data:
            g.set_opacity(0)

        return g

    def __draw_cell(self, offset, origin=[0, 0, 0], direction=1):
        g = self.__get_cell(offset, data=self.data[offset], origin=origin)

        self.add(g)

        if direction > 0:
            self.cells.append(g)
        else:
            self.cells.insert(0, g)

    def __draw_tape(self):
        for i in range(self.size):
            self.__draw_cell(i)

    def get_cursor(self, offset):
        tri = Triangle(color='white').scale(0.2).shift(DOWN)
        tri.shift(RIGHT * offset)
        return tri

    def __shift_cell(self, t, reference, cell_data, direction=1):
        if direction > 0:
            t.data.append(cell_data)
            t.__draw_cell(self.size,
                origin=reference + RIGHT*0.5*self.scale)
        else:
            t.data.insert(0, cell_data)
            t.__draw_cell(0,
                origin=reference + LEFT*0.5*self.scale,
                direction=direction)

    def move_shift(self, new_data=[None], direction=1):
        t = self.copy()
        reference = self.cells[0].get_left()

        start = 0 if direction > 0 else len(new_data) - 1
        end = 0 if direction <= 0 else len(new_data)

        for d in range(start, end, sign(direction)):
            self.__shift_cell(t, reference, new_data[d], direction=direction)
            reference += RIGHT * self.scale * sign(direction)

        fa = FinishingAnimation(Mobject(), on_finish=lambda: t.finalize_move(direction))
        a = t.animate.shift(LEFT * self.scale * direction)
        u = Animation(self, remover=True)
        self.set_opacity(0)
        ag = AnimationGroup(a, u, fa)

        return t, ag

    def finalize_move(self, direction=1):
        if direction > 0:
            new_start = len(self.cells) - self.size
            new_end = new_start + self.size
            self.data = self.data[new_start:new_end]
            remove = self.cells[0:new_start]
            self.cells = self.cells[new_start:new_end]
        else:
            new_end = self.size
            self.data = self.data[0:new_end]
            remove = self.cells[new_end:len(self.cells)]
            self.cells = self.cells[0:new_end]

        for r in remove:
            self.remove(r)

        return 1

    def update_morph(self):
        t = self.copy()
        first_cell = self.cells[0]
        for i in range(t.size):
            new = self.__get_cell(i, t.data[i], origin=first_cell.get_center())
            t.cells[i].become(new)
        return t, ReplacementTransform(self, t)


class CursedTape(Group):
    def __init__(self, data, point=0, start=0, size=6, scale=1, convert=None):
        super().__init__()
        self.data = data
        self.start = start
        self.point = point
        self.size = size
        self.convert = nullable(convert or (lambda x: x))
        self.tape = Tape(self.__slice_data(), size=size, scale=scale)
        self.cursor = self.tape.get_cursor(self.point)
        self.add(self.tape, self.cursor)

    def __slice_data(self):
        a = self.data[max(0, self.start):max(0, self.start + self.size)]
        a = [self.convert(x) for x in a]
        nuls = [None for i in range(self.size - len(a))]
        if self.start < 0:
            a = nuls + a
        else:
            a = a + nuls
        return a

    def move_shift(self, direction=1):
        self.start += direction
        if direction > 0:
            start = self.start + self.tape.size - 1
            end = min(start + direction, len(self.data) - 1)
            nuls = [None for i in range(start + direction - (len(self.data) - 1))]
            new_data = self.data[start:end] + nuls
        else:
            end = max(0, self.start)
            start = max(0, self.start + direction)
            print(start, end)
            print(self.start, min(max(0, -self.start), self.size))
            nuls = [None for i in range(min(max(0, -self.start), self.size))]
            new_data = nuls + self.data[start:end]
        new_data = [self.convert(x) for x in new_data]
        self.remove(self.tape)
        new_tape, anim = self.tape.move_shift(new_data=new_data, direction=direction)
        self.tape = new_tape
        return anim

    def update_morph(self):
        self.tape.data = self.__slice_data()
        new_tape, anim = self.tape.update_morph()
        self.tape = new_tape
        return anim


PointerTape = namedtuple('PointerTape', 'tape get_pointer')

program = '>><<<<'

class Machine(Scene):
    def __init__(self, program=program, inp=[]):
        super().__init__()
        self.input = inp
        self.inpptr = 0
        self.output = []
        self.machine = bf.Machine(program)
        self.machine.memory = [0 for i in range(32)]
        self.machine.max_steps = 50
        self.machine.input = self.__input
        self.machine.print = self.__output
        self.run_time = 1

    def __input(self, m):
        x = self.input[self.inpptr] if self.inpptr < len(self.input) else self.machine.EOF
        self.inpptr += 1
        return ord(x)

    def __output(self, m, v):
        self.output.append(chr(v))

    def construct(self):
        run = True

        i = 0
        tpos = UP * 3 + LEFT * 6
        fc = Text(str(i)).shift(tpos)

        tapes = [
            PointerTape(CursedTape(self.machine.memory,
                point=2, size=5, start=-2,
                convert=lambda x: f'{x:02x}').shift(UP * 3),
                lambda: self.machine.memptr),
            PointerTape(CursedTape(self.machine.program,
                point=2, size=5, start=-2,
                convert=lambda x: x).shift(UP * 1.5),
                lambda: min(self.machine.progptr, len(self.machine.program) - 1)),
            #PointerTape(CursedTape(self.output,
            #    point=2, size=5, start=-2,
            #    convert=lambda x: x),
            #    lambda: self.outptr),
            #PointerTape(CursedTape(self.input,
            #   point=2, size=5, start=-2,
            #    convert=lambda x: x).shift(DOWN * 2),
            #    lambda: self.inpptr)
        ]

        for t in tapes:
            self.add(t.tape)

        while run:
            run = self.machine.step()
            anims = []
            i += 1
            anims.append(fc.animate.become(Text(str(i)).shift(tpos)))
            for t in tapes:
                new_start = t.get_pointer() - t.tape.point
                direction = new_start - t.tape.start
                if direction:
                    anims.append(t.tape.move_shift(direction=direction))
                else:
                    anims.append(t.tape.update_morph())
                    #pass
            if anims:
                self.play(*anims, run_time=self.run_time)
            else:
                self.wait(self.run_time)

