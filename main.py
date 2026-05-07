import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.database import setup_database
from src.etl_pipeline import run_pipeline
from src.reporter import print_report, save_report_to_file
from src.monitor import check_pipeline_health
from src.validators import check_database_quality


def print_menu():
    print("\n" + "=" * 50)
    print("     WEATHER DATA PIPELINE — MAIN MENU")
    print("=" * 50)
    print("  1. Run ETL pipeline once")
    print("  2. View full report")
    print("  3. Save report to file")
    print("  4. Database quality check")
    print("  5. System health monitor")
    print("  6. Start scheduler (runs every 60 min)")
    print("  0. Exit")
    print("=" * 50)


def main():
    # Always ensure DB is set up
    setup_database()

    while True:
        print_menu()
        choice = input("\n  Enter your choice: ").strip()

        if choice == "1":
            run_pipeline()

        elif choice == "2":
            print_report()

        elif choice == "3":
            print_report()
            save_report_to_file()

        elif choice == "4":
            check_database_quality()

        elif choice == "5":
            check_pipeline_health()

        elif choice == "6":
            print("\n⚠️  Scheduler will run the pipeline every 60 minutes.")
            print("   Press Ctrl+C to stop.\n")
            from src.scheduler import start_scheduler
            start_scheduler()

        elif choice == "0":
            print("\n  👋 Goodbye!\n")
            break

        else:
            print("\n  ❌ Invalid choice. Please enter 0–6.")


if __name__ == "__main__":
    main()