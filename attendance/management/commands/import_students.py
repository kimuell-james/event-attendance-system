import csv
from django.core.management.base import BaseCommand
from attendance.models import Student


class Command(BaseCommand):
    help = "Import students from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="D:\Documents\Python Files\event_attendance_system\students_data.csv")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert blank RFID to None
                rfid_value = row["rfid"].strip() if row["rfid"] else None
                if rfid_value == "":
                    rfid_value = None

                try:
                    Student.objects.create(
                        first_name=row["first_name"].strip(),
                        last_name=row["last_name"].strip(),
                        course=row["course"].strip(),
                        year=int(row["year"]),
                        rfid=int(rfid_value) if rfid_value else None,
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error inserting {row['first_name']} {row['last_name']}: {e}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Inserted {row['first_name']} {row['last_name']}"
                        )
                    )
