import json
import pymongo

uri = 'mongodb+srv://rohithmech2006_db_user:Rohith123456@cluster0.3mif2an.mongodb.net/bizflow?retryWrites=true&w=majority&appName=Cluster0'
client = pymongo.MongoClient(uri)
db = client['bizflow']

with open('db.json', 'r') as f:
    data = json.load(f)

for cat, docs in data.items():
    if not docs: continue
    collection = db[cat]
    for doc in docs:
        if '_id' in doc:
            del doc['_id']
        collection.update_one({'id': doc['id']}, {'$set': doc}, upsert=True)

print('Migration successful!')
