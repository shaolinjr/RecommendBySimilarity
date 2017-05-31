import rethinkdb as r
import json

r.connect('localhost',28015).repl()

with open("dados_.json") as json_data:
    data = json.load(json_data)
    r.db('usuarios').table('raw_data').insert(data).run()
    json_data.close()
