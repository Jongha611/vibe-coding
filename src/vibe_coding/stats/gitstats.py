import subprocess
from collections import Counter
from datetime import datetime


class GitStats:

    WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
    LOG_FORMAT = "%H|%an|%aI"

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
            if len(parts) != 3:
                continue

            commit_hash, author, date = parts
            commits.append({
                "hash": commit_hash,
                "author": author,
                "date": datetime.fromisoformat(date),
            })

        return commits

    def by_author(self, commits):

        counts = Counter(commit["author"] for commit in commits)

        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

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

        print("작성자별")
        for author, count in self.by_author(commits).items():
            print(f"  {author}: {count}")

        print("\n요일별")
        for day, count in self.by_weekday(commits).items():
            print(f"  {day}: {count}")
