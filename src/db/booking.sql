create table bookings (
  id integer primary key,
  user_id varchar(80),
  hotel_id varchar(100),
  created_at text,
  booking_for text,
  price text
);

create table users (
  id integer primary key,
  user_id varchar(80) unique
);