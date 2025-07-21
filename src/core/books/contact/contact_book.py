# src/core/books/contact/contact_book.py

from datetime import datetime, timedelta
from typing import List

from src.core.book import Book
from src.core.decorators import hidden_method, method_args_as_command_params, method_for_bot_interface


class ContactBook(Book):
    # used only for code
    @hidden_method
    def get_book_name (self) -> str:
        return 'contact'

    @classmethod
    def get_record_class (cls):
        from src.core.books.contact.contact_record import ContactRecord
        return ContactRecord

    @method_for_bot_interface
    @method_args_as_command_params
    def get_coming_birthdays_from_now (self, days_ahead: int = 0) -> List[str]:
        days_ahead = int(days_ahead)
        today = datetime.today().date()
        upcoming_dates = {
            (today + timedelta(days=i)).strftime('%m-%d')
            for i in range(days_ahead + 1)
        }

        matching_records = []

        for record in self.data.values():
            birthday = record.fields["birthday"]
            if not birthday:
                continue

            # parse string to date if needed
            if isinstance(birthday, str):
                try:
                    birthday_date = datetime.strptime(birthday, '%Y-%m-%d').date()
                except ValueError:
                    continue
            else:
                birthday_date = birthday

            # compare month-day only
            if birthday_date.strftime('%m-%d') in upcoming_dates:
                matching_records.append(record)

        return matching_records
