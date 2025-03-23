from flask import Flask, jsonify, request
from cassandra.cluster import Cluster
import json
from datetime import datetime


def create_app():
    app = Flask(__name__)
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    # Įrašyti kanalo duomenis
    @app.route('/channels', methods=['PUT'])
    def get_data():

        session.execute("CREATE KEYSPACE IF NOT EXISTS mykeyspace WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }")
        session.execute("CREATE TABLE IF NOT EXISTS mykeyspace.channels (id varchar PRIMARY KEY, owner text, topic text)")
        session.execute("CREATE TABLE IF NOT EXISTS mykeyspace.members (channelId varchar, member text, PRIMARY KEY (channelId, member))")

        data = request.get_json()
        id = data['id']
        owner = data['owner']
        topic = data['topic']

        row = session.execute("SELECT * FROM mykeyspace.channels WHERE id = %s", (id,))
        if row:
            return {"message": "Channel already exists"}, 400
        
        if not id or not owner or not topic:
            return {"message": "Missing input"}, 400

        session.execute("INSERT INTO mykeyspace.channels (id, owner, topic) VALUES (%s, %s, %s)  IF NOT EXISTS", (id, owner, topic))
        session.execute("INSERT INTO mykeyspace.members (channelId, member) VALUES (%s, %s) IF NOT EXISTS", (id, owner))

        return {"id": id}, 201

    # Gauti kanalo duomenis
    @app.route('/channels/<channelId>', methods=['GET'])
    def get_channel(channelId):
        rows = session.execute("SELECT * FROM mykeyspace.channels WHERE id = %s", (channelId,))

        if not rows:
            return {"message": "Channel not found"}, 404

        for row in rows:
            return {"id": row.id, "owner": row.owner, "topic": row.topic}, 200

    # Ištrinti kanalą pagal id
    @app.route('/channels/<channelId>', methods=['DELETE'])
    def delete_channel(channelId):
        rows = session.execute("SELECT * FROM mykeyspace.channels WHERE id = %s", (channelId,))
        if not rows:
            return {"message": "Channel not found"}, 404

        session.execute("DELETE FROM mykeyspace.channels WHERE id = %s", (channelId,))
        return {"message": "Channel deleted"}, 204
    
    # Pridėti žinutę į kanalą
    @app.route('/channels/<channelId>/messages', methods=['PUT'])
    def add_message(channelId):
        data = request.get_json()
        author = data['author']
        text = data['text']

        if not author or not text:
            return {"message": "Invalid input, missing text or author"}, 400

        timestamp = datetime.now()

        session.execute("CREATE TABLE IF NOT EXISTS mykeyspace.messages (channelId varchar, author text, text text, timestamp timestamp, PRIMARY KEY (channelId, author, timestamp))")
        session.execute("CREATE TABLE IF NOT EXISTS mykeyspace.messages_by_timestamp (channelId varchar, timestamp timestamp, author text, text text, PRIMARY KEY (channelId, timestamp)) WITH CLUSTERING ORDER BY (timestamp ASC)")
        session.execute("CREATE TABLE IF NOT EXISTS mykeyspace.messages_by_author_timestamp (channelId varchar, author text, timestamp timestamp, text text, PRIMARY KEY (channelId, author, timestamp))")

        session.execute("INSERT INTO mykeyspace.messages (channelId, author, text, timestamp) VALUES (%s, %s, %s, %s) IF NOT EXISTS", (channelId, author, text, timestamp) )
        session.execute("INSERT INTO mykeyspace.messages_by_timestamp (channelId, timestamp, author, text) VALUES (%s, %s, %s, %s)  IF NOT EXISTS", (channelId, timestamp, author, text))
        session.execute("INSERT INTO mykeyspace.messages_by_author_timestamp (channelId, author, timestamp, text) VALUES (%s, %s, %s, %s)  IF NOT EXISTS", (channelId, author, timestamp, text))

        return {"message": "Message added"}, 201

    # Gauti kanalo žinutes pagal kanalo id
    @app.route('/channels/<channelId>/messages', methods=['GET'])
    def get_messages(channelId):
        startAt = request.args.get('startAt')
        author = request.args.get('author')

        if startAt:
            try:
                startAt = datetime.fromisoformat(startAt)
            except ValueError:
                return {"message": "Invalid date format"}, 400

        if startAt and author:
            rows = session.execute("SELECT * FROM mykeyspace.messages_by_author_timestamp WHERE channelId = %s AND timestamp >= %s AND author = %s", (channelId, startAt, author))
        elif startAt:
            rows = session.execute("SELECT * FROM mykeyspace.messages_by_timestamp WHERE channelId = %s AND timestamp >= %s", (channelId, startAt))
        elif author:
            rows = session.execute("SELECT * FROM mykeyspace.messages_by_author_timestamp WHERE channelId = %s AND author = %s", (channelId, author))
        else:
            rows = session.execute("SELECT * FROM mykeyspace.messages_by_timestamp WHERE channelId = %s", (channelId,))

        messages = []
        for row in rows:
            messages.append({"author": row.author, "text": row.text, "timestamp": row.timestamp.isoformat()})

        return messages, 200

    # Prideėti nari į kanalą
    @app.route('/channels/<channelId>/members', methods=['PUT'])
    def add_member(channelId):
        data = request.get_json()
        member = data['member']

        rows = session.execute("SELECT * FROM mykeyspace.members WHERE channelId = %s AND member = %s", (channelId, member))
        if rows:
            return {"message": "Member already exists"}, 400

        if not member:
            return {"message": "Invalid input, missing member"}, 400

        session.execute("INSERT INTO mykeyspace.members (channelId, member) VALUES (%s, %s) IF NOT EXISTS", (channelId, member))
        return {"message": "Member added"}, 201
    
    # Gauti kanalo narius
    @app.route('/channels/<channelId>/members', methods=['GET'])
    def get_members(channelId):
        rows = session.execute("SELECT * FROM mykeyspace.members WHERE channelId = %s", (channelId,))
        members = []

        if not rows:
            return {"message": "Channel not found"}, 404

        for row in rows:
            members.append(row.member)
        return members, 200
    
    # Ištrinti narį iš kanalo
    @app.route('/channels/<channelId>/members/<memberId>', methods=['DELETE'])
    def remove_member(channelId, memberId):
        rows = session.execute("SELECT * FROM mykeyspace.members WHERE channelId = %s AND member = %s", (channelId, memberId))
        if not rows:
            return {"message": "Member not found"}, 404

        session.execute("DELETE FROM mykeyspace.members WHERE channelId = %s AND member = %s", (channelId, memberId))
        return {"message": "Member removed"}, 204
    
    # Ištrinti visą duomenų bazę
    @app.route('/cleanup', methods=['POST'])
    def reset():
        session.execute("DROP KEYSPACE IF EXISTS mykeyspace")
        return {"message": "Cleanup completed."}, 200
    

    return app