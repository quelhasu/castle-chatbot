create table bookings (
  id integer primary key,
  user_id integer,
  hotel_id varchar(100),
  created_at text,
  booking_for text
);

create table users (
  id integer primary key,
  username varchar(25)
);