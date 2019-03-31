# coding: utf8

import sqlite3
import datetime

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
      cursor.execute("""SELECT *
                        FROM bookings
                        WHERE user_id = ?""", (user_id,))

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

    def create_booking(self, user_id, hotel_id, booking_date):
      now = datetime.datetime.now()
      co = self.get_connection()
      cursor = co.cursor()
      cursor.execute(("""INSERT INTO bookings(user_id, hotel_id,
                      created_at, booking_for)"""
                      " values(?,?,?,?)"), (user_id, hotel_id, now.strftime("%Y-%m-%d %H:%M"),
                                              booking_date))
      co.commit()