import subprocess
from collections import Counter
from datetime import datetime


class GitStats:

    WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
    LOG_FORMAT = "%H|%an|%ae|%aI"

    def month_start(self, now=None):

        now = now or datetime.now()

        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def collect(self):

        since = self.month_start().strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", f"--pretty=format:{self.LOG_FORMAT}", f"--since={since}"],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def parse(self, log_text):

        commits = []

        for line in log_text.splitlines():
            parts = line.split("|")
            if len(parts) != 4:
                continue

            commit_hash, author, email, date = parts
            commits.append({
                "hash": commit_hash,
                "author": author,
                "email": email,
                "date": datetime.fromisoformat(date),
            })

        return commits

    def _author_key(self, commit):
        """집계 키. 이메일은 대소문자를 무시하고, 비어 있으면 이름으로 폴백한다."""

        return commit["email"].strip().lower() or commit["author"]

    def by_author(self, commits):

        counts = Counter(self._author_key(commit) for commit in commits)

        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def author_names(self, commits):
        """집계 키마다 출력에 쓸 대표 이름. git log 가 최신순이라 가장 최근 이름이 남는다."""

        names = {}

        for commit in commits:
            names.setdefault(self._author_key(commit), commit["author"])

        return names

    def by_weekday(self, commits):

        counts = Counter(self.WEEKDAYS[commit["date"].weekday()] for commit in commits)

        return {day: counts.get(day, 0) for day in self.WEEKDAYS}

    def run(self):

        start = self.month_start()
        commits = self.parse(self.collect())

        print(f"{start.year}년 {start.month}월 커밋 통계")

        if not commits:
            print("아직 커밋이 없다.")
            return

        print(f"총 커밋: {len(commits)}\n")

        names = self.author_names(commits)

        print("작성자별")
        for email, count in self.by_author(commits).items():
            print(f"  {names[email]}: {count}")

        print("\n요일별")
        for day, count in self.by_weekday(commits).items():
            print(f"  {day}: {count}")
