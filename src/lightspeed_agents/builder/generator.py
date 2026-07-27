class CompanyGenerator:

    def generate(self, company):

        agents = company['agents']['agents']['agents']

        generated_agents = []

        for agent in agents:

            generated_agents.append({
                'id': agent['id'],
                'name': agent['name'],
                'role': agent['role'],
                'department': agent['department'],
                'reportsTo': agent['reportsTo'],
                'tools': agent.get('tools', []),
                'permissions': agent.get('permissions', []),
            })

        return {
            'agents': generated_agents,
            'departments': company['departments'],
            'models': company['models'],
            'workflows': company['workflows'],
            'kpis': company['kpis'],
        }
