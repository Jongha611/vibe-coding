class Gugudan:

    MIN_DAN = 1
    MAX_DAN = 9

    def line(self, dan, times):

        return f"{dan} x {times} = {dan * times}"

    def table(self, dan):

        if not self.MIN_DAN <= dan <= self.MAX_DAN:
            raise ValueError(f"단은 {self.MIN_DAN}~{self.MAX_DAN} 사이여야 한다: {dan}")

        return [self.line(dan, times) for times in range(1, 10)]

    def tables(self, start, end):

        if start > end:
            raise ValueError(f"시작 단이 끝 단보다 클 수 없다: {start} > {end}")

        return [self.table(dan) for dan in range(start, end + 1)]

    def run(self):

        try:
            start = int(input("시작 단: "))
            end = int(input("끝 단: "))
            tables = self.tables(start, end)
        except ValueError as error:
            print(f"입력 오류: {error}")
            return

        for table in tables:
            print("\n".join(table))
            print()
