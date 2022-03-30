DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS settings;

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
  hresolution INT NOT NULL,
  vresolution INT NOT NULL
);

INSERT INTO settings VALUES( --insert default values
  1, --id
  0.4, --throttle
  1, --nightvision mode (on)
  1, --button mode (on)
  1, --key mode (on)
  640, --hresolution
  480 --vresolution
)