#https://github.com/dgraph-io/pydgraph?tab=readme-ov-file#install
#above is important reference for these basics, as well look into upsert requests and metadata section. might be very useful
#pip install pydgraph
import pydgraph
#How to create a client connecion
client_stub = pydgraph.DgraphClientStub('localhost:9080')
client = pydgraph.DgraphClient(client_stub)
#to create a schema example, use the schema I created (create source node and root edge as well as logic for new edges to make it a graph)
schema = 'name: string @index(exact) .'
op = pydgraph.Operation(schema=schema)
client.alter(op)
# Drop all data including schema from the Dgraph instance. This is a useful
# for small examples such as this since it puts Dgraph into a clean state. Similar to Bulk Edit
#DropAttr is used to drop all the data related to a predicate.
op = pydgraph.Operation(drop_all=True)
client.alter(op) 

#Example of creating data.
p = { 'name': 'Alice' }

# Run mutation.
txn.mutate(set_obj=p)

#If you want to use a mutation object, use this instead:
mu = pydgraph.Mutation(set_json=json.dumps(p).encode('utf8'))
txn.mutate(mu)

#Example of deleting data

query = """query all($a: string)
 {
   all(func: eq(name, $a))
    {
      uid
    }
  }"""
variables = {'$a': 'Bob'}

res = txn.query(query, variables=variables)
ppl = json.loads(res.json)
# For a mutation to delete a node, use this:
txn.mutate(del_obj=person)

#You can run a query by calling Txn#query(string). You will need to pass in a DQL query string. If you want to pass an additional dictionary of any variables that you might want to set in the query, call Txn#query(string, variables=d) with the variables dictionary d.
#Example of running a query.
query = """query all($a: string) {
  all(func: eq(name, $a))
  {
    name
  }
}"""
variables = {'$a': 'Alice'}

res = txn.query(query, variables=variables)

# If not doing a mutation in the same transaction, simply use:
# res = client.txn(read_only=True).query(query, variables=variables)

ppl = json.loads(res.json)

# Print results.
print('Number of people named "Alice": {}'.format(len(ppl['all'])))
for person in ppl['all']:
  print(person)
"""
Output
Number of people named "Alice": 1
Alice
"""
#You can also use txn.do_request function to run the query.
request = txn.create_request(query=query)
txn.do_request(request)

