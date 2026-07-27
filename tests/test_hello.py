from lightspeed_agents.hello import greet


def test_greet():
    assert greet() == "Hello, LightSpeed Agents!"
