import unittest

from app.customers import customer_handle
from app.db import connect, find_customer
from app.text import slugify


class SlugifyTest(unittest.TestCase):
    def test_removes_accents_and_punctuation(self):
        self.assertEqual(slugify("João da Silva, Jr."), "joao-da-silva-jr")

    def test_customer_handle(self):
        self.assertEqual(customer_handle("Ana Lima"), "@ana-lima")


class FindCustomerTest(unittest.TestCase):
    def test_finds_by_email(self):
        conn = connect()
        conn.execute("INSERT INTO customers VALUES (1, 'Ana', 'ana@example.com')")
        self.assertEqual(find_customer(conn, "ana@example.com")["name"], "Ana")
