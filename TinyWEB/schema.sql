--SELECT * FROM sqlite_master;

CREATE TABLE IF NOT EXISTS part (
	id INTEGER NOT NULL, 
	partnumber VARCHAR NOT NULL, 
	revision VARCHAR, 
	approved VARCHAR, 
	author VARCHAR, 
	category VARCHAR, 
	configuration VARCHAR, 
	datasheet VARCHAR, 
	description VARCHAR, 
	drawndate VARCHAR, 
	file VARCHAR, 
	finish VARCHAR, 
	folder VARCHAR, 
	link VARCHAR, 
	mass FLOAT, 
	material VARCHAR, 
	oem VARCHAR, 
	process VARCHAR, 
	process2 VARCHAR, 
	process3 VARCHAR, 
	spare_part BOOLEAN, 
	supplier VARCHAR, 
	supplier_partnumber VARCHAR, 
	thickness FLOAT, 
	treatment VARCHAR, 
	colour TEXT, 
	notes TEXT, 
	PRIMARY KEY (id)
);





CREATE TABLE IF NOT EXISTS bom (
	id INTEGER NOT NULL,
	father_id INTEGER NOT NULL,
	child_id INTEGER NOT NULL,
	qty INTEGER NOT NULL,
	CONSTRAINT BOM_PK PRIMARY KEY (id),
	CONSTRAINT FK_bom_part FOREIGN KEY (father_id) REFERENCES part(id)
);

CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS comment (
	id INTEGER PRIMARY KEY  AUTOINCREMENT,
	part_id INTEGER NOT NULL ,
	user_id INTEGER NOT NULL ,
	body TEXT,
	category TEXT,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	pic_path TEXT,
	CONSTRAINT FK_comments_part FOREIGN KEY (part_id) REFERENCES part(id),
	CONSTRAINT FK_comments_user_2 FOREIGN KEY (user_id) REFERENCES "user"(id)
)