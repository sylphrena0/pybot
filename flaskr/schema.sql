DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS throttle;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  throttle FLOAT NOT NULL,
  nightvision BOOLEAN NOT NULL,
  buttoncontrol BOOLEAN NOT NULL,
  keycontrol BOOLEAN NOT NULL,
  vresolution INT NOT NULL,
  hresolution INT NOT NULL
);