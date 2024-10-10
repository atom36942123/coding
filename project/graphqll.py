#run=fastapi dev graphqll.py
#open=http://localhost:8000/graphql
#paste below code
"""
{
  user {
    name
    age
  }
}
"""

#schema
import strawberry

@strawberry.type
class User:
    name: str
    age: int

@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)
    
  
#graphql app    
from strawberry.asgi import GraphQL
schema = strawberry.Schema(query=Query)
graphql_app = GraphQL(schema)


#fastapi
from fastapi import FastAPI
app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)