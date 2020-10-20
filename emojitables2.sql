-- Table creation queries
CREATE TABLE IF NOT EXISTS emojis(
	emoji TEXT NOT NULL,
	emojitype VARCHAR(10) NOT NULL,
	userid VARCHAR(30) NOT NULL,
	guildid VARCHAR(30) NOT NULL,
	cnt INT NOT NULL,
	emojidate timestamp WITH TIME ZONE,
	chid VARCHAR(30),
	PRIMARY KEY(emoji, emojitype, userid, guildid, emojidate)
);

-- Need to create index on timedate so it runs faster
CREATE INDEX emojidate_ndx ON emojis(emojidate);

-- Create channel table
CREATE TABLE IF NOT EXISTS channel(
	chid VARCHAR(30) NOT NULL UNIQUE,
	chname VARCHAR(30) NOT NULL,
	guildid VARCHAR(30) NOT NULL,
	emoji TEXT NOT NULL,
	cnt INT NOT NULL,
	primary key(chid)
);

