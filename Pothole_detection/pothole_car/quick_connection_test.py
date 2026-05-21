from pymongo import MongoClient

# uri = "mongodb+srv://jayeshvivarekar_db_user:BioJay%4004@cluster0.udi0xwl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

uri = 'mongodb://jayeshvivarekar_db_user:BioJay%4004@ac-zi1njbf-shard-00-00.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-01.udi0xw1.mongodb.net:27017,ac-zi1njbf-shard-00-02.udi0xw1.mongodb.net:27017/?ssl=true&replicaSet=atlas-130x6s-shard-0&authSource=admin&appName=Cluster0'

try:

    print("Connecting...")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000
    )

    print(client.server_info())

    print("Connected!")

except Exception as e:

    print("ERROR:")
    print(e)