# src/core/books/note/note_book.py

from src.core.book import Book
from src.core.decorators import hidden_method


class NoteBook(Book):
    @hidden_method
    def get_book_name (self) -> str:
        return 'note'

    @classmethod
    def get_record_class (cls):
        from src.core.books.note.note_record import NoteRecord
        return NoteRecord
