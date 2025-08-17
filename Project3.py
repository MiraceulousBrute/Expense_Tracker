#!/usr/bin/env python3
"""
Human-friendly Personal Expense Tracker
- Resilient loading/saving (handles empty/corrupt JSON)
- Flexible amount parsing (accepts "₹", commas)
- Multiple date formats accepted
- List / Edit / Delete support
"""

import json
import os
import re
from datetime import datetime
from collections import defaultdict

FILE_NAME = "expenses.json"


def load_expenses():
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            print("⚠ The file exists but doesn't contain a list. Starting fresh.")
            return []
    except json.JSONDecodeError:
        print(f"⚠ {FILE_NAME} looks empty or corrupted. I'll start a new file and back up the old one.")
        try:
            backup = FILE_NAME + ".backup." + datetime.now().strftime("%Y%m%d%H%M%S")
            os.rename(FILE_NAME, backup)
            print(f"🔁 Backed up the corrupted file to: {backup}")
        except Exception:
            pass
        return []
    except Exception as e:
        print("❌ Unable to read expenses file:", e)
        return []


def save_expenses(expenses):
    try:
        with open(FILE_NAME, "w") as f:
            json.dump(expenses, f, indent=4)
    except Exception as e:
        print("❌ Failed to save data:", e)


def sanitize_amount(s):
    """Remove currency symbols and commas; convert to float."""
    s = s.strip()
    # keep digits, dot and minus
    cleaned = re.sub(r"[^\d.\-]", "", s)
    if cleaned == "":
        raise ValueError("No numeric characters found")
    return float(cleaned)


def parse_date(s):
    """Accept multiple date formats; return YYYY-MM-DD."""
    s = s.strip()
    if s == "":
        return datetime.now().strftime("%Y-%m-%d")
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y")
    for fmt in formats:
        try:
            d = datetime.strptime(s, fmt)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("Date not recognized. Use YYYY-MM-DD or DD-MM-YYYY")


def add_expense(expenses):
    print("\n💸 Add a new expense (type 'q' at any prompt to cancel)")
    try:
        while True:
            amt_input = input("Amount (e.g., 250 or ₹250): ").strip()
            if amt_input.lower() == "q":
                print("Cancelled.")
                return
            try:
                amount = sanitize_amount(amt_input)
                break
            except ValueError:
                print("❌ I couldn't parse that amount. Try again (you can include ₹ or commas).")

        category = input("Category (e.g., Food, Transport) [default: Misc]: ").strip().title()
        if category.lower() == "q":
            print("Cancelled.")
            return
        if not category:
            category = "Misc"

        while True:
            date_input = input("Date (YYYY-MM-DD) or press Enter for today: ")
            if date_input.strip().lower() == "q":
                print("Cancelled.")
                return
            try:
                date = parse_date(date_input)
                break
            except ValueError:
                print("❌ Bad date. Try YYYY-MM-DD or DD-MM-YYYY (or press Enter).")

        expense = {"amount": amount, "category": category, "date": date}
        expenses.append(expense)
        save_expenses(expenses)
        print(f"✅ Saved: ₹{amount:.2f} — {category} on {date}")
    except KeyboardInterrupt:
        print("\n✋ Interrupted. Returning to menu.")


def list_expenses(expenses):
    if not expenses:
        print("\n📂 No expenses recorded yet.")
        return
    print("\n📋 Your expenses (most recent first):")
    # sort by date descending (string YYYY-MM-DD works)
    for idx, e in enumerate(sorted(expenses, key=lambda x: x["date"], reverse=True), start=1):
        print(f"{idx}. [{e['date']}] {e['category']} — ₹{float(e['amount']):.2f}")


def view_summary(expenses):
    if not expenses:
        print("\n📂 No expenses recorded yet. Add one to see summaries.")
        return
    total = sum(float(e["amount"]) for e in expenses)
    print(f"\n📊 Total spent: ₹{total:.2f}")

    by_cat = defaultdict(float)
    by_month = defaultdict(float)
    for e in expenses:
        by_cat[e["category"]] += float(e["amount"])
        month = e["date"][:7]  # YYYY-MM
        by_month[month] += float(e["amount"])

    print("\n🔖 By category:")
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f" - {cat}: ₹{amt:.2f}")

    print("\n🗓 By month:")
    for m, amt in sorted(by_month.items()):
        print(f" - {m}: ₹{amt:.2f}")


def delete_expense(expenses):
    if not expenses:
        print("\nNothing to delete.")
        return
    list_expenses(expenses)
    try:
        choice = input("Enter the item number to delete (or 'q' to cancel): ").strip()
        if choice.lower() == "q":
            print("Cancelled.")
            return
        idx = int(choice) - 1
        # mapping because we displayed sorted list; find that item
        sorted_list = sorted(expenses, key=lambda x: x["date"], reverse=True)
        item = sorted_list[idx]
        confirm = input(f"Delete {item['category']} ₹{item['amount']} on {item['date']}? (y/N): ").strip().lower()
        if confirm == "y":
            # actually remove the first matching item in original list
            for i, e in enumerate(expenses):
                if e == item:
                    del expenses[i]
                    save_expenses(expenses)
                    print("✅ Deleted.")
                    return
            print("Could not find the item to delete.")
        else:
            print("Cancelled.")
    except (IndexError, ValueError):
        print("❌ Invalid selection.")


def edit_expense(expenses):
    if not expenses:
        print("\nNothing to edit.")
        return
    list_expenses(expenses)
    try:
        choice = input("Enter the item number to edit (or 'q' to cancel): ").strip()
        if choice.lower() == "q":
            print("Cancelled.")
            return
        idx = int(choice) - 1
        sorted_list = sorted(expenses, key=lambda x: x["date"], reverse=True)
        item = sorted_list[idx]
        # find actual index in original list
        orig_index = next(i for i, e in enumerate(expenses) if e == item)

        print("Press Enter to keep current value.")
        new_amt = input(f"Amount (current ₹{item['amount']}): ").strip()
        if new_amt:
            try:
                expenses[orig_index]["amount"] = sanitize_amount(new_amt)
            except ValueError:
                print("Bad amount — keeping old value.")

        new_cat = input(f"Category (current {item['category']}): ").strip()
        if new_cat:
            expenses[orig_index]["category"] = new_cat.title()

        new_date = input(f"Date (current {item['date']}, formats allowed YYYY-MM-DD or DD-MM-YYYY): ").strip()
        if new_date:
            try:
                expenses[orig_index]["date"] = parse_date(new_date)
            except ValueError:
                print("Bad date — keeping old value.")

        save_expenses(expenses)
        print("✅ Updated.")
    except (IndexError, ValueError, StopIteration):
        print("❌ Invalid selection.")


def main():
    expenses = load_expenses()
    print("👋 Hey! Welcome to your friendly Expense Tracker.\n")
    try:
        while True:
            print("\n--- Main Menu ---")
            print("1) Add expense")
            print("2) View summary")
            print("3) List all expenses")
            print("4) Edit an expense")
            print("5) Delete an expense")
            print("6) Exit")
            choice = input("Choose 1-6: ").strip()
            if choice == "1":
                add_expense(expenses)
            elif choice == "2":
                view_summary(expenses)
            elif choice == "3":
                list_expenses(expenses)
            elif choice == "4":
                edit_expense(expenses)
            elif choice == "5":
                delete_expense(expenses)
            elif choice == "6":
                print("✅ All data saved. Bye! 👋")
                break
            else:
                print("⚠ Pick a number between 1 and 6.")
    except KeyboardInterrupt:
        print("\n✋ Interrupted. Saving and exiting...")
        save_expenses(expenses)


if __name__ == "__main__":
    main()