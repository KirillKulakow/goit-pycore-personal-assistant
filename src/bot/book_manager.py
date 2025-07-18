# src/bot/book_manager.py

import importlib
import inspect
import pickle
from pathlib import Path
from typing import Dict
from src.core.book import Book, get_search_prefix, get_update_prefix


class BookManager:
    books: Dict[str, Book] = {}

    def __init__ (self):
        self.books = {}
        self._load_books()

    def _load_books (self):
        books_root = Path(__file__).parent.parent / 'core' / 'books'

        for path in books_root.rglob("*_book.py"):
            rel_path = path.relative_to(Path(__file__).parent.parent.parent)
            module_path = '.'.join(rel_path.with_suffix('').parts)  # e.g. src.core.books.contact.contact_book

            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module, inspect.isclass): # looping through
                if issubclass(obj, Book) and obj is not Book: # looping through specific Book classes

                    bookInstance = obj()
                    book_name = bookInstance.get_book_name()

                    # to delete start
                    self.books[book_name] = bookInstance  # e.g. "contact": ContactBook()
                    continue
                    # to delete end
                    # book_pkl_data_file_path = books_root / book_name / f'{book_name}_book_data.pkl'
                    # try:
                    #     with open(book_pkl_data_file_path, "rb") as f:
                    #         self.books[book_name] = pickle.load(f)
                    # except FileNotFoundError:
                    #     self.books[book_name] = bookInstance  # e.g. "contact": ContactBook()

    def save_books_state (self):
        pass
        # books_root = Path(__file__).parent.parent / 'core' / 'books'
        #
        # for book in self.books:
        #     book_obj = self.books[book]
        #     book_name = book_obj.get_book_name()
        #     book_pkl_data_file_path = books_root / book_name / f'{book_name}_book_data.pkl'
        #
        #     with open(book_pkl_data_file_path, "wb") as f:
        #         pickle.dump(book_obj, f)

    def get_book (self, book_name: str):
        if book_name not in self.books:
            raise ValueError(f'No such book: {book_name}')
        return self.books[book_name]

    def get_supported_operations (self) -> dict[str, list]:
        commands = {}

        for book_name, book in self.books.items():
            # book records operations
            methods_to_process = self._get_class_methods_for_operations_preparing(book)

            for method_to_process in methods_to_process:
                method_acceptable_params = self._get_book_operation_params(book_name, method_to_process)
                cmd = method_to_process.replace('record', book_name).replace('_', '-')
                commands[cmd] = method_acceptable_params

            # child fields operations
            for record_class_multi_field in book.get_record_multi_value_fields():
                standard_ops = ['add', 'update', 'delete', 'get']

                for operation_name in standard_ops:
                    params = {}
                    command_name = f"{operation_name}-{book_name}-{record_class_multi_field.replace('_', '-')}"

                    if operation_name == 'add':
                        params.update({record_class_multi_field:record_class_multi_field})
                    else:
                        # for operations which require search operations - show fields to search by
                        if operation_name in ['update', 'get', 'delete']:
                            params.update({get_search_prefix(Book) + '_' + record_class_multi_field: record_class_multi_field})

                            # for update operations - show fields user can modify
                            if operation_name in ['update']:
                                params.update({get_update_prefix(Book) + '_' + record_class_multi_field: record_class_multi_field})

                    commands[command_name] = params

        return commands

    def _get_class_methods_for_operations_preparing (self, book):
        methods_to_process = []

        for method_name in dir(book):
            # checking only public methods
            if method_name.startswith('_') is False:
                method = getattr(book, method_name)
                # preparing for processing only not hidden from bot user functions
                if callable(getattr(book, method_name)) and getattr(method, '_hidden', False) is not True:
                    methods_to_process.append(method_name)

        return methods_to_process

    def run_command (self, command_name: str, *args, **kwargs):
        # dispatches and runs a command like 'add-contact' or 'add-note-tag'
        additional_params = command_name.split("-")[2:]  # ['phone', 'number']
        func_name = command_name.replace('-', '_')

        for book_name, book in self.books.items():
            if ('_' + book_name) in func_name:  # if '-contact' in 'add-contact' or 'get-contacts'
                if not additional_params:
                    func_name = func_name.replace(book_name, 'record')
                    print('running main command:', func_name)
                    func = getattr(book, func_name)  # gets the method
                    return func(*args, **kwargs)
                else:
                    print('running nested field command')
                    # Handle nested field commands (add-contact-phone, etc.)
                    # Implementation needed for multi-value field operations
                    return f"Multi-value field commands not yet implemented for: {command_name}"
            elif hasattr(book, func_name) and callable(getattr(book, func_name)):
                print('elif working')
                func = getattr(book, func_name)  # gets the method
                return func(*args, **kwargs)
        
        return f"Unknown command: {command_name}"

    def _get_book_operation_params (self, book_name: str = '', method_name: str = '') -> dict:
        params = {}

        method_name_parts = method_name.split("_")
        operation_name = method_name_parts[0]

        module_path = f'src.core.books.{book_name}.{book_name}'

        # for add operations - show all record fields
        record_fields = self.books[book_name].get_record_class_fields()
        if operation_name == 'add':
            params.update({record_field:record_field for record_field in record_fields})
        else:
            # for operations which require search operations - show fields to search by
            if operation_name in ['update', 'get', 'delete']:
                for field_name in record_fields:
                    params.update({get_search_prefix(Book) + '_' + field_name: field_name})

                    # for update operations - show fields user can modify
                    if operation_name in ['update']:
                        params.update({get_update_prefix(Book) + '_' + field_name: field_name})

        # if not generic record operations - show function arguments as commands params
        if len(params) == 0:
            module_path += '_book'
            module = importlib.import_module(module_path)
            class_name = book_name.capitalize() + 'Book'
            book_class = getattr(module, class_name)

            # get the method by name (could be 'add_record', 'get_records', etc.)
            if hasattr(book_class, method_name):
                method = getattr(book_class, method_name)
                # inspect the method signature
                sig = inspect.signature(method)
                # return list of parameter names (skip 'self' or 'cls')
                params = {
                    f'{name}={name}'
                    for name in sig.parameters
                    if name not in ['self', 'cls']
                }

        return params

