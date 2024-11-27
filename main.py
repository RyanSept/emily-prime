from letta import create_client

from constants import TEST_RYAN_2014, COMPASSIONATE_HIPPOPOTAMUS

# connect to the server
client = create_client(base_url="http://localhost:8283")

test_agent = client.get_agent(agent_id=TEST_RYAN_2014)
main_agent = client.get_agent(agent_id=COMPASSIONATE_HIPPOPOTAMUS)

# send a message to the agent
# response = client.send_message(
#     agent_id=TEST_RYAN_2014,
#     role="user",
#     message="hey!! how are you?"
# )

print(response)
