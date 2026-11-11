import unittest

from app.db import connect
from app.orders import average_total, export_orders, summary


def seed(conn):
    conn.execute("INSERT INTO customers VALUES (1, 'João da Silva', 'joao@example.com')")
    conn.execute("INSERT INTO orders VALUES (10, 1, 'paid', 120.0)")
    conn.execute("INSERT INTO orders VALUES (11, 1, 'cancelled', 80.0)")


class ExportOrdersTest(unittest.TestCase):
    def test_exports_paid_orders(self):
        conn = connect()
        seed(conn)
        rows = export_orders(conn, "paid")
        self.assertEqual([r["id"] for r in rows], [10])
        self.assertEqual(rows[0]["customer_slug"], "joao-da-silva")
        self.assertEqual(rows[0]["email"], "joao@example.com")
        self.assertEqual(rows[0]["total"], 120.0)

    def test_exports_cancelled_orders(self):
        conn = connect()
        seed(conn)
        rows = export_orders(conn, "cancelled")
        self.assertEqual([r["id"] for r in rows], [11])

    def test_average_total(self):
        self.assertEqual(average_total([{"total": 10}, {"total": 20}]), 15)


class SummaryTest(unittest.TestCase):
    def test_paid_share(self):
        conn = connect()
        seed(conn)
        self.assertEqual(summary(conn), {"paid_share": 0.5})

    def test_paid_share_without_orders_is_zero(self):
        self.assertEqual(summary(connect()), {"paid_share": 0})
