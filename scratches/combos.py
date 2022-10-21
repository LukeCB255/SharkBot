import datetime
import random
import itertools

players = [f"Player {num}" for num in range(1, 6)]
agents = [f"Agent {num}" for num in range(1, 21)]
agentValues = {}

for player in players:
    agentValues[player] = {}
    for agent in agents:
        agentValues[player][agent] = random.randint(1, 5)

optimalValues = {}
for agent in agents:
    optimalValues[agent] = [random.randint(1, 5) for num in range(1, 6)]

print(agentValues)
print(optimalValues)

teams = [team for team in itertools.permutations(players, 5)]
print(len(teams))
print(teams)

agentTeams = [team for team in itertools.permutations(agents, 5)]
print(len(agentTeams))

combos = itertools.product(teams, agentTeams)
comboResults = {}
i = 0

highestValue = 0
c = None

start = datetime.datetime.now()

for combo in combos:
    value = 0
    for j in range(0, 5):
        player = combo[0][j]
        agent = combo[1][j]
        value += agentValues[player][agent] * optimalValues[agent][j]

    if value > highestValue:
        highestValue = value
        c = combo

    if i % 1000000 == 0:
        print(f"{i} done")
    i += 1

end = datetime.datetime.now()
print(f"{highestValue} {c}")
print(f"{(end - start).total_seconds()} time")

print("Done")