
from datetime import date, datetime, timedelta


PRIORITY_RANK = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


def build_daily_plan(
    tasks: list[dict],
    calendar: list[dict],
    preferences: dict,
    plan_date: str,
    available_minutes: int | None = None,
) -> dict:
    """Build a daily schedule without overlapping calendar events."""

    day = date.fromisoformat(plan_date)

    work_start = datetime.combine(
        day,
        datetime.strptime(
            preferences["working_hours_start"], "%H:%M"
        ).time(),
    )
    work_end = datetime.combine(
        day,
        datetime.strptime(
            preferences["working_hours_end"], "%H:%M"
        ).time(),
    )

    focus_minutes = int(preferences["preferred_focus_minutes"])
    break_minutes = int(preferences["break_minutes"])

    if work_end <= work_start:
        raise ValueError("Working hours must end after they start.")

    if focus_minutes < 1 or break_minutes < 0:
        raise ValueError(
            "Focus must be positive and break cannot be negative."
        )

    if available_minutes is not None and available_minutes < 1:
        raise ValueError("Available minutes must be positive.")

    # For today, never schedule work in the past.
    # For other dates, preserve the normal working hours.
    planning_start = work_start
    now = datetime.now()

    if day == now.date():
        current_minute = now.replace(second=0, microsecond=0)

        if now.second > 0 or now.microsecond > 0:
            current_minute += timedelta(minutes=1)

        planning_start = max(work_start, current_minute)

    # Keep only calendar events overlapping the planning window.
    busy = []

    for event in calendar:
        start = datetime.fromisoformat(event["start"])
        end = datetime.fromisoformat(event["end"])

        if end <= start:
            raise ValueError(f"Invalid calendar event: {event['id']}")

        start = max(start, planning_start)
        end = min(end, work_end)

        if start < end:
            busy.append((start, end, event["title"]))

    busy.sort(key=lambda item: item[0])

    # Merge overlapping calendar events.
    merged = []

    for start, end, title in busy:
        if merged and start < merged[-1][1]:
            old_start, old_end, old_title = merged[-1]
            merged[-1] = (
                old_start,
                max(old_end, end),
                f"{old_title} / {title}",
            )
        else:
            merged.append((start, end, title))

    # Find free intervals between calendar events.
    free_intervals = []
    cursor = planning_start

    for start, end, _ in merged:
        if cursor < start:
            free_intervals.append((cursor, start))

        cursor = max(cursor, end)

    if cursor < work_end:
        free_intervals.append((cursor, work_end))

    # Keep only pending tasks.
    pending = [
        task
        for task in tasks
        if task.get("status", "pending") == "pending"
    ]

    def sort_key(task: dict) -> tuple:
        due = task.get("due_date")
        overdue = bool(due and due < plan_date)

        return (
            0 if overdue else 1,
            PRIORITY_RANK.get(task.get("priority", "medium"), 1),
            due or "9999-12-31",
            task["id"],
        )

    pending.sort(key=sort_key)

    scheduled = []
    unscheduled = []
    total_scheduled = 0

    # Each slot is mutable so allocated time cannot be reused.
    slots = [[start, end] for start, end in free_intervals]

    # Optional limit: schedule only within this time window.
    # Breaks also occupy time within the window.
    if available_minutes is not None:
        deadline = planning_start + timedelta(minutes=available_minutes)
        limited_slots = []

        for start, end in slots:
            if start >= deadline:
                continue

            limited_slots.append((start, min(end, deadline)))

        slots = [
            [start, end]
            for start, end in limited_slots
            if start < end
        ]

    for task in pending:
        remaining = int(task["duration_minutes"])

        if remaining <= 0:
            unscheduled.append({
                "task_id": task["id"],
                "title": task["title"],
                "minutes_remaining": remaining,
                "reason": "Task duration must be positive.",
            })
            continue

        for slot in slots:
            while remaining > 0:
                cursor, interval_end = slot

                available = int(
                    (interval_end - cursor).total_seconds() // 60
                )

                if available <= 0:
                    break

                session_length = min(
                    focus_minutes,
                    remaining,
                    available,
                )

                session_end = cursor + timedelta(
                    minutes=session_length
                )

                scheduled.append({
                    "task_id": task["id"],
                    "title": task["title"],
                    "start": cursor.isoformat(timespec="minutes"),
                    "end": session_end.isoformat(timespec="minutes"),
                    "duration_minutes": session_length,
                    "priority": task.get("priority", "medium"),
                    "due_date": task.get("due_date"),
                    "overdue": bool(
                        task.get("due_date")
                        and task["due_date"] < plan_date
                    ),
                })

                remaining -= session_length
                total_scheduled += session_length
                cursor = session_end

                # Add a break only when more work remains and it fits.
                if remaining > 0 and break_minutes > 0:
                    break_end = cursor + timedelta(
                        minutes=break_minutes
                    )

                    if break_end <= interval_end:
                        scheduled.append({
                            "task_id": None,
                            "title": "Break",
                            "start": cursor.isoformat(timespec="minutes"),
                            "end": break_end.isoformat(timespec="minutes"),
                            "duration_minutes": break_minutes,
                            "type": "break",
                        })
                        cursor = break_end
                    else:
                        cursor = interval_end

                # Save the updated cursor to prevent double allocation.
                slot[0] = cursor

        if remaining > 0:
            unscheduled.append({
                "task_id": task["id"],
                "title": task["title"],
                "minutes_remaining": remaining,
                "reason": "Not enough available time today.",
            })

    scheduled.sort(key=lambda item: item["start"])

    return {
        "plan_date": plan_date,
        "working_hours": {
            "start": work_start.isoformat(timespec="minutes"),
            "end": work_end.isoformat(timespec="minutes"),
        },
        "scheduled": scheduled,
        "unscheduled": unscheduled,
        "summary": {
            "pending_tasks": len(pending),
            "fully_scheduled_tasks": len(pending) - len(unscheduled),
            "unscheduled_tasks": len(unscheduled),
            "task_minutes_scheduled": total_scheduled,
        },
    }
