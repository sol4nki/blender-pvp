
DROP TABLE IF EXISTS pvp_matches CASCADE;
DROP TABLE IF EXISTS pvp_users CASCADE;
DROP TABLE IF EXISTS pvp_topics CASCADE;

CREATE TABLE pvp_users (
    username TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    wins INT8 DEFAULT 0
);


CREATE TABLE pvp_topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT NOT NULL
);


CREATE TABLE pvp_matches (
    id TEXT PRIMARY KEY,                     
    host_name TEXT NOT NULL,
    guest_name TEXT,                         
    prompt TEXT,                             
    status TEXT DEFAULT 'waiting',           
    is_active BOOLEAN DEFAULT true
);

CREATE OR REPLACE FUNCTION set_random_prompt()
RETURNS TRIGGER AS $$
BEGIN
    SELECT topic_name INTO NEW.prompt FROM pvp_topics ORDER BY random() LIMIT 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER assign_random_prompt_trigger
BEFORE INSERT ON pvp_matches
FOR EACH ROW EXECUTE FUNCTION set_random_prompt();


ALTER TABLE pvp_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE pvp_topics DISABLE ROW LEVEL SECURITY;
ALTER TABLE pvp_matches DISABLE ROW LEVEL SECURITY;