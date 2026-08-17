import csv
import io


def generate_tasks_csv(tasks: list[dict]) -> io.BytesIO:
    string_buf = io.StringIO()
    writer = csv.writer(string_buf)

    writer.writerow(
        [
            "ID",
            "Название",
            "Описание",
            "Автор",
            "Исполнитель",
            "Статус",
            "Приоритет",
            "Срок",
            "Создано",
            "Завершено",
            "Закрыл",
        ]
    )

    for t in tasks:
        writer.writerow(
            [
                t["id"],
                t["title"],
                t.get("description", ""),
                t.get("username", ""),
                t.get("assigned_to_name", "") or "—",
                t.get("status", ""),
                t.get("priority", ""),
                t.get("planned_end_date", "") or "—",
                t.get("created_at", ""),
                t.get("completed_at", "") or "—",
                t.get("closed_by_name", "") or "—",
            ]
        )

    encoded = string_buf.getvalue().encode("utf-8-sig")
    output = io.BytesIO(encoded)
    output.seek(0)
    return output
