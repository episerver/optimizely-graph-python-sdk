from flask import Flask, render_template, request
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

app = Flask(__name__)

OG_ENDPOINT = "http://localhost:4000/content/v2?auth=PUTliAQZzXXGQWccncDMFmtZ3rFbBZfQVFBrriYNjDI0ebKm"

transport = AIOHTTPTransport(
    url=OG_ENDPOINT)
client = Client(transport=transport, fetch_schema_from_transport=True)

query_actors_default = gql(
    """
query MyQuery {
  Actor {
    total
    items {
      primaryName
      primaryProfession
      birthYear
      deathYear
      _link (type:DEFAULT) {
        Title (orderBy: {primaryTitle: ASC}) {
          items {
            primaryTitle
            genres
            _link(type:TITLES) {
              Rating {
                items {
                  averageRating
                  numVotes
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
)

query_ratings_default = gql(
    """
query MyQuery {
  Rating(
    limit: 100
    where: { averageRating: { lte: 10 } }
    orderBy: { averageRating: DESC, numVotes: DESC }
  ) {
    total (all: true)
    items {
      tconst
      numVotes
      averageRating
      linkWithDefaultType: _link(type: TITLES) {
        Title {
          items {
            primaryTitle
            originalTitle
            genres
            tconst
            _fulltext
          }
        }
      }
      linkWithTitleToActor: _link(type: TITLE_TO_ACTOR) {
        Actor {
          items {
            primaryName
            _link (type: DEFAULT) {
              Title {
                items {
                  primaryTitle
                  genres
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
)


def query_with_gql(query):
    return gql(
        """
query MyQuery {
  Record(
    where: { _fulltext: { match: \"""" + query + """\" }}
    orderBy: { _ranking: SEMANTIC }
  ) {
    total
    items {
      __typename
      ... on Title {
        primaryTitle
        genres
        actors: _link(type: TITLE_TO_ACTOR) {
          Actor {
            items {
              primaryName
              primaryProfession
              birthYear
              deathYear
              _fulltext
            }
          }
        }
        ratings: _link(type: TITLES) {
          Rating {
            items {
              averageRating
              numVotes
            }
          }
        }
      }
      ... on Actor {
        primaryName
        primaryProfession
        birthYear
        deathYear
        _link(type: DEFAULT) {
          Title {
            items {
              primaryTitle
              genres
              _link(type: TITLES) {
                Rating {
                  items {
                    averageRating
                    numVotes
                    tconst
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
    """
    )


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/actors')
def actors():
    result = client.execute(query_actors_default)
    actors = result["Actor"]["items"]
    hits = result["Actor"]["total"]
    return render_template('actors.html', len=len(actors), actors=actors, hits=hits)


@app.route('/ratings')
def ratings():
    result = client.execute(query_ratings_default)
    items = result["Rating"]["items"]
    hits = result["Rating"]["total"]
    return render_template('ratings.html', len=len(items), items=items, hits=hits)


@app.route('/search')
def search():
    query = request.args.get('query')
    result = client.execute(query_with_gql(query) if query is not None else query_actors_default)
    items = result["Record"]["items"]
    hits = result["Record"]["total"]
    return render_template('results.html', len=len(items), query=query, items=items, hits=hits)


if __name__ == '__main__':
    app.run(debug=True, port=7001)
