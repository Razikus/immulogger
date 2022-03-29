from immudb import ImmudbClient

w = ImmudbClient("localhost:3322")
w.login("immudb", "immudb")
w.sqlExec("""CREATE TABLE IF NOT EXISTS Logs(
    id INTEGER AUTO_INCREMENT, 
    log VARCHAR[4096] NOT NULL, 
    uniqueidentifier VARCHAR[64] NOT NULL, 
    createdate INTEGER NOT NULL, 
    PRIMARY KEY (id)
)""")
w.sqlExec("""
CREATE TABLE IF NOT EXISTS Tags(
    id INTEGER AUTO_INCREMENT, 
    logid INTEGER NOT NULL, 
    tag VARCHAR[64] NOT NULL,
    PRIMARY KEY (id)
)""")