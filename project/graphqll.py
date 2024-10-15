#run=fastapi dev graphqll.py
#paste below code
"""
{
  user {
    name
    age
  }
}
"""

#type
import strawberry
@strawberry.type
class User:
    name: str
    age: int

#query
@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)
    
#graphql 
from strawberry.asgi import GraphQL
schema = strawberry.Schema(query=Query)
graphql_app = GraphQL(schema)

#fastapi
from fastapi import FastAPI
app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)