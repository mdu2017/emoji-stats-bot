-- Table creation queries
CREATE TABLE IF NOT EXISTS guild(
	guildid VARCHAR(30),
	guildname VARCHAR(80),
	CONSTRAINT pk_guild PRIMARY KEY(guildid)
);

CREATE TABLE IF NOT EXISTS users(
	userid VARCHAR(30) NOT NULL,
	guildid VARCHAR(30) NOT NULL,
	enabled BOOLEAN NOT NULL DEFAULT TRUE,

	CONSTRAINT pk_users PRIMARY KEY(userid, guildid),
	CONSTRAINT fk_users FOREIGN KEY(guildid) REFERENCES guild(guildid)
);

CREATE TABLE IF NOT EXISTS channel(
	chid VARCHAR(30) NOT NULL UNIQUE,
	chname VARCHAR(30) NOT NULL,
	guildid VARCHAR(30) NOT NULL,
 	CONSTRAINT pk_channel PRIMARY KEY(chid, guildid),
	CONSTRAINT fk_channel FOREIGN KEY(guildid) REFERENCES guild(guildid)
);

CREATE TABLE IF NOT EXISTS emojis(
	emoji TEXT NOT NULL,
	emojitype VARCHAR(10) NOT NULL,
	userid VARCHAR(30) NOT NULL,
	guildid VARCHAR(30) NOT NULL,
	cnt INT NOT NULL,
	emojidate timestamp WITH TIME ZONE,
	chid VARCHAR(30),
	PRIMARY KEY(emoji, emojitype, userid, guildid),
	CONSTRAINT fk_user_guild FOREIGN KEY(userid, guildid) REFERENCES users(userid, guildid),
	CONSTRAINT fk_channel FOREIGN KEY(chid) REFERENCES channel(chid)
);


-- Insert queries

-- Run once every few days for guild (
INSERT INTO guild(guildid, guildname)
VALUES ('guildid', 'guildname')
ON CONFLICT DO UPDATE SET guildname = 'someguildname';

-- On member join, run this query
INSERT INTO users(userid, guildid)
VALUES ('abc', 'guild')
ON CONFLICT DO NOTHING;

-- On guild channel create
-- on_guild_channel_create(channel)
INSERT INTO channel(chid, chname)
VALUES ('channelid', 'channelname')
ON CONFLICT DO NOTHING;

-- on guild channel update
--on_guild_channel_update(before, after)
UPDATE channel SET channelname = after.name;


-- When adding emojis on message or on react
INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, channel)
VALUES('thumbsup', 'message', 'abc', '77', 1, '2020-09-16 21:00:00')
ON CONFLICT(emoji, emojitype, userid, guildid)
DO UPDATE SET cnt = emojis.cnt + 1, emojidate = '2020-09-16 21:00:00';

-- Grab top 5 reacts/messages
SELECT emoji, SUM(cnt) FROM emojis
WHERE emojis.emojitype = 'react' AND emojis.guildid = '77'
GROUP BY emoji
ORDER BY SUM(cnt) DESC
LIMIT 5;