DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS logging;

CREATE TABLE user ( --create user table
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE settings ( --create settings table
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  throttle FLOAT NOT NULL UNIQUE,
  nightvision BOOLEAN NOT NULL,
  buttoncontrol BOOLEAN NOT NULL,
  keycontrol BOOLEAN NOT NULL,
  resolution STR NOT NULL
);

CREATE TABLE logging ( --create logging table
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  datetime TEXT NOT NULL,
  lvl INT NOT NULL,
  msg TEXT NOT NULL
);


INSERT INTO settings VALUES( --insert default values
  1, --id
  0.4, --throttle
  1, --nightvision mode (on)
  1, --button mode (on)
  1, --key mode (on)
  '640x480' --hresolution
)