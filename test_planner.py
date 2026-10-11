
from app.planner.engine import build_daily_plan
from app.tools.storage import load_data


def main():
    data = load_data()

    plan = build_daily_plan(
        tasks=data["tasks"],
        calendar=data["calendar"],
        preferences=data["preferences"],
        plan_date="2026-10-12",
    )

    print("\nDAYPILOT DAILY PLAN")
    print("=" * 40)
    print("Date:", plan["plan_date"])

    for item in plan["scheduled"]:
        print(
            f'{item["start"][11:]} - {item["end"][11:]}'
            f' | {item["title"]}'
            f' ({item["duration_minutes"]} min)'
        )

    if plan["unscheduled"]:
        print("\nUNSCHEDULED TASKS")
        for task in plan["unscheduled"]:
            print(
                f'- {task["title"]}: '
                f'{task["minutes_remaining"]} minutes left'
            )

    print("\nSUMMARY")
    print(plan["summary"])


if __name__ == "__main__":
    main()
