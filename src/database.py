# coding: utf8

import sqlite3
import datetime

def bookings_dict(row):
    return {"hotel": row[0], "created_at": row[1], "booking_date": row[2], "price": row[3]}

class Database:

    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('src/db/booking.db')
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()

    def get_bookings(self, user_id):
      cursor = self.get_connection().cursor()
      cursor.execute("""SELECT hotel_id, created_at, booking_for, price
                        FROM bookings
                        WHERE user_id = ?""", (user_id,))
      bookings = cursor.fetchall()
      return [bookings_dict(each) for each in bookings]

    def user_exist(self, user_id):
      cursor = self.get_connection().cursor()
      cursor.execute("""SELECT id
                        FROM users WHERE user_id = ?""", (user_id,))
      return len(cursor.fetchall())

    def create_user(self, user_id):
      connection = self.get_connection()
      connection.execute(("""INSERT INTO users(user_id)"""
                          " values(?)"), (user_id,))
      connection.commit()

    def create_booking(self, user_id, hotel_id, booking_date, price):
      now = datetime.datetime.now()
      co = self.get_connection()
      cursor = co.cursor()
      cursor.execute(("""INSERT INTO bookings(user_id, hotel_id,
                      created_at, booking_for, price)"""
                      " values(?,?,?,?, ?)"), (user_id, hotel_id, now.strftime("%Y-%m-%d %H:%M"),
                                              booking_date, price))
      co.commit()