#docker
#image pull=docker pull postgres
#container run=docker run --name postgres_container_1 -e POSTGRES_PASSWORD=password -d -p 5432:5432  postgres
#container login=docker exec -it 09897e9d1267 bash
#psql login=psql -U postgres
#host=docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres_container_1

#brew
#brew install postgresql@16
#brew services start postgresql@16
#brew services stop postgresql@16
#brew services info postgresql@16
#brew services restart postgresql@16
#psql postgres

#url
url="postgresql://localhost:5432/postgres"
# url="postgres://postgres:password@172.17.0.3:5432/postgres?sslmode=disable"

#code
import asyncio
import asyncpg
import datetime

async def main():
   conn = await asyncpg.connect(url)
   await conn.execute('''CREATE TABLE if not exists users(id serial PRIMARY KEY,username text,dob date)''')
   await conn.execute('''INSERT INTO users(username, dob) VALUES($1, $2)''', 'atom',datetime.date(1984, 3, 1))
   row = await conn.fetchrow('SELECT * FROM users WHERE username = $1', 'atom')
   print(row)
   await conn.close()

if __name__ == "__main__":
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(main())